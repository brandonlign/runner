#!/usr/bin/env python3
"""Audit SonotaCo-2023 fields before HDBSCAN; computes no clusters or scores."""
import argparse, csv, hashlib, io, json, math, zipfile
from collections import Counter
from pathlib import Path

ARCHIVE_SHA256='9f44696f99164801ff405dab90f68df3666b0d6734fed464a95e7ed0d6f5f430'
EXPECTED_ROWS=47087
FIELDS=['sol(deg)','ra(deg)','de(deg)','vg(km/s)','vg sd(km/s)','q(AU)','e','Qc(deg)','Shower']
SPO={'','...','-','0','SPO','SPORADIC','NONE','NAN'}

def number(value):
    try: x=float(str(value).strip())
    except (TypeError,ValueError): return None
    return x if math.isfinite(x) else None

def stats(values):
    x=sorted(values)
    if not x: return {'count':0}
    def q(p):
        z=p*(len(x)-1); lo=int(z); hi=min(lo+1,len(x)-1); w=z-lo
        return x[lo]*(1-w)+x[hi]*w
    return {'count':len(x),'min':x[0],'p01':q(.01),'p05':q(.05),'median':q(.5),'p95':q(.95),'p99':q(.99),'max':x[-1]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--archive',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    payload=a.archive.read_bytes(); digest=hashlib.sha256(payload).hexdigest()
    if digest!=ARCHIVE_SHA256: raise RuntimeError(digest)
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        names=[n for n in z.namelist() if n.lower().endswith('_s.csv')]
        if len(names)!=1: raise RuntimeError(names)
        member=names[0]; csv_bytes=z.read(member)
    reader=csv.DictReader(io.StringIO(csv_bytes.decode('utf-8-sig'),newline=''))
    header=[(x or '').strip() for x in (reader.fieldnames or [])]
    missing=sorted(set(FIELDS)-set(header))
    if missing: raise RuntimeError(missing)
    rows=core=0; parse_fail=Counter(); passes=Counter(); patterns=Counter(); raw_labels=Counter(); pass_labels=Counter(); token_counts=Counter(); exact_quality=0; exact_sporadic_quality=0; exact_primary_labels=Counter()
    series={k:[] for k in ['Qc','vg','vg_sd','vg_sd_over_vg','q','e']}
    for raw in reader:
        rows+=1; r={(k or '').strip():v for k,v in raw.items()}
        vals={f:number(r.get(f)) for f in FIELDS[:-1]}
        for f,v in vals.items():
            if v is None: parse_fail[f]+=1
        required=[vals[x] for x in ['sol(deg)','ra(deg)','de(deg)','vg(km/s)','vg sd(km/s)','Qc(deg)']]
        if any(v is None for v in required): continue
        core+=1; vg=vals['vg(km/s)']; vg_sd=vals['vg sd(km/s)']; qv=vals['q(AU)']; ev=vals['e']; qc=vals['Qc(deg)']; ratio=vg_sd/vg if vg>0 else math.inf
        series['Qc'].append(qc); series['vg'].append(vg); series['vg_sd'].append(vg_sd); series['vg_sd_over_vg'].append(ratio)
        if qv is not None: series['q'].append(qv)
        if ev is not None: series['e'].append(ev)
        label=str(r.get('Shower') or '').strip(); token_counts[label]+=1; label='SPORADIC' if label.upper() in SPO else label
        if label!='SPORADIC': raw_labels[label]+=1
        checks={'convergence':qc>=15,'velocity':vg>0 and vg_sd>=0 and ratio<=.10,'eccentricity':ev is not None and 0<=ev<=1,'perihelion':qv is not None and 0<qv<=1}
        for k,v in checks.items(): passes[k]+=int(v)
        failed=tuple(sorted(k for k,v in checks.items() if not v)); patterns['|'.join(failed) if failed else 'PASS_ALL']+=1
        if not failed:
            exact_quality+=1
            if label=='SPORADIC': exact_sporadic_quality+=1
            else: exact_primary_labels[label]+=1; pass_labels[label]+=1
    out={'classification':'pre-clustering diagnostic; no HDBSCAN fit or score','archive_sha256':digest,'member':member,'member_sha256':hashlib.sha256(csv_bytes).hexdigest(),'header_width':len(header),'header':header,'required_missing':missing,'rows':rows,'expected_rows':EXPECTED_ROWS,'core_rows':core,'parse_failures':dict(parse_fail),'criterion_pass_counts':dict(passes),'all_pass':patterns['PASS_ALL'],'patterns':dict(patterns.most_common()),'summaries':{k:stats(v) for k,v in series.items()},'raw_labeled_events':sum(raw_labels.values()),'raw_labels':len(raw_labels),'largest_raw_labels':raw_labels.most_common(20),'pass_labeled_events':sum(pass_labels.values()),'pass_labels':len(pass_labels),'largest_pass_labels':pass_labels.most_common(20),'largest_raw_tokens':token_counts.most_common(20),'runner_exact_quality_rows':exact_quality,'runner_exact_quality_sporadic_rows':exact_sporadic_quality,'runner_exact_labels_at_least_100':sorted([[k,v] for k,v in exact_primary_labels.items() if v>=100]),'gates':{'archive':digest==ARCHIVE_SHA256,'rows':rows==EXPECTED_ROWS,'fields':not missing,'no_clustering':True}}
    (a.output/'sonotaco_2023_quality_diagnostic.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ['rows','core_rows','parse_failures','criterion_pass_counts','all_pass','patterns','summaries','runner_exact_quality_rows','runner_exact_quality_sporadic_rows','runner_exact_labels_at_least_100','largest_raw_tokens']},indent=2))
if __name__=='__main__': main()
