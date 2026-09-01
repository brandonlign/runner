#!/usr/bin/env python3
"""Run the already-frozen matched-property analysis on validation RA 180-360 with detection-only rows."""
from pathlib import Path
src=Path(__file__).with_name('xmm_reprocessing_dev_properties.py').read_text()
src=src.replace("range(0,180,5)","range(180,360,5)")
src=src.replace("WHERE {BASE} AND s.ra >= {lo} AND s.ra < {hi}","WHERE {BASE} AND d.pps_srcnum IS NOT NULL AND s.ra >= {lo} AND s.ra < {hi}")
src=src.replace("results/xmm_reprocessing_dev_properties.json","results/xmm_reprocessing_validation_properties_detectiononly.json")
src=src.replace("'hemisphere':'development'","'hemisphere':'validation'")
ns={'__name__':'__main__','__file__':str(Path(__file__).with_name('xmm_reprocessing_dev_properties.py'))}
exec(compile(src,ns['__file__'],'exec'),ns)
