from orbittrace_pooled_year_centroid_v8 import run_development as v8
from clones import draw
YEARS=(2022,2023)
def make(hard,measurements,support,iteration):
    sol,sun,lat,vg,seed=draw(measurements,iteration)
    lookup={r['id']:{'id':r['id'],'year':int(r['year']),'sol':float(sol[i]),'sun_lon':float(sun[i]),'ecl_lat':float(lat[i]),'vg':float(vg[i]),'iau':0,'complex_key':'HIDDEN'} for i,r in enumerate(measurements)}
    families=[]
    for f in hard:
        g=dict(f); centers={}
        for y in YEARS:
            ids=[str(e) for e in f['event_ids'] if int(str(e)[:4])==y]
            events=[lookup[e] for e in ids]
            if not events: raise RuntimeError(f"empty cloned family-year {f['family_id']} {y}")
            centers[str(y)]=v8.pooled_centroid(events,support)
        g['centroids']=centers; families.append(g)
    return families,lookup,seed
