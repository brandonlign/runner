#!/usr/bin/env python3
import json, urllib.parse, urllib.request, io
from pathlib import Path
from astropy.table import Table

SDSS_ID=103285333
GAIA_ID=5868283055734381184
SQL='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
GAIA='https://gea.esac.esa.int/tap-server/tap/sync'
OUT=Path('results/sdss_dr20_postsurvivor_candidate_audit.json'); OUT.parent.mkdir(exist_ok=True)

def sql(q):
    u=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
    req=urllib.request.Request(u,headers={'User-Agent':'ISEF-DR20-PostSurvivor/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r: o=json.loads(r.read().decode())
    tabs=[x for x in o if isinstance(x,dict) and x.get('TableName')=='Table1']
    return tabs[0].get('Rows',[]) if tabs else []

def gaia(q):
    data=urllib.parse.urlencode({'REQUEST':'doQuery','LANG':'ADQL','FORMAT':'votable','QUERY':q}).encode()
    req=urllib.request.Request(GAIA,data=data,headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'ISEF-DR20-PostSurvivor/1.0'})
    with urllib.request.urlopen(req,timeout=180) as r: raw=r.read()
    t=Table.read(io.BytesIO(raw),format='votable')
    out=[]
    for row in t:
        d={}
        for n in t.colnames:
            v=row[n]
            try: v=v.item()
            except Exception: pass
            if hasattr(v,'mask') and v.mask: v=None
            if isinstance(v,bytes): v=v.decode(errors='replace')
            d[n]=v
        out.append(d)
    return out

o={'status':'POSTSURVIVOR_IDENTITY_AUDIT','sdss_id':SDSS_ID,'gaia_dr3_source_id':GAIA_ID}
try:
    fields='sdss_id,gaia_dr3_source_id,ra,dec,telescope,n_boss_visits,boss_min_mjd,boss_max_mjd,n_apogee_visits,apogee_min_mjd,apogee_max_mjd,v_rad,e_v_rad,std_v_rad,n_good_rvs,snr,zwarning_flags,nmf_flags,xcsao_meanrxc,xcorr_v_rad,xcorr_v_rel,xcorr_e_v_rel,boss_net_v_rad,boss_net_e_v_rad,gaia_v_rad,gaia_e_v_rad,teff,e_teff,logg,e_logg,v_sini,e_v_sini,m_h_atm,e_m_h_atm,classification,spectral_type,sub_type'
    o['boss_summary']=sql(f"SELECT {fields} FROM mwm_boss_allstar WHERE sdss_id={SDSS_ID}")
    vf='sdss_id,mjd,fieldid,spec_file,n_exp,exptime,telescope,snr,zwarning_flags,xcsao_v_rad,xcsao_e_v_rad,xcsao_teff,xcsao_e_teff,xcsao_logg,xcsao_e_logg,xcsao_fe_h,xcsao_e_fe_h,xcsao_rxc'
    o['boss_visits']=sql(f"SELECT {vf} FROM mwm_boss_allvisit WHERE sdss_id={SDSS_ID} ORDER BY mjd")
    o['gaia_dr3']=gaia(f"SELECT source_id,radial_velocity,radial_velocity_error,rv_nb_transits,rv_expected_sig_to_noise,rv_renormalised_gof,rv_chisq_pvalue,grvs_mag,ruwe,duplicated_source,non_single_star,ipd_frac_multi_peak,astrometric_excess_noise FROM gaiadr3.gaia_source WHERE source_id={GAIA_ID}")
    gp_queries=[
      f"SELECT TOP 5 * FROM GravPot16 WHERE sdss_id={SDSS_ID}",
      f"SELECT TOP 5 * FROM GravPot16 WHERE gaia_dr3_source_id={GAIA_ID}",
      f"SELECT TOP 5 * FROM GravPot16 WHERE gaia_source_id={GAIA_ID}"
    ]
    gp=[]
    for q in gp_queries:
        try:
            rows=sql(q); gp.append({'query':q,'rows':rows})
            if rows: break
        except Exception as e: gp.append({'query':q,'error':type(e).__name__+': '+str(e)[:300]})
    o['gravpot16_attempts']=gp
    o['success']=True
except Exception as e:
    o['success']=False; o['error']=type(e).__name__+': '+str(e)
OUT.write_text(json.dumps(o,indent=2,default=str)+'\n'); print(json.dumps(o,indent=2,default=str))
