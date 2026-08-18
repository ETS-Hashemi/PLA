#!/usr/bin/env python3
"""Check that every URL in research/READING_LIST.md resolves.

Run on a machine with open network access (the development sandbox blocks
scholarly hosts). doi.org links count as resolvable when the DOI handle
redirects (HTTP 30x) — publisher pages behind the redirect often block
scripted clients, which says nothing about the DOI itself.

Usage:
    python3 scripts/check_links.py          # fetch and report every URL
    python3 scripts/check_links.py --list   # just list the URLs found
"""

import pathlib
import re
import sys
import urllib.error
import urllib.request

READING_LIST = pathlib.Path(__file__).resolve().parents[1] / "research" / "READING_LIST.md"
URL_RE = re.compile(r"https://[^\s<>\"']+")
USER_AGENT = "Mozilla/5.0 (compatible; PLA-link-check/1.0)"
TIMEOUT = 20


def extract_urls(text):
    urls = []
    for raw in URL_RE.findall(text):
        url = raw.rstrip(".,;")
        if url not in urls:
            urls.append(url)
    return urls


def check(url):
    """Return (ok, detail). doi.org: a 30x redirect proves the DOI exists."""
    is_doi = url.startswith("https://doi.org/")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    handlers = [NoRedirect()] if is_doi else []
    opener = urllib.request.build_opener(*handlers)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        response = opener.open(request, timeout=TIMEOUT)
        code = response.getcode()
        return code < 400, f"HTTP {code}"
    except urllib.error.HTTPError as err:
        if is_doi and err.code in (301, 302, 303, 307, 308):
            return True, f"HTTP {err.code} (DOI registered)"
        return False, f"HTTP {err.code}"
    except Exception as err:  # noqa: BLE001 - report any network failure
        return False, f"{type(err).__name__}: {err}"


def main():
    urls = extract_urls(READING_LIST.read_text(encoding="utf-8"))
    if not urls:
        print("No URLs found in", READING_LIST)
        return 1

    if "--list" in sys.argv:
        for url in urls:
            print(url)
        print(f"\n{len(urls)} URLs found.")
        return 0

    failures = 0
    for url in urls:
        ok, detail = check(url)
        print(f"{'OK  ' if ok else 'FAIL'}  {detail:<28} {url}")
        if not ok:
            failures += 1

    print(f"\n{len(urls) - failures}/{len(urls)} URLs resolved.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
