# What FreeIdea saves

Storage, delivery and transfer bills grow with bytes. Measured on public data, FreeIdea stores
the same market data, bit for bit, in a fraction of the bytes that `zstd -19` needs:

| Data | FreeIdea stores, compared with zstd -19 | compared with xz | Storage bill cut vs zstd -19 |
|---|---:|---:|---:|
| Packet captures (IEX DEEP, pcapng) | 30% of the bytes | 37% | **70%** |
| Equities files (Nasdaq TotalView-ITCH 5.0) | 41% | 45% | **59%** |
| Options files (Nasdaq ITTO 4.0) | 47% | 54% | **53%** |

Measured ratios: captures 19.34x (zstd -19: 5.81x, xz: 7.13x) on the first 3.0 GB of the IEX
DEEP capture of 2026-09-30; equities 7.34x (2.98x, 3.30x) on the full Nasdaq day 2019-10-30;
options 6.16x (2.92x, 3.34x) on 7.23 GB of the Nasdaq ITTO day 2022-04-11. FreeIdea with 8
threads; [RESULTS.md](RESULTS.md) has every run.

## Storage: per petabyte of raw data, one copy, one year

AWS S3 list prices, US East (AWS price list of 2026-09-28): Standard $0.021, Standard-Infrequent
Access $0.0125, Glacier Instant Retrieval $0.004 per GB-month.

| Data | Stored with zstd -19 | Stored with FreeIdea | Saved, S3 Standard | Standard-IA | Glacier IR |
|---|---:|---:|---:|---:|---:|
| Packet captures | 172 TB | 52 TB | **$30,300** | $18,100 | $5,800 |
| Equities (ITCH) | 335 TB | 136 TB | **$50,100** | $29,800 | $9,500 |
| Options (ITTO) | 342 TB | 162 TB | **$45,400** | $27,000 | $8,600 |

The saving multiplies with every copy kept: production, disaster recovery, research clusters,
other regions. Three copies of one petabyte of raw captures save $91,000 a year on S3 Standard.

At archive scale, for captures on S3 Standard, one copy:

| Raw captures kept | Saved per year vs zstd -19 |
|---:|---:|
| 100 TB | $3,000 |
| 1 PB | $30,300 |
| 10 PB | $303,000 |
| An archive of 6 PB of zstd-compressed captures (about 35 PB raw) | **$1.06 million** (6 PB becomes 1.8 PB) |

The last row assumes the archive compresses like our IEX sample, at the zstd -19 level; the
evaluation build measures it on your data.

## Delivery: per petabyte of raw data sent out

Data sold or shared leaves storage again and again: client downloads, other regions, other
sites. At S3's rate for data sent to the internet above 150 TB a month ($0.05 per GB):

| Data | zstd -19 | FreeIdea | Saved per PB delivered |
|---|---:|---:|---:|
| Packet captures | $8,600 | $2,600 | **$6,000** |
| Equities (ITCH) | $16,800 | $6,800 | **$9,900** |
| Options (ITTO) | $17,100 | $8,100 | **$9,000** |

## Time: moving and replaying

One petabyte of raw data over a fully used 10 Gbit/s link:

| Data | Raw | zstd -19 | FreeIdea |
|---|---:|---:|---:|
| Packet captures | 9.3 days | 38 hours | **11.5 hours** |
| Equities (ITCH) | 9.3 days | 74 hours | **30 hours** |
| Options (ITTO) | 9.3 days | 76 hours | **36 hours** |

### Download and decompress

Delivered data is downloaded first, then decompressed. For 100 GB of raw capture (IEX DEEP),
download time plus decompression time at the measured speeds (FreeIdea and xz on eight threads,
zstd on its one decompression thread):

| Link, fully used | Raw | zstd -3 | zstd -19 | xz -9 | FreeIdea |
|---|---:|---:|---:|---:|---:|
| 1 Gbit/s | 800 s | 211 s | 209 s | 178 s | **124 s** |
| 10 Gbit/s | 80 s | **64 s** | 85 s | 77 s | 87 s |

Below about 3.5 Gbit/s (internet delivery, cross-region copies, most client downloads)
FreeIdea finishes first, even against `zstd -3`: the download shrinks more than the
decompression grows. On a fully used 10 Gbit/s link the faster decompressors win.

Replay from storage reads fewer bytes: decompressing the IEX capture at 1,213 MB/s of raw data
on 8 threads reads 63 MB/s from disk or network; zstd -19 at the same raw rate reads 209 MB/s.
A shared 1 Gbit/s link feeds FreeIdea's full 8-thread replay speed.

## What it costs in compute

Less than the general compressors it replaces. Compressing one petabyte of raw data on one
8-core machine at the speeds measured on eight threads ([RESULTS.md](RESULTS.md)), priced at an
AWS c8a.2xlarge on demand: $0.431 an hour in US East (AWS price list of 2026-09-25), 8 AMD EPYC
cores of the same Zen 5 design as our test machine.

| Data | FreeIdea | zstd -19 --long | xz -9 | Less compute than zstd -19 |
|---|---:|---:|---:|---:|
| Packet captures | **370 h, $160** | 22,400 h, $9,650 | 18,800 h, $8,090 | **98%** |
| Equities (ITCH) | **540 h, $230** | 26,100 h, $11,230 | 36,300 h, $15,650 | **98%** |
| Options (ITTO) | **1,110 h, $480** | 17,200 h, $7,410 | 19,500 h, $8,420 | **94%** |

Cloud cores run at a lower clock than our desktop (at most 4.5 GHz against 5.5 GHz), so expect
somewhat more hours for every compressor; the proportions hold. Against the fast `zstd -3`,
FreeIdea costs $80 to $290 more compute per petabyte (measured on one thread), once, and saves
$39,000 to $69,000 a year of S3 Standard storage per copy.

Decompression is where FreeIdea pays: on one thread it runs at 210 MB/s on captures, 123 MB/s on
equities files and 51 MB/s on options files, while zstd decompresses 8 to 18 times faster per
thread. On eight threads FreeIdea decodes at 278 MB/s to 1.21 GB/s. FreeIdea is a
high-compression archive tier: archives, end-of-day files, deliveries and research replay, not
a hot real-time path.

## Who saves what

| You are | Where the saving lands |
|---|---|
| Market data vendor | Years of captures and files in storage, every client delivery, every replica |
| Capture and analytics appliance vendor | An archive tier behind your capture box: the IEX capture shrinks 19x |
| Trading firm | Years of captures kept in production, disaster recovery and research copies; research jobs read 30 to 47% of the bytes zstd -19 needs |
| Exchange historical data business | Smaller files for the products you sell and deliver |

These figures do not count A/B line deduplication: the IEX capture holds one line. If you
record both lines, FreeIdea stores the B line as references to the A line, on top of the
savings above.

## Your numbers

Run the evaluation build on a few days of your own data ([EVALUATION.md](EVALUATION.md)); it
prints the ratio. Then put your volumes, copies and prices into the calculator (Python 3, no
dependencies):

```
python savings.py --kind capture --raw-tb 2000 --copies 3 --egress-tb 150
python savings.py --ratio 17.8 --baseline-ratio 5.4 --raw-tb 800 --price 0.0125
python savings.py --help
```

## Assumptions

- Ratios measured on public data (IEX HIST, Nasdaq's public samples); your data will differ, and
  the evaluation measures it.
- List prices before discounts; 1 PB = 1,000 TB, 1 TB = 1,000 GB. Smaller archives pay a higher
  price per GB, so their saving per TB is higher than shown.
- The baseline is `zstd -19 --long`, a strong general setting. Faster settings in wide use
  compress less (on the IEX capture: `zstd -3` 4.88x, `gzip -9` 4.29x), so against them the
  saving is larger.
- Every FreeIdea file in these measurements was decompressed and compared with its original:
  all byte-identical.
