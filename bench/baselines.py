"""Baseline compressors on one raw ITCH file: size, ratio, single-thread encode and decode wall time.

Usage: python baselines.py <raw_itch_file> [<raw_itch_file> ...]
Set MT=<threads> for the multi-threaded zstd/xz variants used on multi-GB days.
Prints one line per (file, compressor), flushed as each run ends:
file, compressor, packed bytes, ratio, encode s, decode s
"""
import os, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LOCAL_ZSTD = os.path.join(ROOT, "tools", "zstd", "zstd-v1.5.7-win64", "zstd.exe")
# zstd binary: $ZSTD, else the copy in our tools folder, else zstd on PATH.
ZSTD = os.environ.get("ZSTD") or (_LOCAL_ZSTD if os.path.exists(_LOCAL_ZSTD) else "zstd")

RUNS = [
    ("gzip -9", lambda f, o: ["gzip", "-9", "-c", f], lambda o: ["gzip", "-dc", o]),
    ("zstd -3", lambda f, o: [ZSTD, "-q", "-3", "-T1", "-c", f], lambda o: [ZSTD, "-q", "-d", "-c", o]),
    ("zstd -19 --long", lambda f, o: [ZSTD, "-q", "-19", "--long=31", "-T1", "-c", f], lambda o: [ZSTD, "-q", "-d", "--long=31", "-c", o]),
    ("zstd -22 --ultra --long", lambda f, o: [ZSTD, "-q", "--ultra", "-22", "--long=31", "-T1", "-c", f], lambda o: [ZSTD, "-q", "-d", "--long=31", "-c", o]),
    ("xz -9e", lambda f, o: ["xz", "-9e", "-T1", "-c", f], lambda o: ["xz", "-dc", o]),
]


# Multi-threaded variants for multi-GB days (single-thread xz -9e would take hours there).
MT = int(os.environ.get("MT", "0"))
if MT:
    RUNS = [
        (f"zstd -19 --long -T{MT}", lambda f, o: [ZSTD, "-q", "-19", "--long=31", f"-T{MT}", "-c", f], lambda o: [ZSTD, "-q", "-d", "--long=31", "-c", o]),
        (f"xz -9 -T{MT}", lambda f, o: ["xz", "-9", f"-T{MT}", "-c", f], lambda o: ["xz", "-dc", f"-T{MT}", o]),
    ]


def main():
    only = os.environ.get("ONLY")
    for f in sys.argv[1:]:
        orig = os.path.getsize(f)
        for k, (name, enc, dec) in enumerate(RUNS):
            out = f"{f}.{os.getpid()}.{k}.baseline"  # unique: runs may overlap
            if only and only not in name:
                continue
            t0 = time.perf_counter()
            with open(out, "wb") as w:
                subprocess.run(enc(f, out), stdout=w, check=True)
            t1 = time.perf_counter()
            size = os.path.getsize(out)
            subprocess.run(dec(out), stdout=subprocess.DEVNULL, check=True)
            t2 = time.perf_counter()
            print(f"{os.path.basename(f)}\t{name}\t{size}\t{orig / size:.3f}\t{t1 - t0:.1f}\t{t2 - t1:.1f}", flush=True)
            os.remove(out)


if __name__ == "__main__":
    main()
