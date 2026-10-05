"""Single-thread decode speed of gzip, zstd and xz on raw ITCH files (no other load).

Compresses with zstd -19 --long -T16 and xz -9 -T16 (fast to make; decode speed does not
depend on the level much), then times single-thread decoding to a null sink, best of 3.
Nasdaq's published .gz next to the raw file is timed as well.

Usage: python decode_speed.py <raw_itch_file> [...]
Prints: file, format, decode s, MB/s
"""
import os, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_LOCAL_ZSTD = os.path.join(ROOT, "tools", "zstd", "zstd-v1.5.7-win64", "zstd.exe")
# zstd binary: $ZSTD, else the copy in our tools folder, else zstd on PATH.
ZSTD = os.environ.get("ZSTD") or (_LOCAL_ZSTD if os.path.exists(_LOCAL_ZSTD) else "zstd")


def best_of(args, n=3):
    best = 1e9
    for _ in range(n):
        t0 = time.perf_counter()
        subprocess.run(args, stdout=subprocess.DEVNULL, check=True)
        best = min(best, time.perf_counter() - t0)
    return best


def main():
    for f in sys.argv[1:]:
        mb = os.path.getsize(f) / 1e6
        tmp = f"{f}.{os.getpid()}"
        runs = []
        if os.path.exists(f + ".gz"):
            runs.append(("gzip (Nasdaq .gz)", ["gzip", "-dc", f + ".gz"]))
        with open(tmp + ".zst", "wb") as w:
            subprocess.run([ZSTD, "-q", "-19", "--long=31", "-T16", "-c", f], stdout=w, check=True)
        runs.append(("zstd -19 --long", [ZSTD, "-q", "-d", "--long=31", "-T1", "-c", tmp + ".zst"]))
        with open(tmp + ".xz", "wb") as w:
            subprocess.run(["xz", "-9", "-T16", "-c", f], stdout=w, check=True)
        runs.append(("xz -9", ["xz", "-dc", "-T1", tmp + ".xz"]))
        for name, args in runs:
            s = best_of(args)
            print(f"{os.path.basename(f)}\t{name}\t{s:.2f}\t{mb / s:.0f}", flush=True)
        os.remove(tmp + ".zst")
        os.remove(tmp + ".xz")


if __name__ == "__main__":
    main()
