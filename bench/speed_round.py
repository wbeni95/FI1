"""Clean speed round: FreeIdea and general compressors, encode and decode, on a quiet machine.

Copies the samples to a fast work directory first, so the disk does not set the pace. Each
measurement is wall time of one process; runs under a minute are repeated (3 in all) and the
best is kept. Compressed files go to the work directory, decoded data to the null device.

  python speed_round.py --work <dir> --freeidea <exe> [--zstd <exe>] [--threads 8]
         --single <file> [<file> ...] --multi <file> [<file> ...] --out <tsv> --log <log>

--single: every compressor on one thread (xz -9e, zstd -19, gzip -9, zstd -3, FreeIdea -j 1).
--multi: zstd -19 and xz -9 with --threads, FreeIdea with --threads and with 2 x --threads.
TSV columns: file, raw bytes, compressor, threads, packed bytes, ratio, encode s, decode s,
encode MB/s, decode MB/s, encode runs, decode runs (1 MB = 10^6 bytes).
"""
import argparse, os, shutil, subprocess, sys, time

T0 = time.perf_counter()


def log(f, msg):
    line = f"{time.strftime('%H:%M:%S')} +{(time.perf_counter() - T0) / 60:5.1f} min  {msg}"
    print(line, flush=True)
    f.write(line + "\n")
    f.flush()


def run(cmd, out=None):
    t = time.perf_counter()
    with open(out, "wb") if out else open(os.devnull, "wb") as w:
        p = subprocess.run(cmd, stdout=w, stderr=subprocess.PIPE)
    dt = time.perf_counter() - t
    if p.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {p.stderr.decode(errors='replace')}")
    return dt


def best(fn, limit=60.0, n=3):
    times = [fn()]
    while len(times) < n and times[0] < limit:
        times.append(fn())
    return min(times), len(times)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--freeidea", required=True)
    ap.add_argument("--zstd", default=shutil.which("zstd") or "zstd")
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--single", nargs="*", default=[])
    ap.add_argument("--multi", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    ap.add_argument("--log", required=True)
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    lf = open(a.log, "a", encoding="utf-8")
    tsv = open(a.out, "a", encoding="utf-8")
    Z, FI, T = a.zstd, a.freeidea, a.threads
    xz, gz = shutil.which("xz"), shutil.which("gzip")
    log(lf, f"tools: freeidea={FI} zstd={Z} xz={xz} gzip={gz}; threads={T}")

    local = {}
    for f in dict.fromkeys(a.single + a.multi):
        dst = os.path.join(a.work, os.path.basename(f))
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(f):
            t = time.perf_counter()
            shutil.copyfile(f, dst)
            log(lf, f"copied {os.path.basename(f)} ({os.path.getsize(f) / 1e9:.2f} GB) in {time.perf_counter() - t:.0f} s")
        local[f] = dst

    def single(src):
        return [
            ("FreeIdea", 1, lambda o: [FI, "compress", "-j", "1", src, o], lambda o: [FI, "decompress", "-j", "1", o, "null"], False),
            ("zstd -3", 1, lambda o: [Z, "-q", "-3", "-T1", "-c", src], lambda o: [Z, "-q", "-d", "-c", o], True),
            ("gzip -9", 1, lambda o: [gz, "-9", "-c", src], lambda o: [gz, "-dc", o], True),
            ("zstd -19 --long", 1, lambda o: [Z, "-q", "-19", "--long=31", "-T1", "-c", src], lambda o: [Z, "-q", "-d", "--long=31", "-c", o], True),
            ("xz -9e", 1, lambda o: [xz, "-9e", "-T1", "-c", src], lambda o: [xz, "-dc", "-T1", o], True),
        ]

    def multi(src):
        return [
            ("FreeIdea", T, lambda o: [FI, "compress", "-j", str(T), src, o], lambda o: [FI, "decompress", "-j", str(T), o, "null"], False),
            ("FreeIdea", 2 * T, lambda o: [FI, "compress", "-j", str(2 * T), src, o], lambda o: [FI, "decompress", "-j", str(2 * T), o, "null"], False),
            ("zstd -19 --long", T, lambda o: [Z, "-q", "-19", "--long=31", f"-T{T}", "-c", src], lambda o: [Z, "-q", "-d", "--long=31", "-c", o], True),
            ("xz -9", T, lambda o: [xz, "-9", f"-T{T}", "-c", src], lambda o: [xz, "-dc", f"-T{T}", o], True),
        ]

    plan = [(f, single(local[f])) for f in a.single] + [(f, multi(local[f])) for f in a.multi]
    for f, runs in plan:
        src = local[f]
        raw = os.path.getsize(src)
        name = os.path.basename(f)
        for tool, th, enc, dec, to_stdout in runs:
            out = os.path.join(a.work, f"{name}.{tool.split()[0]}.{th}.out")
            # Compressors that write to stdout get a file; FreeIdea writes its own file.
            e, ne = best(lambda: run(enc(out), out if to_stdout else None))
            packed = os.path.getsize(out)
            d, nd = best(lambda: run(dec(out)))
            os.remove(out)
            row = [name, raw, tool, th, packed, f"{raw / packed:.3f}", f"{e:.2f}", f"{d:.2f}", f"{raw / 1e6 / e:.1f}", f"{raw / 1e6 / d:.1f}", ne, nd]
            tsv.write("\t".join(map(str, row)) + "\n")
            tsv.flush()
            log(lf, f"{name:28} {tool:16} -T{th:<2} ratio {raw / packed:7.3f}  enc {e:8.2f} s {raw / 1e6 / e:8.1f} MB/s ({ne}x)  dec {d:7.2f} s {raw / 1e6 / d:8.1f} MB/s ({nd}x)")
    log(lf, "done")


if __name__ == "__main__":
    main()
