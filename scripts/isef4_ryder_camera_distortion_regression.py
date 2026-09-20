#!/usr/bin/env python3
"""No-image right/left NAC CSM distortion serialization regression tests."""
import copy,sys
sys.path.insert(0,"scripts")
from isef4_isis_camera_triage import normalize_lroc_nac_distortion

def case(ikid,val,shape="scalar"):
    coeff=val if shape=="scalar" else [val]
    return {"name_model":"USGS_ASTRO_LINE_SCANNER_SENSOR_MODEL",
        "naif_keywords":{f"INS{ikid}_OD_K":val},
        "optical_distortion":{"lrolrocnac":{"coefficients":coeff}}}
def raises(x):
    try:normalize_lroc_nac_distortion(x)
    except ValueError:return True
    return False
def main():
    right=case("-85610",.0000183)
    r=normalize_lroc_nac_distortion(right)
    assert r["verified_source_key"]=="INS-85610_OD_K"
    assert right["optical_distortion"]["lrolrocnac"]["coefficients"]==[.0000183]
    assert r["instrument"]=="NAC-R (-85610)"
    assert r["status"]=="repaired_derived_isd_only"
    left=case("-85600",.0000179)
    assert normalize_lroc_nac_distortion(left)["instrument"]=="NAC-L (-85600)"
    existing=case("-85610",.0000183,"list")
    assert normalize_lroc_nac_distortion(existing)["status"]=="already_vector"
    mismatch=case("-85610",.0000183)
    mismatch["optical_distortion"]["lrolrocnac"]["coefficients"]=.000015
    assert raises(mismatch)
    ambiguous=case("-85610",.0000183)
    ambiguous["naif_keywords"]["INS-85600_OD_K"]=.0000183
    assert raises(ambiguous)
    unknown=case("-85610",.0000183)
    unknown["naif_keywords"]={"INS-85620_OD_K":.0000183}
    assert raises(unknown)
    wrong_model=case("-85610",.0000183)
    wrong_model["name_model"]="USGS_ASTRO_FRAME_SENSOR_MODEL"
    assert raises(wrong_model)
    print("PASS: right NAC source-derived scalar fix; left NAC unchanged; vector idempotence; 4 independent reject gates")
if __name__=="__main__":main()
