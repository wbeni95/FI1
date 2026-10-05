# FreeIdea results

Measured 2026-10-01 on four public Nasdaq TotalView-ITCH 5.0 days. FreeIdea stores them in
**1/6.5 to 1/7.7** of their raw size: **2.1 to 2.2 times smaller than xz**, 2.4 to 2.5 times
smaller than `zstd -19 --long`, and 3.0 to 3.2 times smaller than the gzip files Nasdaq
publishes. Every run was verified byte for byte.

## Data

Raw BinaryFILE days from Nasdaq's public sample server, <https://emi.nasdaq.com/ITCH/>, unpacked
from the published `.gz` files.

| Day | Venue | File | Raw bytes | Messages |
|---|---|---|---:|---:|
| 2019-07-30 | Nasdaq BX | `20190730.BX_ITCH_50` | 837,472,908 | 28,734,686 |
| 2019-07-30 | Nasdaq PSX | `20190730.PSX_ITCH_50` | 918,015,732 | 30,467,321 |
| 2019-10-30 | Nasdaq | `10302019.NASDAQ_ITCH50` | 9,035,016,843 | 293,989,079 |
| 2025-11-28 | Nasdaq (half trading day) | `S112825-v50` | 11,269,366,583 | 353,357,889 |

## Compression ratio (raw size / compressed size; higher is better)

| Compressor | BX 2019-07-30 | PSX 2019-07-30 | Nasdaq 2019-10-30 | Nasdaq 2025-11-28 |
|---|---:|---:|---:|---:|
| Nasdaq's published `.gz` | 2.141 | 2.229 | 2.333 | 2.380 |
| `gzip -9` | 2.186 | 2.276 | | |
| `zstd -3` | 2.336 | 2.413 | | |
| `zstd -19 --long=31` | 2.747 | 2.889 | 2.985 * | 3.096 * |
| `zstd --ultra -22 --long=31` | 2.760 | 2.896 | | |
| `xz -9e` | 3.045 | 3.295 | | |
| `xz -9 -T16` | 3.037 | | 3.297 * | 3.423 * |
| **FreeIdea** (8 threads, default segments) | **6.528** | **6.877** | **7.337** | **7.659** |
| FreeIdea / best general compressor | 2.14x | 2.09x | 2.23x | 2.24x |

\* multi-threaded run (`-T16`); single-threaded `xz -9e` on the multi-GB days would take hours.
On BX, `zstd -19 -T16` gives exactly the single-threaded size and `xz -9 -T16` is within 0.3%
of `xz -9e`.

With one thread FreeIdea uses larger segments (256 MB) and is slightly smaller still: BX 6.541,
PSX 6.896; the two big days are cut into 256 MB segments at any thread count.

## Speed (clean round, measured 2026-10-02)

Measured with nothing else running on the machine (AMD Ryzen 7 9700X, 8 cores, 16 threads), the
samples copied to an NVMe SSD first so the disk does not set the pace. Wall time of each process;
runs under a minute were repeated three times and the best is kept. Decompression writes to the
null device. MB/s of raw data (1 MB = 10^6 bytes); ratio in parentheses. FreeIdea is the
evaluation build.

**One thread.** BX ITCH day (837 MB), first 400 MB of the ITTO day, first 300 MB of the IEX
capture.

| Compressor | BX ITCH: compress | decompress | ITTO: compress | decompress | IEX: compress | decompress |
|---|---:|---:|---:|---:|---:|---:|
| **FreeIdea** | **105 (6.54x)** | **123** | **46 (7.10x)** | **51** | **142 (20.94x)** | **210** |
| `zstd -3` | 388 (2.34x) | 1,320 | 389 (2.30x) | 1,280 | 688 (4.88x) | 2,120 |
| `gzip -9` | 3.3 (2.19x) | 308 | 2.1 (2.36x) | 295 | 9.7 (4.29x) | 556 |
| `zstd -19 --long=31` | 2.9 (2.75x) | 976 | 3.4 (3.07x) | 906 | 2.5 (5.88x) | 1,612 |
| `xz -9e` | 1.3 (3.05x) | 134 | 1.6 (3.58x) | 138 | 1.3 (7.32x) | 272 |

**Eight threads.** BX ITCH day (837 MB), 7.23 GB of the ITTO day, first 3.0 GB of the IEX
capture. zstd decompresses on one thread whatever `-T` says; xz decompresses its multi-block
files in parallel.

| Compressor | BX ITCH: compress | decompress | ITTO: compress | decompress | IEX: compress | decompress |
|---|---:|---:|---:|---:|---:|---:|
| **FreeIdea `-j 8`** | **517 (6.53x)** | **704** | **250 (6.16x)** | **278** | **757 (19.34x)** | **1,213** |
| FreeIdea `-j 16` | 637 (6.50x) | 883 | 369 (6.03x) | 405 | 893 (19.33x) | 1,397 |
| `zstd -19 --long=31 -T8` | 10.7 (2.75x) | 969 | 16.2 (2.92x) | 959 | 12.4 (5.81x) | 1,407 |
| `xz -9 -T8` | 7.7 (3.04x) | 494 | 14.2 (3.34x) | 830 | 14.8 (7.13x) | 1,517 |

- Compressing, FreeIdea is 13 to 58 times faster than `zstd -19` and 28 to 108 times faster than
  `xz -9e` on one thread; on eight threads it is 15 to 61 times faster than `zstd -19` and 18 to
  68 times faster than `xz -9`. Its files are 1.8 to 3.6 times smaller.
- `zstd -3` compresses 3.7 to 8.5 times faster than FreeIdea on one thread, with files 2.8 to 4.3
  times larger.
- Decompressing on one thread, FreeIdea runs at about xz speed on ITCH files; zstd is 8 to 18
  times faster per thread. On eight threads FreeIdea decodes ITCH at 704 MB/s (xz 494, zstd 969)
  and captures at 1.2 GB/s (zstd and xz 1.4 to 1.5 GB/s); options are the slowest at 278 MB/s
  (405 MB/s with 16 threads), against 830 to 959 MB/s.
- With 16 threads FreeIdea cuts files into more segments, so they are up to 2% larger.

Raw output: `speed_2026-10-02.tsv` (file, raw bytes, compressor, threads, packed bytes, ratio,
compress s, decompress s, compress MB/s, decompress MB/s, compress runs, decompress runs), made
by `speed_round.py`.

## Speed, first round (2026-10-01, shared desktop)

Superseded by the clean round above: other programs were running, so these are lower. Kept
for the record. MB/s of raw data.

| | Threads | BX | PSX | Nasdaq 2019 | Nasdaq 2025 |
|---|---:|---:|---:|---:|---:|
| FreeIdea compress | 1 | 70 | 72 | 63 | 72 |
| FreeIdea decompress | 1 | 115 | 121 | 82 | 87 |
| FreeIdea compress | 8 | 441 | 459 | 398 | 410 |
| FreeIdea decompress | 8 | 598 | 656 | 491 | 501 |
| gzip decompress (Nasdaq's `.gz`) | 1 | 298 | 286 | | |
| `zstd -19 --long` decompress | 1 | 764 | 612 | | |
| `xz -9` decompress | 1 | 119 | 109 | | |
| `zstd -19 --long` compress | 1 | 1.8 | 2.0 | | |

On BX and PSX, one FreeIdea core decompresses as fast as xz and compresses 35 to 40 times faster than
`zstd -19`; zstd decompresses 5 to 7 times faster per core. FreeIdea times are wall clock
including process start and writing the compressed file; decompression writes to a null sink.
gzip, zstd and xz decode speeds: best of 3 single-thread runs with nothing else of ours running
(`decode_speed.tsv`); zstd compress speed from `baselines_2019-07-30.tsv`.

Peak memory at 8 threads: 1.2 GB on BX (105 MB segments), 4.5 GB compressing and 3.4 GB
decompressing the Nasdaq 2019 day (256 MB segments). Memory scales with threads x segment size.

## Machine

AMD Ryzen 7 9700X (8 cores, 16 threads), 31 GB RAM, Windows 11 Pro; data on a SATA hard disk
(repeated runs read mostly from the OS file cache). FreeIdea built
with rustc 1.98.1 (`cargo build --release`), zstd 1.5.7, xz 5.8.1 and gzip 1.14 from Git for Windows. A shared desktop: other
programs used about two cores during the runs. The clean speed round ran with nothing else running.

## Reproduce

Point the scripts at the FreeIdea binary (or put it on PATH) and at zstd if it is not on PATH:

```
set FREEIDEA=C:\path\to\freeidea.exe        (Linux/macOS: export FREEIDEA=...)
python bench/freeidea_bench.py <raw files...>          # FreeIdea at 1 and 8 threads + verify
python bench/baselines.py <raw files...>               # gzip, zstd, xz single-threaded
set MT=16 & python bench/baselines.py <raw files...>   # zstd -19 and xz -9 multi-threaded
python bench/decode_speed.py <raw files...>            # clean single-thread decode speeds
powershell -File bench/peakmem.ps1 freeidea.exe compress <in> <out>
python bench/speed_round.py --work <ssd dir> --freeidea <exe> --zstd <exe> --threads 8 --single <files> --multi <files> --out <tsv> --log <log>
```

The measurements were made with the full build; the evaluation build writes byte-identical
files (checked on the BX day: 128,298,456 bytes from both).

Raw outputs: `freeidea_final.tsv`, `baselines_2019-07-30.tsv`, `baselines_mt.tsv`
(columns: file, compressor or threads, bytes, ratio, compress s, decompress s) and
`decode_speed.tsv` (file, format, decode s, MB/s). Decode times in the two baseline files were
taken while other benchmarks ran and are not used for speed claims.

## Options: Nasdaq ITTO 4.0 (measured 2026-10-02)

Nasdaq Options Market, ITCH to Trade Options 4.0, sample day 2022-04-11, partition AE
(`S041122-itto-v4-ae.txt.gz` under `emi.nasdaq.com/Options/Nasdaq Options Market/ITTO/`). The
.gz file is 33 GB; its first 3 GB were unpacked to 7.23 GB of BinaryFILE, and its first 400 MB
were used as a smaller sample.

| Compressor | first 400 MB | first 7.23 GB |
|---|---:|---:|
| `gzip -9` | 2.356 | |
| `zstd -3` | 2.295 | |
| `zstd -19 --long=31` | 3.073 | 2.920 * |
| `zstd --ultra -22 --long=31` | 3.106 | |
| `xz -9e` / `xz -9 -T16` * | 3.575 | 3.340 * |
| **FreeIdea, 1 thread** | **7.096** | **6.376** |
| **FreeIdea, 8 threads** | **7.096** | **6.156** |

\* multi-threaded run. ITTO segments default to 512 MB..2 GB, because options data
compresses better in larger segments. The 400 MB sample is one segment; the 7.23 GB file is
4 segments at 1 thread and 8 at 8 threads. Speed on the 7.23 GB file: 40 MB/s compress and
50 MB/s decompress on one thread, 170 and 250 MB/s on eight (first round; the clean round above has
the current figures).

## Packet captures (measured 2026-10-02)

Real: IEX DEEP 1.0 capture of 2026-09-30 from IEX HIST (pcapng, microsecond timestamps, one
UDP flow of IEX-TP packets): the first 3.0 GB (unpacked from the first 2 GB of the 12 GB .gz)
and its first 300 MB.

| Compressor | first 300 MB | first 3.0 GB |
|---|---:|---:|
| `gzip -9` | 4.289 | |
| `zstd -3` | 4.881 | |
| `zstd -19 --long=31` | 5.884 | 5.810 * |
| `zstd --ultra -22 --long=31` | 5.906 | |
| `xz -9e` / `xz -9 -T16` * | 7.320 | 7.134 * |
| **FreeIdea, 1 thread** | **20.940** | **19.365** |
| **FreeIdea, 8 threads** | **20.911** | **19.344** |

Speed on the 3.0 GB capture: 99 MB/s compress and 195 MB/s decompress on one thread, 714 and
1154 MB/s on eight (first round; the clean round above has the current figures).

Synthetic: MoldUDP64 captures built by our test generator from real data, with an A and a B
line: the BX day's first 120 MB as a classic pcap (microseconds), and the ITTO sample's first
120 MB as a pcapng (nanoseconds).

| Compressor | BX ITCH, A+B, 884 MB | ITTO, A+B, 696 MB |
|---|---:|---:|
| `zstd -19 --long=31 -T16` | 6.577 | 6.880 |
| `xz -9 -T16` | 7.797 | 8.408 |
| **FreeIdea, 8 threads** | **38.534** | **24.330** |

These two test the capture path end to end. The generator's packing and latency are regular,
so their ratios are optimistic; the IEX capture is the real-world figure.

Raw outputs: `freeidea_v02.tsv`, `freeidea_v02_small.tsv`, `baselines_v02_mt.tsv`,
`baselines_itto.tsv`, `baselines_iex.tsv`, `baselines_synth.tsv`. Every FreeIdea file in this
section was decompressed and compared with its original: all byte-identical.

## Linux (measured 2026-10-02)

The Linux evaluation build (one static x86-64 binary) ran on a GitHub-hosted runner, 2 vCPUs of
an AMD EPYC 7763, on the same public samples, downloaded fresh and checked by SHA-256. It wrote
**byte-identical files** to the Windows build: 128,298,456 bytes for the BX day, 56,372,367 for
the first 400 MB of the ITTO day and 14,346,849 for the first 300 MB of the IEX capture (8
threads each). Every file was verified byte for byte.

| Decompress, MB/s of raw data | 1 vCPU | 2 vCPUs |
|---|---:|---:|
| Nasdaq BX ITCH day | 68 | 93 |
| ITTO, first 400 MB (one segment) | 33 | 33 |
| IEX capture, first 300 MB | 136 | 142 |

A shared cloud vCPU is slower than a desktop core; the speeds above this section are from the
Ryzen 7 9700X.

## Version 0.2.1 (measured 2026-10-02)

0.2.1 writes byte-identical files to 0.2.0 (compared byte for byte on the BX day, the 2019
Nasdaq day, the ITTO samples of 20 MB, 400 MB and 7.23 GB and the IEX samples of 30 MB, 300 MB
and 3.0 GB). It adds a note on input that is not a supported feed, stores segments that would
not get smaller, keeps a run within free memory and reads standard input.

**Memory.** At most threads + 2 segments are held at once. Peaks at 8 threads, samples on an
NVMe SSD:

| File | Segment | Compress | Decompress |
|---|---:|---:|---:|
| Nasdaq ITCH 2019-10-30, 9.0 GB | 256 MB | 3.7 GB | 3.3 GB |
| IEX capture, 3.0 GB | 375 MB | 3.7 GB | 3.5 GB |
| ITTO, 7.23 GB | 904 MB | 10.9 GB | 12.0 GB |

On a cloud runner limited to 2 GB, compressing the BX day without `-j` used 1 thread instead
of 2 and wrote the same file; limited to 1 GB it used 1 thread and 138 MB segments and
finished (6.537x instead of 6.541x); decompressing under 1 GB used 1 thread.

**Linux ARM64.** The ARM64 build ran on a GitHub-hosted Arm runner (2 vCPUs) on the same
samples and wrote byte-identical files to the x86-64 builds: BX day 128,298,456 bytes, ITTO
400 MB 56,372,367, IEX 300 MB 14,346,849, all verified.

| Decompress, MB/s of raw data, 1 vCPU | Linux ARM64 | Linux x86-64 |
|---|---:|---:|
| Nasdaq BX ITCH day | 77 | 82 |
| ITTO, first 400 MB | 28 | 45 |
| IEX capture, first 300 MB | 148 | 160 |

Both are shared cloud runners of 2 vCPUs; the speeds above this section are from the Ryzen.

## OPRA Pillar captures (version 0.3.0, measured 2026-10-02)

A free public OPRA Pillar PCAP sample from a leading market-data vendor: 10 minutes, A side only, the four
lines of one underlying. Unpacked: 12.08 GB, 81.5 million packets, 184.6 million messages, 7,576 series; classic pcap with
microsecond stamps and VLAN-tagged Ethernet.

| Compressor | first 100 MB | first 1 GB | all 12.08 GB |
|---|---:|---:|---:|
| `zstd -3` | 3.081 | 3.152 | |
| `zstd -19 --long=31 -T8` | 4.059 | 4.131 | |
| `xz -9 -T8` | 4.733 | 4.858 | |
| **FreeIdea 0.3.0, 8 threads** | **10.390** | **10.872** | **10.880** |

Every FreeIdea file was decompressed and compared with its original: all byte-identical. On the
12.08 GB file (12 segments, data on a hard disk): 138 s to compress, 91 s to decompress and
compare. Peak memory on the 1 GB slice at 8 threads: 0.92 GB compressing, 1.29 GB
decompressing.

This sample is one underlying on four lines. A full OPRA capture has 96 lines with many
underlyings each, and both sides; it is not measured yet. Capture files from 0.3.0 use capture
format 4, which 0.2.x cannot read; 0.3.0 reads every earlier file.

## Version 0.4.0 (measured 2026-10-02)

New: NYSE XDP and Cboe PITCH captures. Capture files are written in capture format 5, which
0.3.x cannot read; 0.4.0 reads every earlier file (checked against files written by 0.2.1 and
0.3.0). ITCH and ITTO files are byte-identical to 0.3.0's (BX day 128,298,456 bytes, ITTO 400 MB
56,372,367). Other captures got slightly smaller; 8 threads, every file verified:

| Capture | 0.3.0 | **0.4.0** |
|---|---:|---:|
| IEX DEEP, first 300 MB | 20.911 | **20.974** |
| IEX DEEP, first 3.0 GB | 19.344 | **19.389** |
| OPRA, four lines of one underlying, first 1 GB | 10.872 | **10.879** |
| OPRA, four lines of one underlying, all 12.08 GB | 10.880 | **10.888** |

### Cboe PITCH captures

A free public PCAP sample of one Cboe US equities exchange from a leading market-data vendor: 10 minutes from
the 09:30 ET open, A side. Unpacked: 1.159 GB, classic pcap with nanosecond stamps and VLAN-tagged Ethernet, 12,425,340
packets on 70 multicast flows (35 units), 14,290,032 messages: 6.49 M short adds, 6.14 M
deletes, 1.22 M short modifies, 0.14 M executions, 0.12 M short reductions, 66 k long adds,
46 k short trades and others.

| Compressor | all 1.159 GB |
|---|---:|
| `zstd -3` | 2.895 |
| `zstd -19 --long=31 -T8` | 3.789 |
| `xz -9 -T8` | 4.261 |
| **FreeIdea, 8 threads** | **13.392** |

Decompressed byte-identical. Eight threads, samples on the NVMe SSD: 4.2 s to compress, 3.5 s
to decompress. Other Cboe exchanges, Cboe options and B-side copies are not measured yet.

### NYSE XDP captures

There is no free binary XDP capture, so one was rebuilt from NYSE's own record of the feed: the
TAQ NYSE Integrated Feed file of channel 1, 2026-07-01 (`EQY_US_NYSE_IBF_1_20260701.gz` from
NYSE's public FTP, 239.8 MB as distributed), one CSV line per message in feed order. Each line
was turned back into its binary XDP message: 13,364,835 messages from 00:28 to 16:45 ET on 325
symbols, plus 33,909 source time references where TAQ skips sequence numbers.

What is real: every message's type, time, symbol, symbol sequence number, order id, price,
size, side, firm and trade id. What is generated: symbol index numbers and price scales, two
fields TAQ does not carry (set to 0), and the packet layer: grouping (11,127,819 packets),
send and capture times, one Ethernet/IPv4/UDP flow, A side only. Two packet timings:

- noisy: send delay 10 to 30 us after the packet's last message and capture delay 1 to 2 us,
  uniformly random (about 24 bits of pure noise per packet);
- regular: no random delay at all.

| Compressor | noisy (1.262 GB) | regular (1.262 GB) |
|---|---:|---:|
| `zstd -3` | 3.381 | 3.381 |
| `zstd -19 --long=31 -T8` | 3.902 | 3.900 |
| `xz -9 -T8` | 4.482 | 4.498 |
| **FreeIdea, 8 threads** | **13.419** | **21.345** |

Both FreeIdea files decompressed byte-identical; eight threads: 2.7 s and 2.4 s to compress,
2.3 s and 2.2 s to decompress. A real capture's timing should lie between the two. For scale:
NYSE distributes the same day as gzipped CSV in 239.8 MB; FreeIdea keeps the binary capture in
94.1 MB (noisy) or 59.1 MB (regular).

