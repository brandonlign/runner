#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import requests

EXPECTED_P9_SOURCE = Path('/tmp/run_p9.py')
GMN_NETWORK_RETRY_DELAYS_SECONDS = (0, 1, 2, 4, 8, 16)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def compatible_exact_header_positions(text: str) -> tuple[list[str], dict[str, int]]:
    candidates: list[list[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.lstrip('\ufeff \t')
        if not line.startswith('#'):
            continue
        body = line[1:].strip()
        fields = [field.strip() for field in body.split(';')]
        if fields and fields[0] == 'Unique trajectory':
            candidates.append(fields)
    require(len(candidates) == 1, f"raw schema header not unique after whitespace normalization: {len(candidates)}")
    fields = candidates[0]

    def exact(name: str) -> int:
        hits = [idx for idx, field in enumerate(fields) if field == name]
        require(len(hits) == 1, f"raw schema field {name!r} not unique: {hits}")
        return hits[0]

    positions = {
        'id': exact('Unique trajectory'),
        'sol': exact('Sol lon'),
        'q': exact('q'),
        'e': exact('e'),
        'i': exact('i'),
        'peri': exact('peri'),
        'node': exact('node'),
    }
    require(len(set(positions.values())) == len(positions), f"raw schema positions overlap: {positions}")
    q_upper = [idx for idx, field in enumerate(fields) if field == 'Q']
    require(len(q_upper) == 1 and q_upper[0] != positions['q'], 'q/Q schema identity changed')
    return fields, positions


def _retry_network_request(
    call: Callable[[], Any],
    label: str,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> Any:
    last_error: requests.exceptions.RequestException | None = None
    for attempt, delay in enumerate(GMN_NETWORK_RETRY_DELAYS_SECONDS, start=1):
        if delay:
            sleep_fn(float(delay))
        try:
            value = call()
            if attempt > 1:
                print(f"PASS_GMN_NETWORK_RETRY label={label} attempt={attempt}", flush=True)
            return value
        except requests.exceptions.RequestException as exc:
            last_error = exc
            print(
                f"RETRY_GMN_NETWORK_FAILURE label={label} attempt={attempt}/{len(GMN_NETWORK_RETRY_DELAYS_SECONDS)} type={type(exc).__name__}",
                flush=True,
            )
    require(last_error is not None, f"network retry exhausted without captured error for {label}")
    raise last_error


def install_gmn_fetch_resilience(module: Any, *, sleep_fn: Callable[[float], None] = time.sleep) -> None:
    """Add transport-only retry/cache around the exact GMN API calls used by P9.

    Successful payload text is returned byte-for-byte unchanged. Only
    requests.exceptions.RequestException is retried. There is no alternate
    endpoint, alternate data source, synthetic fallback, or scientific change.
    """
    dd = module.dd
    original_get_all_monthly_file_urls = dd.get_all_monthly_file_urls
    original_get_monthly_file_content_by_date = dd.get_monthly_file_content_by_date
    listing_cache: list[Any] = []
    monthly_cache: dict[tuple[int, int], str] = {}

    def robust_get_all_monthly_file_urls() -> Any:
        if listing_cache:
            return listing_cache[0]
        value = _retry_network_request(
            original_get_all_monthly_file_urls,
            "monthly-directory-index",
            sleep_fn=sleep_fn,
        )
        listing_cache.append(value)
        try:
            count = len(value)
        except TypeError:
            count = -1
        print(f"CACHE_GMN_MONTHLY_DIRECTORY_INDEX entries={count}", flush=True)
        return value

    def robust_get_monthly_file_content_by_date(year: int, month: int) -> str:
        key = (int(year), int(month))
        if key in monthly_cache:
            return monthly_cache[key]
        value = _retry_network_request(
            lambda: original_get_monthly_file_content_by_date(year, month),
            f"monthly-trajectory-{key[0]:04d}-{key[1]:02d}",
            sleep_fn=sleep_fn,
        )
        require(isinstance(value, str), f"GMN monthly payload type changed for {key}: {type(value).__name__}")
        monthly_cache[key] = value
        payload_sha = hashlib.sha256(value.encode('utf-8')).hexdigest()
        print(
            f"CACHE_GMN_MONTHLY_TRAJECTORY year={key[0]} month={key[1]:02d} chars={len(value)} sha256={payload_sha}",
            flush=True,
        )
        return value

    # The gmn_python_api monthly helper resolves get_all_monthly_file_urls from
    # its module globals at call time, so this removes 23 redundant directory
    # fetches while leaving monthly-file selection logic inside the exact API.
    dd.get_all_monthly_file_urls = robust_get_all_monthly_file_urls
    dd.get_monthly_file_content_by_date = robust_get_monthly_file_content_by_date


def load_p9() -> Any:
    require(EXPECTED_P9_SOURCE.is_file(), f'P9 runtime missing: {EXPECTED_P9_SOURCE}')
    spec = importlib.util.spec_from_file_location('orbittrace_p9_runtime', EXPECTED_P9_SOURCE)
    require(spec is not None and spec.loader is not None, 'cannot load P9 runtime')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def self_test_fetch_resilience() -> None:
    counters = {'listing': 0, 'monthly': 0}
    fake_dd = SimpleNamespace()

    def flaky_listing() -> list[str]:
        counters['listing'] += 1
        if counters['listing'] < 3:
            raise requests.exceptions.ReadTimeout('synthetic listing timeout')
        return ['2022-01', '2022-02']

    def flaky_monthly(year: int, month: int) -> str:
        # Exercise the monkey-patched cached directory lookup exactly as the real
        # gmn_python_api helper does through its module global.
        fake_dd.get_all_monthly_file_urls()
        counters['monthly'] += 1
        if counters['monthly'] == 1:
            raise requests.exceptions.HTTPError('synthetic 502')
        return f'exact-payload-{year:04d}-{month:02d}'

    fake_dd.get_all_monthly_file_urls = flaky_listing
    fake_dd.get_monthly_file_content_by_date = flaky_monthly
    fake_module = SimpleNamespace(dd=fake_dd)
    install_gmn_fetch_resilience(fake_module, sleep_fn=lambda _seconds: None)
    value1 = fake_module.dd.get_monthly_file_content_by_date(2022, 1)
    value2 = fake_module.dd.get_monthly_file_content_by_date(2022, 1)
    require(value1 == 'exact-payload-2022-01' and value2 == value1, 'network wrapper changed successful payload')
    require(counters['listing'] == 3, f"directory retry/cache count changed: {counters}")
    require(counters['monthly'] == 2, f"monthly retry/cache count changed: {counters}")
    print('PASS_P9_GMN_FETCH_RESILIENCE_SELF_TEST', flush=True)


def self_test() -> None:
    names = ['Unique trajectory','Beginning','Beginning','IAU','IAU','Sol lon','App LST','RAgeo','+/-','DECgeo','+/-','LAMgeo','+/-','BETgeo','+/-','Vgeo','+/-','LAMhel','+/-','BEThel','+/-','Vhel','+/-','a','+/-','e','+/-','i','+/-','peri','+/-','node','+/-','Pi','+/-','b','+/-','q','+/-','f','+/-','M','+/-','Q']
    expected = {'id':0,'sol':5,'q':37,'e':25,'i':27,'peri':29,'node':31}
    for prefix in ('# ', '#  ', '\ufeff#  ', ' \t#\t'):
        fields, positions = compatible_exact_header_positions(prefix + ';'.join(names) + '\nrow;ignored')
        require(fields == names, 'header whitespace normalization changed fields')
        require(positions == expected, f'header whitespace normalization changed positions: {positions}')
    print('PASS_P9_HEADER_WHITESPACE_COMPAT_SELF_TEST')
    self_test_fetch_resilience()


def main() -> int:
    self_test()
    module = load_p9()
    module.exact_header_positions = compatible_exact_header_positions
    install_gmn_fetch_resilience(module)
    print('P9_GMN_FETCH_RESILIENCE=network-exception-retry+single-directory-cache+successful-month-cache; no alternate source', flush=True)
    return int(module.main())


if __name__ == '__main__':
    raise SystemExit(main())
