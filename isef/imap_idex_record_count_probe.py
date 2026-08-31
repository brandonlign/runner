#!/usr/bin/env python3
"""Count public IDEX Release-1 L2A records without opening science values.

This stage remains behind the scientific-outcome information barrier. It uses
only directory filenames, file sizes, CDF variable metadata, and the record
count encoded in the CDF schema. It never calls varget().
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import cdflib
import requests

OUT = Path('results/imap_idex_record_count_probe')
OUT.mkdir(parents=True, exist_ok=True)
BASE = 'https://spdf.gsfc.nasa.gov/pub/data/imap/idex/l2a/sci-10days/2026/'
HREF_RE = re.compile(r'href=["\']([^"\']+\.cdf)["\']', re.I)


def list_cdfs():
    r = requests.get(BASE, timeout=(15, 60)); r.raise_for_status()
    return sorted(set(HREF_RE.findall(r.text)))


def download(url, path):
    n = 0
    with requests.get(url, stream=True, timeout=(15, 180)) as r:
        r.raise_for_status()
        with path.open('wb') as f:
            for ch in r.iter_content(1024 * 1024):
                if ch:
                    f.write(ch); n += len(ch)
    return n


def main():
    rows = []
    for name in list_cdfs():
        url = urljoin(BASE, name)
        p = OUT / name
        nbytes = download(url, p)
        c = cdflib.CDF(str(p))
        info = c.cdf_info()
        zvars = list(getattr(info, 'zVariables', []) or [])
        if 'epoch' not in zvars:
            raise RuntimeError(f'epoch missing from {name}')
        epoch_info = c.varinq('epoch')
        last = int(getattr(epoch_info, 'Last_Rec'))
        records = last + 1 if last >= 0 else 0
        # Cross-check all record-varying data variables share the same final
        # record where they depend on epoch; still metadata only.
        epoch_record_counts = {}
        for var in zvars:
            try:
                a = c.varattsget(var)
                if a.get('DEPEND_0') == 'epoch' or var == 'epoch':
                    vi = c.varinq(var)
                    epoch_record_counts[var] = int(getattr(vi, 'Last_Rec')) + 1
            except Exception:
                pass
        inconsistent = {k:v for k,v in epoch_record_counts.items() if v != records}
        rows.append({
            'file': name,
            'url': url,
            'bytes': nbytes,
            'records': records,
            'epoch_dependent_variable_count': len(epoch_record_counts),
            'inconsistent_record_counts': inconsistent,
        })
        p.unlink(missing_ok=True)

    counts = [r['records'] for r in rows]
    report = {
        'information_barrier': 'IDEX public filenames + CDF schema record counts only; zero science values opened',
        'dataset': 'IMAP_IDEX_L2A_SCI-10DAYS',
        'n_files': len(rows),
        'files': rows,
        'total_records_release1': sum(counts),
        'minimum_records_per_10day_file': min(counts) if counts else None,
        'maximum_records_per_10day_file': max(counts) if counts else None,
        'mean_records_per_file': sum(counts)/len(counts) if counts else None,
        'all_epoch_dependent_shapes_consistent': all(not r['inconsistent_record_counts'] for r in rows),
        'science_values_opened': False,
    }
    (OUT/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('n_files','total_records_release1','minimum_records_per_10day_file','maximum_records_per_10day_file','mean_records_per_file','all_epoch_dependent_shapes_consistent','science_values_opened')},indent=2,sort_keys=True))

if __name__=='__main__':
    main()
