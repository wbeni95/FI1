# FreeIdea

Lossless compression for exchange market data: packet captures, equities and options feeds.
Every byte comes back exactly.

**On real data** (public samples, every file verified byte for byte):

| Data | Size with FreeIdea | Smaller than xz |
|---|---:|---:|
| IEX DEEP packet capture | **1/19 to 1/21** | **2.7 to 2.9x** |
| Cboe PITCH packet capture | **1/13.4** | **3.1x** |
| OPRA Pillar packet capture | **1/10.9** | **2.2x** |
| Nasdaq ITCH 5.0 equities files | **1/6.5 to 1/7.7** | **2.1 to 2.2x** |
| Nasdaq ITTO 4.0 options files | **1/6.2 to 1/7.1** | **1.8 to 2.0x** |

NYSE XDP: 1/13.4 to 1/21.3 on a capture rebuilt from NYSE's own record of the feed (real
messages, generated packet timing; [details](#nyse-xdp-and-cboe-pitch)).

**Why it matters**

- **Storage.** Per petabyte of captures, per copy and year, about **$30,000 less** on S3
  Standard than with `zstd -19` ([What it saves](#what-it-saves)).
- **A and B lines.** A B-line packet is stored as a reference to its A-line copy: a few bits
  instead of the whole packet again. On synthetic A+B captures built from real Nasdaq data:
  **38.5x**, against 7.8x with xz. A real A+B capture is not measured yet.
- **Speed.** Compresses **15 to 60 times faster** than `zstd -19` on eight threads, and
  decompresses captures at **1.2 GB/s** on eight threads, straight into replay tools.

**Try it on your own data:** ask for an evaluation build, [below](#try-it). Evaluation is free
for 90 days per organisation, and non-commercial use is free; business use needs a license
([Licensing](#licensing)). The source code is not public. [Status](#status) says what is
measured on real data and what is not yet.

## Results on real data

Ratio = raw size / compressed size; FreeIdea with 8 threads and default segments. Every
FreeIdea file was decompressed and compared with its original: all byte-identical.

| Data | Raw | `zstd -19 --long` | xz | **FreeIdea** | vs xz |
|---|---:|---:|---:|---:|---:|
| IEX DEEP capture (pcapng), 2026-09-30, first 300 MB | 0.3 GB | 5.88 | 7.32 | **20.97** | 2.9x |
| IEX DEEP capture (pcapng), 2026-09-30, first 3 GB | 3.0 GB | 5.81 | 7.13 | **19.39** | 2.7x |
| Cboe PITCH capture (pcap), one US equities exchange, 10 minutes from the open | 1.16 GB | 3.79 | 4.26 | **13.39** | 3.1x |
| OPRA Pillar capture (pcap), four lines of one underlying, first 1 GB | 1.0 GB | 4.13 | 4.86 | **10.88** | 2.2x |
| OPRA Pillar capture (pcap), four lines of one underlying, 10 minutes | 12.1 GB | | | **10.89** | |
| Nasdaq ITCH, 2025-11-28 | 11.3 GB | 3.10 | 3.42 | **7.66** | 2.2x |
| Nasdaq ITCH, 2019-10-30 | 9.0 GB | 2.99 | 3.30 | **7.34** | 2.2x |
| Nasdaq PSX ITCH, 2019-07-30 | 0.9 GB | 2.89 | 3.30 | **6.88** | 2.1x |
| Nasdaq BX ITCH, 2019-07-30 | 0.8 GB | 2.75 | 3.05 | **6.53** | 2.1x |
| Nasdaq Options ITTO 4.0, 2022-04-11, first 400 MB | 0.4 GB | 3.07 | 3.58 | **7.10** | 2.0x |
| Nasdaq Options ITTO 4.0, 2022-04-11, first 7.2 GB | 7.2 GB | 2.92 | 3.34 | **6.16** | 1.8x |

FreeIdea 0.4.0. Sources: IEX HIST, Nasdaq's public samples (`emi.nasdaq.com`) and the free
public PCAP samples of a leading market-data vendor (OPRA and Cboe). [RESULTS.md](RESULTS.md) has every number,
the speeds, memory, the machine and the commands.

## What it saves

Per petabyte of raw data, one copy, one year on AWS S3 Standard at list price, compared with
`zstd -19`: **$30,300 on packet captures, $50,100 on equities files and $45,400 on options
files**. The storage bill drops by 53 to 70%, and every extra copy and every delivery saves
again. [SAVINGS.md](SAVINGS.md) covers delivery, transfer time and compute cost, with a
calculator for your own volumes and prices (`savings.py`).

## Speed

Smaller files and faster compression at once: compared with `zstd -19` and `xz`, FreeIdea makes
files 1.8 to 3.6 times smaller and compresses **13 to 108 times faster on one thread, 15 to 68
times faster on eight**. Measured on a quiet machine (AMD Ryzen 7 9700X, 8 cores), MB/s of raw
data:

| Data | Compressor | Compress, 1 thread | Compress, 8 threads | Decompress, 1 thread | Decompress, 8 threads |
|---|---|---:|---:|---:|---:|
| Packet captures (IEX DEEP) | **FreeIdea** | **142** | **757** | **210** | **1,213** |
| | `zstd -19 --long` | 2.5 | 12.4 | 1,612 | 1,407 |
| | `xz -9e` / `xz -9 -T8` | 1.3 | 14.8 | 272 | 1,517 |
| Equities (Nasdaq BX ITCH) | **FreeIdea** | **105** | **517** | **123** | **704** |
| | `zstd -19 --long` | 2.9 | 10.7 | 976 | 969 |
| | `xz -9e` / `xz -9 -T8` | 1.3 | 7.7 | 134 | 494 |
| Options (Nasdaq ITTO 4.0) | **FreeIdea** | **46** | **250** | **51** | **278** |
| | `zstd -19 --long` | 3.4 | 16.2 | 906 | 959 |
| | `xz -9e` / `xz -9 -T8` | 1.6 | 14.2 | 138 | 830 |

One-thread runs use the first 300 MB of the capture, the BX day and the first 400 MB of the
options day; eight-thread runs use 3.0 GB of the capture, the BX day and 7.23 GB of the options
day. Decompressing, zstd is faster per thread (8 to 18 times); fast settings such as `zstd -3`
compress 3.7 to 8.5 times faster than FreeIdea, with files 2.8 to 4.3 times larger. Full tables
with gzip and `zstd -3`: [RESULTS.md](RESULTS.md).

- **Compute.** Compressing a petabyte of captures takes about 370 machine-hours with FreeIdea
  against 22,400 with `zstd -19`: about $160 against $9,650 on an AWS c8a.2xlarge, 98% less.
- **Download and decompress.** On links up to about 3.5 Gbit/s, fetching and decompressing a
  FreeIdea capture finishes first, even against `zstd -3`: 124 s for 100 GB of raw capture at
  1 Gbit/s, against 178 to 211 s with xz and zstd. On a fully used 10 Gbit/s link the faster
  decompressors win. Details in [SAVINGS.md](SAVINGS.md).

## Packet captures (pcap, pcapng)

FreeIdea reads captures down to the packet: Ethernet, VLAN, IPv4 and UDP headers, MoldUDP64
(Nasdaq ITCH and ITTO), IEX-TP (IEX DEEP), OPRA Pillar, NYSE XDP and Cboe PITCH packets, and the
messages inside them. Other traffic in the capture is kept exactly and compressed as ordinary
data.

- **Near-zero-cost A/B line deduplication.** Many firms record both the A and the B line of a
  feed, which doubles the archive. FreeIdea stores a B-line packet as a reference to its A-line
  copy plus its own timestamp, instead of the whole packet again: a few bits per packet in our
  tests on synthetic A+B captures; we have not yet measured a real one.
- **Fast replay.** The 3 GB IEX capture decompresses at 1.21 GB/s on 8 threads (about
  9.7 Gbit/s) and 1.40 GB/s on 16, straight into existing replay tools (`decompress ... -`
  writes to stdout).
- **Capture appliances compress for the write path.** Some compress as they capture; FreeIdea
  is built for the archive behind them.

On synthetic A+B captures built from the real Nasdaq ITCH data above, FreeIdea reaches 38.5x
(xz: 7.8x) thanks to the deduplicated B line. The timing in these synthetic captures is more
regular than on a real network, so real A+B captures will land lower; we welcome one in a pilot.

## NYSE XDP and Cboe PITCH

**Cboe PITCH.** A free public sample of one Cboe US equities exchange from a leading market-data vendor (10
minutes from the open, A side, 35 units, 14.3 million messages, 1.16 GB) compresses 13.4 times:
3.1 times smaller than xz and 3.5 times smaller than `zstd -19`, every byte verified. Eight
threads compress it in 4.2 s and decompress it in 3.5 s. The other Cboe exchanges, Cboe options
and B-side copies are not measured yet.

**NYSE XDP.** There is no free binary XDP capture, so we rebuilt one from NYSE's own record of
the feed: the TAQ NYSE Integrated Feed file of one channel for a full day (2026-07-01, 13.4
million messages, 1.26 GB as a capture). Every message is real; the packets around them
(grouping, send and capture times, network headers) are generated. Because a real capture's
packet timing is unknown, we measured two extremes:

| NYSE XDP channel 1, full day, 1.26 GB | `zstd -19 --long` | xz | **FreeIdea** | vs xz |
|---|---:|---:|---:|---:|
| noisy packet timing (random delays) | 3.90 | 4.48 | **13.42** | 3.0x |
| regular packet timing | 3.90 | 4.50 | **21.35** | 4.7x |

A real XDP capture should land between the two; we welcome one in a pilot.

## Options data (OPRA and Nasdaq ITTO 4.0)

**OPRA.** Captures of the OPRA Pillar feed compress 10.9 times, 2.2 times smaller than xz and
2.6 times smaller than `zstd -19`: measured on a free 10-minute sample from a leading market-data vendor, four
lines of one underlying on the A side (12.1 GB, 184.6 million messages), every byte verified. A full OPRA capture
(96 lines, many underlyings per line, both sides) is not measured yet.

**Nasdaq ITTO 4.0.** ITCH to Trade Options files compress 6.2 to 7.1 times, 1.8 to 2.0 times
smaller than xz, with quotes, quote replaces and executions all kept exactly. They decompress at
278 MB/s on eight threads (the 7.23 GB file in 26 s), plenty for end-of-day files, archives and
vendor deliveries.

Other options or futures feeds are available as a custom integration under an enterprise
license.

## Try it

**1. Ask for an evaluation build.** Copy this into a mail and fill in the three lines:

```text
To: benjaminweisz.dev@gmail.com
Subject: Evaluation build request

Organisation: <your organisation>
Name: <your name>
Data: <what you would like to test, e.g. OPRA captures or ITCH files>
```

You get a download link to a build made for your organisation, for Windows x86-64, Linux x86-64
and Linux ARM64, usually within the hour.

**2. Unpack it and check the download:** [EVALUATION.md, Install](EVALUATION.md#install).

**3. Run it:**

```
freeidea compress   capture.pcapng capture.fi    # any supported input; the type is recognised
freeidea verify     capture.pcapng capture.fi    # decodes and compares byte for byte
freeidea decompress capture.fi capture.pcapng    # or "-" for stdout, "null" to discard
freeidea stats      20190730.BX_ITCH_50          # bits spent per field and message type
freeidea version                                 # version, organisation, last day it compresses
freeidea help                                    # the commands and options

aws s3 cp s3://bucket/day.fi - | freeidea decompress - - | your_replay   # "-" works both ways
```

Options: `-j <threads>` (default: cores, at most 8; fewer when free memory is short),
`--segment-mb <MB>`, `--feed itch|itto|pcap` (default: recognised from the input).

[EVALUATION.md](EVALUATION.md) is a step-by-step guide for a two-week test on your own data,
from unpacking and checking the download to the numbers we ask back; nothing needs to leave
your machines.

Public test data: IEX HIST for captures, <https://emi.nasdaq.com/ITCH/> and
<https://emi.nasdaq.com/Options/> for Nasdaq files (unpack the `.gz` files first).

## Inputs

- Packet captures, pcap and pcapng: MoldUDP64 packets carrying ITCH or ITTO, IEX-TP packets
  carrying IEX DEEP, OPRA Pillar blocks, NYSE XDP packets (Integrated Feed and the control
  messages all XDP feeds share) and Cboe PITCH 2.x packets; any other traffic is kept as it is.
- Nasdaq TotalView-ITCH 5.0 files (BinaryFILE framing), also BX and PSX ITCH.
- Nasdaq ITCH to Trade Options (ITTO) 4.0 files.

## The evaluation build

- Free for evaluation (companies included, up to 90 days per organisation) and non-commercial use.
- Made for your organisation on request. It compresses for 90 days, the evaluation period,
  then stops compressing. For non-commercial use, ask for a new build when it runs out.
- Decompress and verify never expire, so files made with it stay readable.
- Your part: keep your originals until `freeidea verify` confirms the compressed file, test
  it on your own data before relying on it, and keep a copy of the build you used
  ([LICENSE.txt](LICENSE.txt), section 6).
- Prints a one-line notice on every run: your organisation, the last day it compresses and
  the license contact.
- Windows on x86-64, Linux on x86-64 and on ARM64 (AWS Graviton and other Arm servers). Each
  Linux build is one static binary with no dependencies.

## Guarantees

- **Lossless for any input.** Messages, packets and blocks it does not recognise, wrong
  lengths and a cut trailing record go through a fallback path and come back byte for byte.
- **Never grows by more than a few bytes.** A segment that would not get smaller is stored as
  it is.
- **Fits the machine.** Without `-j`, it uses fewer threads when a run would not fit in free
  memory, and writes the same file.
- **Damage is detected.** Each segment carries its size and a 64-bit checksum; a flipped bit or a
  truncated file is an error, never silently wrong output.
- **One file, no dependencies.**

## Status

What this release can show today, as it stands:

- **Measured on real data, every file verified byte for byte:** four public Nasdaq
  TotalView-ITCH 5.0 days (BX and PSX of 2019-07-30, the whole Nasdaq days of 2019-10-30 and
  2025-11-28, the last a half trading day of 11.3 GB), the first 7.23 GB
  of a public Nasdaq ITTO 4.0 options day, the first 3 GB of a real IEX DEEP capture, a
  10-minute OPRA Pillar capture of four lines of one underlying, A side (12.1 GB), and a
  10-minute Cboe PITCH capture of one US equities exchange at the open, A side (1.16 GB), both
  free public samples from a leading market-data vendor.
- **Built and tested, not yet measured on a real capture:** Nasdaq ITCH and ITTO over
  MoldUDP64 in pcap/pcapng captures, and A/B line deduplication. Our tests use captures we
  built from the real Nasdaq files, whose timing and packing are more regular than a real
  network's, so their ratios (24x to 39x) are optimistic. Capture devices differ in how they
  frame and stamp packets; what FreeIdea does not recognise is kept exactly but compresses
  poorly. A sample of your captures, or your evaluation, tells us how it goes. Likewise a full
  OPRA capture (96 lines, many underlyings per line) and A+B OPRA captures are not measured
  yet.
- **NYSE XDP is measured on real messages in a generated capture** (see
  [above](#nyse-xdp-and-cboe-pitch)); a real XDP capture is not measured yet. Cboe PITCH is
  measured on one exchange, A side, 10 minutes.
- **Not supported yet:** CME MDP 3.0, the SIP feeds (CTA CQS/CTS, UTP UQDF/UTDF) and IEX TOPS
  (in captures they are kept as raw traffic). Custom integration on request.
- **File compatibility:** 0.4.0 reads every file written by earlier versions; capture files
  written by 0.4.0 need 0.4.0 or later.
- **Data that is not a supported feed** compresses poorly, worse than zstd; `compress` says so
  when it is more than 30% of the input.
- **Decoding is slower per thread than zstd's:** 210 MB/s on the IEX capture, 123 MB/s on ITCH
  files (about xz speed) and 51 MB/s on ITTO. Segments decode in parallel, at 278 MB/s to
  1.21 GB/s on eight threads. FreeIdea is a high-compression archive tier: archives,
  end-of-day files, deliveries and research replay, not a hot real-time path.
- **Platforms tested:** Windows 11 x86-64 (AMD Ryzen 7 9700X), Linux x86-64 and Linux ARM64
  (GitHub-hosted cloud runners). No macOS build yet.

## Trademarks

Nasdaq, NYSE, Cboe, IEX, OPRA, CME and the other names of exchanges, feeds, products and
services in this repository belong to their owners. They are used only to say which data
formats FreeIdea reads, where public test data comes from and which tools it was compared
with. FreeIdea is not affiliated with, sponsored or endorsed by any of them.

## Licensing

- **Free:** evaluation by anyone, companies included, for up to 90 days per organisation, and
  non-commercial use (personal use, teaching, research at schools, universities and
  non-profits).
- **Business use needs an individual license agreement:** running FreeIdea in the operations
  of a business, such as storing, processing, serving or delivering data for business
  purposes, in production, or in a product or service. Tell us who would use it, for what,
  where and on how much data; we agree a license case by case.
- **Source code where needed, under strict confidentiality:** it may not be passed on or
  copied beyond the licensed use, and neither it nor what was learned from it may be used to
  build a competing product, also for five years after the license ends.

Full terms: [LICENSE.txt](LICENSE.txt). Commercial license: Benjamin Weisz,
benjaminweisz.dev@gmail.com.
