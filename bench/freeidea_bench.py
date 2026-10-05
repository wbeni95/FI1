"""FreeIdea on raw ITCH files: size, ratio, encode and decode wall time at 1 and 8 threads,
and a byte-for-byte verify.

Usage: python freeidea_bench.py <raw_itch_file> [<raw_itch_file> ...]
Prints one tab-separated line per (file, threads), flushed as each run ends:
file, threads, packed bytes, ratio, encode s, decode s, verified
"""
import os, re, subprocess, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_LOCAL = os.path.join(ROOT, "target", "release", "freeidea.exe" if os.name == "nt" else "freeidea")
# FreeIdea binary: $FREEIDEA, else a local release build, else freeidea on PATH.
EXE = os.environ.get("FREEIDEA") or (_LOCAL if os.path.exists(_LOCAL) else "freeidea")


def timed(args):
    t0 = time.perf_counter()
    out = subprocess.run(args, check=True, capture_output=True, text=True)
    return time.perf_counter() - t0, out.stdout + out.stderr


def main():
    threads = [int(x) for x in os.environ.get("THREADS", "1,8").split(",")]
    for f in sys.argv[1:]:
        orig = os.path.getsize(f)
        packed = f + ".fi"
        for j in threads:
            enc_s, _ = timed([EXE, "compress", "-j", str(j), f, packed])
            size = os.path.getsize(packed)
            dec_s, _ = timed([EXE, "decompress", "-j", str(j), packed, "null"])
            _, ver = timed([EXE, "verify", "-j", str(j), f, packed])
            ok = "verify ok" in ver
            print(f"{os.path.basename(f)}\t{j}\t{size}\t{orig / size:.3f}\t{enc_s:.1f}\t{dec_s:.1f}\t{ok}", flush=True)
        os.remove(packed)


if __name__ == "__main__":
    main()
