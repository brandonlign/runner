#!/usr/bin/env python3
"""Target-blind access/structure probe for the first public IMAP science release.

Purpose: determine whether the fresh July 2026 IMAP public release is technically
usable for a new ISEF project *before* inspecting scientific outcome
distributions. This script inventories public archive files and inspects CDF
metadata/record structure only. It does not print or summarize science-variable
values, spectra, elemental abundances, impact compositions, or event directions.

The first priority is IDEX L2A sci-10days because event-level dust composition
could provide an unusually fresh discovery surface. Other Release-1 datasets
are inventoried at directory level for fallback comparison.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import cdflib
import requests

OUT = Path('results/imap_release1_access_probe')
OUT.mkdir(parents=True, exist_ok=True)

ROOT = 'https://spdf.gsfc.nasa.gov/pub/data/imap/'
DATASETS = {
    'idex_l2a_sci_10days': 'idex/l2a/sci-10days/',
    'codice_l2_hi_direct_events': 'codice/l2/hi-direct-events/',
    'codice_l2_lo_direct_events': 'codice/l2/lo-direct-events/',
    'swapi_l2_sci': 'swapi/l2/sci/',
    'swe_l2_sci': 'swe/l2/sci/',
    'mag_l2_norm_rtn': 'mag/l2/norm-rtn/',
    'hit_l2_standard': 'hit/l2/standard/',
    'glows_l2_hist': 'glows/l2/hist/',
}

HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
CDF_RE = re.compile(r'\.cdf$', re.I)


def get_text(url: str) -> str:
    r = requests.get(url, timeout=(15, 60))
    r.raise_for_status()
    return r.text


def listing(url: str):
    html = get_text(url)
    hrefs = []
    for h in HREF_RE.findall(html):
        if h.startswith('?') or h.startswith('/') or h in ('../', './'):
            continue
        hrefs.append(h)
    return sorted(set(hrefs))


def recursive_inventory(base: str, max_depth: int = 3):
    """List names/URLs only; never decode science values."""
    files = []
    dirs_seen = set()

    def walk(url: str, depth: int):
        if url in dirs_seen or depth > max_depth:
            return
        dirs_seen.add(url)
        for h in listing(url):
            full = urljoin(url, h)
            if h.endswith('/'):
                walk(full, depth + 1)
            else:
                files.append({'name': h, 'url': full})

    walk(base, 0)
    return files, sorted(dirs_seen)


def head_meta(url: str):
    r = requests.head(url, allow_redirects=True, timeout=(15, 60))
    if r.status_code >= 400:
        r = requests.get(url, headers={'Range': 'bytes=0-0'}, stream=True,
                         timeout=(15, 60))
    r.raise_for_status()
    size = r.headers.get('Content-Length')
    cr = r.headers.get('Content-Range')
    if cr and '/' in cr:
        size = cr.rsplit('/', 1)[-1]
    return {
        'content_length_bytes': int(size) if size and size.isdigit() else None,
        'last_modified': r.headers.get('Last-Modified'),
        'etag': r.headers.get('ETag'),
        'content_type': r.headers.get('Content-Type'),
    }


def choose_representative(cdfs):
    """Outcome-independent representative: lexicographically earliest public CDF."""
    if not cdfs:
        return None
    return sorted(cdfs, key=lambda x: x['url'])[0]


def download(url: str, dest: Path):
    h = hashlib.sha256()
    n = 0
    with requests.get(url, stream=True, timeout=(15, 180)) as r:
        r.raise_for_status()
        with dest.open('wb') as f:
            for chunk in r.iter_content(1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk); h.update(chunk); n += len(chunk)
    return {'bytes': n, 'sha256': h.hexdigest()}


def safe_scalar(v):
    if isinstance(v, bytes):
        return v.decode('utf-8', 'replace')
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    if isinstance(v, (list, tuple)):
        return [safe_scalar(x) for x in v[:20]]
    try:
        return safe_scalar(v.tolist())
    except Exception:
        return str(v)


def cdf_structure(path: Path):
    """Metadata/schema only. Never call varget on a science variable."""
    c = cdflib.CDF(str(path))
    info = c.cdf_info()
    zvars = list(getattr(info, 'zVariables', []) or [])
    rvars = list(getattr(info, 'rVariables', []) or [])
    out = {
        'cdf_info': {
            'version': safe_scalar(getattr(info, 'Version', None)),
            'encoding': safe_scalar(getattr(info, 'Encoding', None)),
            'majority': safe_scalar(getattr(info, 'Majority', None)),
            'zvariables': zvars,
            'rvariables': rvars,
            'num_zvariables': len(zvars),
            'num_rvariables': len(rvars),
        },
        'global_attributes': {},
        'variables': {},
        'science_values_opened': False,
    }
    try:
        gattrs = c.globalattsget()
        for k, v in gattrs.items():
            out['global_attributes'][k] = safe_scalar(v)
    except Exception as exc:
        out['global_attributes_error'] = repr(exc)

    for name in zvars + rvars:
        try:
            vi = c.varinq(name)
            va = c.varattsget(name)
            out['variables'][name] = {
                'data_type': safe_scalar(getattr(vi, 'Data_Type_Description', None)),
                'num_elements': safe_scalar(getattr(vi, 'Num_Elements', None)),
                'num_dims': safe_scalar(getattr(vi, 'Num_Dims', None)),
                'dim_sizes': safe_scalar(getattr(vi, 'Dim_Sizes', None)),
                'last_record': safe_scalar(getattr(vi, 'Last_Rec', None)),
                'rec_vary': safe_scalar(getattr(vi, 'Rec_Vary', None)),
                'attributes': {k: safe_scalar(v) for k, v in va.items()},
            }
        except Exception as exc:
            out['variables'][name] = {'metadata_error': repr(exc)}
    # cdflib.CDF is a pure reader in this version and exposes no close() method.
    return out


def main():
    report = {
        'information_barrier': (
            'Public IMAP Release-1 archive inventory + CDF metadata/schema only; '
            'no science-variable values or outcome distributions inspected.'
        ),
        'archive_root': ROOT,
        'datasets': {},
        'idex_representative_cdf': None,
    }

    for label, rel in DATASETS.items():
        url = urljoin(ROOT, rel)
        try:
            files, dirs = recursive_inventory(url, max_depth=3)
            cdfs = [x for x in files if CDF_RE.search(x['name'])]
            entry = {
                'url': url,
                'access': 'PASS',
                'directories_seen_n': len(dirs),
                'files_n': len(files),
                'cdf_files_n': len(cdfs),
                'first_cdf': sorted([x['url'] for x in cdfs])[:1],
                'last_cdf': sorted([x['url'] for x in cdfs])[-1:] if cdfs else [],
            }
            if cdfs:
                ordered = sorted(cdfs, key=lambda x: x['url'])
                entry['first_cdf_http_metadata'] = head_meta(ordered[0]['url'])
                entry['last_cdf_http_metadata'] = head_meta(ordered[-1]['url'])
            report['datasets'][label] = entry
        except Exception as exc:
            report['datasets'][label] = {'url': url, 'access': 'FAIL', 'error': repr(exc)}

    idex = report['datasets'].get('idex_l2a_sci_10days', {})
    if idex.get('access') == 'PASS':
        files, _ = recursive_inventory(idex['url'], max_depth=3)
        cdfs = [x for x in files if CDF_RE.search(x['name'])]
        rep = choose_representative(cdfs)
        if rep:
            dest = OUT / 'representative_idex_metadata_probe.cdf'
            dl = download(rep['url'], dest)
            structure = cdf_structure(dest)
            report['idex_representative_cdf'] = {
                'selection_rule': 'lexicographically earliest public CDF; outcome-independent',
                'url': rep['url'],
                'download': dl,
                'structure': structure,
            }
            dest.unlink(missing_ok=True)

    (OUT / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'datasets': {k: {kk: vv for kk, vv in v.items() if kk in ('access','files_n','cdf_files_n','first_cdf','last_cdf')}
                     for k, v in report['datasets'].items()},
        'idex_metadata_probe_available': bool(report['idex_representative_cdf']),
        'science_values_opened': False,
    }, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
