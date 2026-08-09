from __future__ import annotations

import hashlib
import heapq
import math
import re
import tarfile
from collections import Counter
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import requests

YEARS=(2018,2019)
BLIND_LOW=20.0
BLIND_HIGH=55.0
MAX_EVENTS_PER_BIN=10_000
CONTENT_URL="https://zenodo.org/api/records/15553437/files/silseth_thesis_data.tar.gz/content"
ZENODO_RECORD_URL="https://zenodo.org/api/records/15553437"
EXPECTED_FILE_KEY="silseth_thesis_data.tar.gz"
EXPECTED_FILE_SIZE=21_485_785_089
EXPECTED_FILE_MD5="01820c6a90ea1415b011bb013a4d9213"
MONTH_RE=re.compile(r"^data/(2018|2019)/(0[1-9]|1[0-2])/kep_collect\.h5$")
STOP_PREFIX="data/2020/"
REQUIRED_GEOMETRY=("sun_lon","slat","slon","vels")
AU_M=149_597_870_700.0


def require(ok:bool,message:str)->None:
    if not ok: raise RuntimeError(message)


def event_id(year:int,member:str,row:int)->str:
    return f"MAARSY|{year}|{member}|{row}"


def parse_event_id(eid:str)->tuple[int,str,int]:
    parts=eid.split("|",3)
    require(len(parts)==4 and parts[0]=="MAARSY",f"invalid MAARSY ID {eid}")
    year=int(parts[1]); member=parts[2]; row=int(parts[3])
    require(year in YEARS and member.startswith(f"data/{year}/") and member.endswith("/kep_collect.h5") and row>=0,f"invalid MAARSY ID {eid}")
    return year,member,row


def identity_hash(eid:str)->int:
    return int.from_bytes(hashlib.sha256(eid.encode()).digest(),"big")


def push_smallest(heap:list[tuple[int,str,dict[str,Any]]],event:dict[str,Any])->None:
    eid=str(event["id"]); hv=identity_hash(eid); item=(-hv,eid,event)
    if len(heap)<MAX_EVENTS_PER_BIN: heapq.heappush(heap,item); return
    if hv < -heap[0][0] or (hv == -heap[0][0] and eid < heap[0][1]): heapq.heapreplace(heap,item)


def verify_zenodo_metadata()->dict[str,Any]:
    response=requests.get(ZENODO_RECORD_URL,timeout=120,headers={"Accept":"application/json","User-Agent":"OrbitTrace-v6-LF-MAARSY-2018-2019/1.0"}); response.raise_for_status()
    obj=response.json(); files=obj.get("files",[]); require(len(files)==1,"Zenodo file count changed")
    f=files[0]; require(f.get("key")==EXPECTED_FILE_KEY,"Zenodo key changed"); require(int(f.get("size"))==EXPECTED_FILE_SIZE,"Zenodo size changed")
    require(str(f.get("checksum"))==f"md5:{EXPECTED_FILE_MD5}","Zenodo checksum changed")
    links=f.get("links") or {}; content=str(links.get("content") or links.get("self") or "")
    require(content==CONTENT_URL,"Zenodo content URL changed")
    return {"record_id":int(obj.get("id")),"file_key":str(f["key"]),"file_size":int(f["size"]),"checksum":str(f["checksum"]),"content_url":content}


def _read_retained(ds:h5py.Dataset,indices:np.ndarray)->np.ndarray:
    if not len(indices): return np.asarray([],dtype=np.float64)
    require(indices.ndim==1 and np.all(indices[1:]>indices[:-1]),"retained indices not increasing")
    return np.asarray(ds[indices],dtype=np.float64)


def parse_geometry_member(path:Path,year:int,member:str,heaps:dict[int,list[tuple[int,str,dict[str,Any]]]])->dict[str,Any]:
    with h5py.File(path,"r") as h:
        for name in REQUIRED_GEOMETRY: require(name in h and isinstance(h[name],h5py.Dataset),f"{member}: missing {name}")
        n=int(h["sun_lon"].shape[0]) if h["sun_lon"].ndim==1 else -1; require(n>=0,f"{member}: bad sun_lon")
        for name in REQUIRED_GEOMETRY:
            ds=h[name]; require(ds.shape==(n,) and ds.dtype.kind in "fi",f"{member}: geometry schema changed {name}")
        # FIRST scientific values: solar longitude only. Blind mask is immutable before radiant/speed access.
        sol_all=np.asarray(h["sun_lon"][()],dtype=np.float64)
        valid_sol=np.isfinite(sol_all)&(sol_all>=0.0)&(sol_all<360.0)
        blind=valid_sol&(sol_all>=BLIND_LOW)&(sol_all<=BLIND_HIGH)
        keep=np.flatnonzero(valid_sol&~blind).astype(np.int64)
        slat=_read_retained(h["slat"],keep); slon=_read_retained(h["slon"],keep); vels=_read_retained(h["vels"],keep)
    sol=sol_all[keep]; good=np.isfinite(slat)&np.isfinite(slon)&np.isfinite(vels)&(slat>=-90)&(slat<=90)&(vels>=5)&(vels<=75)
    eligible=Counter()
    for local in np.flatnonzero(good):
        physical=int(keep[int(local)]); eid=event_id(year,member,physical); s=float(sol[int(local)])
        e={"id":eid,"year":year,"sol":s,"sun_lon":float(((float(slon[int(local)])+180.0)%360.0)-180.0),"ecl_lat":float(slat[int(local)]),"vg":float(vels[int(local)])}
        b=int(s//10.0)%36; eligible[b]+=1; push_smallest(heaps[b],e)
    return {"year":year,"member":member,"rows":n,"invalid_solar_longitude_rows":int(np.count_nonzero(~valid_sol)),"blind_removed_before_radiant_speed_read":int(np.count_nonzero(blind)),"radiant_speed_rows_read":int(len(keep)),"invalid_geometry_after_blind":int(np.count_nonzero(~good)),"eligible_geometry_before_density_cap":int(np.count_nonzero(good)),"eligible_by_bin_before_cap":{str(k):int(v) for k,v in sorted(eligible.items())},"target_interval_radiant_speed_read":False,"orbital_dataset_opened":False}


def stream_geometry(output:Path)->tuple[dict[int,list[dict[str,Any]]],dict[str,Any]]:
    heaps={year:{b:[] for b in range(36)} for year in YEARS}; months={year:set() for year in YEARS}; members=[]; audits=[]; stop=None
    tmp=output/"_geometry_tmp"; tmp.mkdir(parents=True,exist_ok=True)
    with requests.get(CONTENT_URL,timeout=(60,600),stream=True,headers={"User-Agent":"OrbitTrace-v6-LF-MAARSY-2018-2019/1.0","Accept-Encoding":"identity"}) as response:
        response.raise_for_status(); total=response.headers.get("Content-Length");
        if total is not None: require(int(total)==EXPECTED_FILE_SIZE,"MAARSY content length changed")
        response.raw.decode_content=False
        with tarfile.open(fileobj=response.raw,mode="r|gz") as tf:
            for item in tf:
                name=item.name.lstrip("./")
                if name.startswith(STOP_PREFIX): stop=name; break
                match=MONTH_RE.fullmatch(name)
                if match is None: continue
                year=int(match.group(1)); month=int(match.group(2)); require(month not in months[year],f"duplicate {year}-{month:02d}"); months[year].add(month)
                require(item.isfile(),f"nonfile {name}"); extracted=tf.extractfile(item); require(extracted is not None,f"cannot extract {name}")
                local=tmp/f"{year}-{month:02d}.h5"; written=0
                with local.open("wb") as fh:
                    while True:
                        chunk=extracted.read(1024*1024)
                        if not chunk: break
                        fh.write(chunk); written+=len(chunk)
                require(written==int(item.size),f"member size mismatch {name}")
                audits.append(parse_geometry_member(local,year,name,heaps[year])); members.append(name); local.unlink()
                print(f"MAARSY_GEOMETRY {year}-{month:02d} rows={audits[-1]['rows']:,} eligible={audits[-1]['eligible_geometry_before_density_cap']:,}",flush=True)
    require(stop is not None,"archive never reached 2020 header")
    for year in YEARS: require(months[year]==set(range(1,13)),f"incomplete MAARSY months {year}: {sorted(months[year])}")
    scan={}; selected={}
    for year in YEARS:
        rows=[]; bins={}
        for b in range(36):
            chosen=[x[2] for x in heaps[year][b]]; chosen.sort(key=lambda e:str(e["id"])); rows.extend(chosen); bins[str(b)]=len(chosen)
        rows.sort(key=lambda e:str(e["id"])); scan[year]=rows; selected[str(year)]=bins
    try: tmp.rmdir()
    except OSError: pass
    return scan,{"years":list(YEARS),"selected_months":{str(y):sorted(months[y]) for y in YEARS},"selected_members":members,"member_audits":audits,"stopped_at_first_2020_member_header":stop,"density_cap_per_10deg_bin":MAX_EVENTS_PER_BIN,"density_selection":"10,000 smallest SHA256(MAARSY|year|archive_member|row_index_0based) per fixed 10-degree bin","selected_by_bin_after_cap":selected,"selected_events":{str(y):len(scan[y]) for y in YEARS},"blind_before_radiant_speed":True,"target_interval_radiant_speed_read":False,"orbital_dataset_opened":False,"labels_used":False,"target_information_access":False}


def read_needed_orbits(needed_ids:set[str],output:Path)->tuple[dict[str,dict[str,float]],dict[str,Any]]:
    wanted:dict[str,dict[int,str]]={}
    for eid in sorted(needed_ids):
        _year,member,row=parse_event_id(eid); rowmap=wanted.setdefault(member,{}); require(row not in rowmap,f"duplicate orbit row {eid}"); rowmap[row]=eid
    seen=set(); orbits={}; invalid=[]; audits=[]; stop=None; tmp=output/"_orbit_tmp"; tmp.mkdir(parents=True,exist_ok=True)
    with requests.get(CONTENT_URL,timeout=(60,600),stream=True,headers={"User-Agent":"OrbitTrace-v6-LF-MAARSY-2018-2019-orbit/1.0","Accept-Encoding":"identity"}) as response:
        response.raise_for_status(); response.raw.decode_content=False
        with tarfile.open(fileobj=response.raw,mode="r|gz") as tf:
            for item in tf:
                name=item.name.lstrip("./")
                if name.startswith(STOP_PREFIX): stop=name; break
                rowmap=wanted.get(name)
                if rowmap is None: continue
                require(name not in seen and item.isfile(),f"bad needed member {name}"); seen.add(name); extracted=tf.extractfile(item); require(extracted is not None,f"cannot extract {name}")
                local=tmp/f"needed-{len(seen):03d}.h5"
                with local.open("wb") as fh:
                    while True:
                        chunk=extracted.read(1024*1024)
                        if not chunk: break
                        fh.write(chunk)
                rows=sorted(rowmap)
                with h5py.File(local,"r") as h:
                    require("kepler" in h and isinstance(h["kepler"],h5py.Dataset),f"missing kepler {name}"); ds=h["kepler"]
                    require(ds.ndim==2 and ds.shape[1]==6 and ds.dtype.kind in "fi",f"kepler schema changed {name}"); require(rows and rows[-1]<ds.shape[0],f"orbit row outside dataset {name}")
                    values=np.asarray(ds[np.asarray(rows,dtype=np.int64),:],dtype=np.float64)
                valid=0
                for i,row in enumerate(rows):
                    eid=rowmap[row]; a_m,e,inc,arg,node,_nu=[float(x) for x in values[i]]; q=abs((a_m/AU_M)*(1-e))
                    ok=bool(np.all(np.isfinite(values[i])) and q>0 and e>=0 and 0<=inc<=180 and math.isfinite(arg) and math.isfinite(node))
                    if not ok: invalid.append(eid); continue
                    orbits[eid]={"q":q,"e":e,"i":inc,"arg":arg%360.0,"node":node%360.0}; valid+=1
                audits.append({"member":name,"needed_rows":len(rows),"valid_orbit_rows":valid,"invalid_orbit_rows":len(rows)-valid,"kepler_shape":[int(x) for x in ds.shape],"kepler_dtype":str(ds.dtype)}); local.unlink()
    require(stop is not None,"archive never reached 2020 header"); require(set(wanted)==seen,f"missing needed archive members: {sorted(set(wanted)-seen)[:10]}")
    missing=needed_ids-set(orbits)-set(invalid); require(not missing,f"needed IDs neither valid nor invalid: {sorted(missing)[:10]}")
    try: tmp.rmdir()
    except OSError: pass
    return orbits,{"needed_family_events":len(needed_ids),"needed_archive_members":len(wanted),"seen_needed_archive_members":len(seen),"valid_orbital_events":len(orbits),"invalid_or_missing_orbital_events":len(needed_ids)-len(orbits),"member_audits":audits,"stopped_at_first_2020_member_header":stop,"native_kepler_mapping":["a_m","e","i_deg","omega_deg","Omega_deg","nu_deg"],"au_m":AU_M,"q_definition":"abs((a_m/AU_M)*(1-e))","kepler_std_opened":False,"geometry_fields_opened_this_stage":False,"orbital_elements_interpreted_only_after_rank_freeze":True,"target_information_access":False}
