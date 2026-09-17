"""Shared HTTP helpers."""

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


class FetchError(Exception):
    pass


def http_get(url, headers=None, params=None, timeout=20, tries=2):
    last = None
    for _ in range(tries):
        try:
            resp = requests.get(url, headers={**HEADERS, **(headers or {})},
                                params=params, timeout=timeout)
            if resp.status_code == 200:
                return resp
            last = FetchError(f"HTTP {resp.status_code} from {url}")
        except Exception as exc:  # noqa: BLE001 - surface any network error
            last = FetchError(f"network error: {exc}")
    raise last


def http_json(url, **kw):
    resp = http_get(url, **kw)
    try:
        return resp.json()
    except ValueError as exc:
        raise FetchError(f"invalid JSON from {url}") from exc


def http_post_json(url, payload, headers=None, timeout=25, tries=2):
    last = None
    for _ in range(tries):
        try:
            resp = requests.post(
                url, json=payload,
                headers={**HEADERS, "Content-Type": "application/json",
                         **(headers or {})},
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json()
            last = FetchError(f"HTTP {resp.status_code} from {url}")
        except Exception as exc:  # noqa: BLE001
            last = FetchError(f"network error: {exc}")
    raise last