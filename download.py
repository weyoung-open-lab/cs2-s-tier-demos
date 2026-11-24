#!/usr/bin/env python3
"""Download the CS2 S-Tier Demos dataset from this repository's GitHub Releases.

Only the Python standard library is needed (Python 3.8+). Downloads resume after an interruption, every file is
checked against the release's SHA-256 list, and the raw tar chunks are extracted into the original Kaggle layout.

    python download.py --list                       # what is available
    python download.py clean                        # cleaned tables used in the paper (~1.7 GB)
    python download.py raw-member-a                 # one raw part (~27 GB)
    python download.py raw-member-a --only E57      # only the chunks that contain event E57
    python download.py all                          # everything (~135 GB)
    python download.py all --out /data/cs2 --keep-tar

Set GITHUB_TOKEN to raise the API rate limit; HTTPS_PROXY is honoured.
"""
import argparse
import hashlib
import json
import os
import sys
import tarfile
import time
import urllib.error
import urllib.request

REPO = "weyoung-open-lab/cs2-s-tier-demos"
PARTS = ["member-a", "member-b", "member-c", "member-d", "member-e", "member-e2", "patch"]
TAGS = ["clean-v1"] + [f"raw-{p}" for p in PARTS]
ALIASES = {"clean": ["clean-v1"], "raw": TAGS[1:], "all": TAGS}


def request(url, headers=None):
    h = {"User-Agent": "cs2-s-tier-demos-downloader", **(headers or {})}
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        h["Authorization"] = f"Bearer {tok}"
    return urllib.request.Request(url, headers=h)


def get(url, tries=5):
    """GET a small file; retries on network errors (HTTP errors such as 404 are raised at once)."""
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request(url), timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, OSError) as e:
            if attempt == tries - 1:
                raise
            print(f"    network error ({e}); retrying in {5 * (attempt + 1)} s")
            time.sleep(5 * (attempt + 1))


def release(tag):
    return json.loads(get(f"https://api.github.com/repos/{REPO}/releases/tags/{tag}"))


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1000:
            return f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} TB"


def checksums(rel):
    """{file name: sha256} from the release's *SHA256SUMS.txt asset."""
    out = {}
    for a in rel["assets"]:
        if a["name"].endswith("SHA256SUMS.txt"):
            for line in get(a["browser_download_url"]).decode().splitlines():
                if line.strip():
                    sha, name = line.split(None, 1)
                    out[name.strip()] = sha
    return out


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url, dest, size):
    """Download with resume; retries on network errors."""
    for attempt in range(10):
        have = os.path.getsize(dest) if os.path.exists(dest) else 0
        if have == size:
            return
        if have > size:
            os.remove(dest)
            have = 0
        try:
            req = request(url, {"Range": f"bytes={have}-"} if have else None)
            with urllib.request.urlopen(req, timeout=120) as r:
                if have and r.status != 206:              # server ignored the range: start over
                    have = 0
                with open(dest, "ab" if have else "wb") as f:
                    t0, done = time.time(), have
                    while True:
                        b = r.read(1 << 20)
                        if not b:
                            break
                        f.write(b)
                        done += len(b)
                        rate = (done - have) / max(time.time() - t0, 1e-3)
                        print(f"\r    {human(done)} / {human(size)}  {human(rate)}/s   ", end="", flush=True)
            print()
        except (urllib.error.URLError, OSError) as e:
            print(f"\n    network error ({e}); retrying in {10 * (attempt + 1)} s")
            time.sleep(10 * (attempt + 1))
    if not os.path.exists(dest) or os.path.getsize(dest) != size:
        raise SystemExit(f"could not download {url}")


def extract(path, out):
    with tarfile.open(path) as t:
        if hasattr(tarfile, "data_filter"):
            t.extractall(out, filter="data")
        else:                                              # Python < 3.12: refuse absolute or parent paths
            for m in t.getmembers():
                p = os.path.normpath(m.name)
                if p.startswith(("/", "..")) or not (m.isfile() or m.isdir()):
                    raise SystemExit(f"unsafe member {m.name} in {path}")
            t.extractall(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", nargs="*", help="clean | raw | all | a release tag such as raw-member-a")
    ap.add_argument("--list", action="store_true", help="list releases and sizes")
    ap.add_argument("--out", default="cs2-data", help="output folder (default: ./cs2-data)")
    ap.add_argument("--only", help="raw parts: only chunks whose name contains this text, e.g. E57")
    ap.add_argument("--keep-tar", action="store_true", help="keep the downloaded tar chunks after extracting")
    ap.add_argument("--no-extract", action="store_true", help="download and verify only")
    a = ap.parse_args()
    if a.list or not a.what:
        for tag in TAGS:
            try:
                r = release(tag)
                files = [x for x in r["assets"] if not x["name"].endswith(("SHA256SUMS.txt", "_manifest.csv"))]
                print(f"{tag:16s} {len(files):3d} files  {human(sum(x['size'] for x in files)):>9s}   {r['name']}")
            except urllib.error.HTTPError as e:
                print(f"{tag:16s} not available ({e.code})")
        return
    tags = []
    for w in a.what:
        tags += ALIASES.get(w, [w])
    os.makedirs(a.out, exist_ok=True)
    for tag in tags:
        rel = release(tag)
        sums = checksums(rel)
        dest_dir = os.path.join(a.out, "clean") if tag == "clean-v1" else os.path.join(a.out, "_downloads")
        os.makedirs(dest_dir, exist_ok=True)
        assets = sorted(rel["assets"], key=lambda x: x["name"])
        if a.only and tag != "clean-v1":
            assets = [x for x in assets if a.only in x["name"] or x["name"].endswith(("_meta.tar", ".txt", ".csv"))]
        print(f"== {tag}: {len(assets)} files, {human(sum(x['size'] for x in assets))}")
        for x in assets:
            name = x["name"]
            dest = os.path.join(dest_dir if tag == "clean-v1" or name.endswith(".tar") else a.out, name)
            done_mark = os.path.join(a.out, "_downloads", f".{name}.extracted")
            if os.path.exists(done_mark):
                print(f"  {name}: already extracted")
                continue
            print(f"  {name}")
            fetch(x["browser_download_url"], dest, x["size"])
            if name in sums and sha256(dest) != sums[name]:
                os.remove(dest)
                raise SystemExit(f"checksum mismatch for {name}; deleted, run the command again")
            if name.endswith(".tar") and not a.no_extract:
                extract(dest, a.out)
                os.makedirs(os.path.dirname(done_mark), exist_ok=True)
                open(done_mark, "w").close()
                if not a.keep_tar:
                    os.remove(dest)
    print(f"done: {os.path.abspath(a.out)}")


if __name__ == "__main__":
    sys.exit(main())
