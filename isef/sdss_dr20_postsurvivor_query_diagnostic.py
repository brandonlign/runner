#!/usr/bin/env python3
import json, urllib.parse, urllib.request
from pathlib import Path
ID=103285333
SQL='https://skyserver.sdss.org/dr20/SkyServerWS/SearchTools/SqlSearch'
OUT=Path('results/sdss_dr20_postsurvivor_query_diagnostic.json'); OUT.parent.mkdir(exist_ok=True)
def go(q):
    u=SQL+'?'+urllib.parse.urlencode({'cmd':q,'format':'json'})
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ISEF-DR20-PostSurvivorDiag/1.0'}),timeout=120) as r:
            raw=r.read().decode('utf-8','replace'); return {'ok':True,'response':json.loads(raw)}
    except Exception as e: return {'ok':False,'error':type(e).__name__+': '+str(e)}
queries={
 'allstar_basic':f'SELECT sdss_id,gaia_dr3_source_id,ra,dec,telescope,v_rad,e_v_rad,std_v_rad,n_good_rvs,snr,zwarning_flags,nmf_flags FROM mwm_boss_allstar WHERE sdss_id={ID}',
 'allstar_alt_rv':f'SELECT sdss_id,xcsao_meanrxc,xcorr_v_rad,xcorr_v_rel,xcorr_e_v_rel,boss_net_v_rad,boss_net_e_v_rad FROM mwm_boss_allstar WHERE sdss_id={ID}',
 'allstar_gaia':f'SELECT sdss_id,gaia_v_rad,gaia_e_v_rad,n_boss_visits,boss_min_mjd,boss_max_mjd,n_apogee_visits,apogee_min_mjd,apogee_max_mjd FROM mwm_boss_allstar WHERE sdss_id={ID}',
 'allstar_params':f'SELECT sdss_id,teff,e_teff,logg,e_logg,v_sini,e_v_sini,m_h_atm,e_m_h_atm FROM mwm_boss_allstar WHERE sdss_id={ID}',
 'visit_basic':f'SELECT sdss_id,mjd,fieldid,spec_file,telescope,snr,zwarning_flags,xcsao_v_rad,xcsao_e_v_rad,xcsao_rxc FROM mwm_boss_allvisit WHERE sdss_id={ID} ORDER BY mjd',
 'gravpot_top': 'SELECT TOP 1 * FROM GravPot16'
}
o={k:go(q) for k,q in queries.items()}; OUT.write_text(json.dumps(o,indent=2)+'\n'); print(json.dumps(o,indent=2))
