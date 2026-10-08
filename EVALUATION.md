# FreeIdea evaluation guide

For the engineers who run the pilot: about two weeks of work, while the build runs for 90 days.
Everything runs on your machines; no data
and no file leaves your premises. We only ask for the numbers in the table at the end.

## What you need

- The `freeidea` evaluation build made for your organisation (one file, no installation;
  ask for it at benjaminweisz.dev@gmail.com, subject "Evaluation build request"). It compresses until the date it prints on
  every run, 90 days after it was made (the license's evaluation period); decompress and
  verify never expire. For non-commercial use, ask for a new build when it runs out.
- 5 to 10 trading days of your data in one of these forms:
  - Nasdaq TotalView-ITCH 5.0 files in BinaryFILE framing (each message preceded by its
    2-byte big-endian length), also BX and PSX ITCH: the format of Nasdaq's historical files;
  - Nasdaq ITCH to Trade Options (ITTO) 4.0 files in the same framing;
  - packet captures (pcap or pcapng) of MoldUDP64 ITCH/ITTO, IEX-TP DEEP, OPRA Pillar,
    NYSE XDP (Integrated Feed) or Cboe PITCH 2.x feeds. Other traffic in a capture is kept
    exactly but compresses like ordinary data.
- Disk space for one compressed copy (about one sixth of the input).

## Install

1. Unpack the package.
   - Windows: right-click the `.zip`, Properties, tick **Unblock**, OK, then Extract All.
     Unblocking first keeps Windows from warning about a program downloaded from the internet.
   - Linux: `tar xzf freeidea-<version>-eval-<organisation>-linux-<arch>.tar.gz`. The binary is
     static and needs no libraries; if it lost its execute bit, `chmod +x freeidea`.
2. Check the download against `SHA256SUMS.txt`, which lists each archive and the binary inside
   it:
   - Linux: `sha256sum -c SHA256SUMS.txt --ignore-missing` in the folder with the archive and
     the unpacked files;
   - Windows (PowerShell): `Get-FileHash <archive or freeidea.exe> -Algorithm SHA256` and compare
     with the matching line.
3. In a terminal, `freeidea version` shows the version, the organisation the build is for and
   the last day it compresses; `freeidea help` lists the commands.

The Windows program is not code-signed yet. If SmartScreen still says "Windows protected your
PC", choose **More info**, then **Run anyway**.

## Steps

1. Compress each day and note the printed ratio and time:

   ```
   freeidea compress 20251128.itch 20251128.fi
   ```

2. Prove it is lossless. `verify` decodes and compares with the original byte for byte:

   ```
   freeidea verify 20251128.itch 20251128.fi
   ```

   Independently, you can also decompress and compare with your own tools:

   ```
   freeidea decompress 20251128.fi 20251128.back
   cmp 20251128.itch 20251128.back        # or: certutil -hashfile ... SHA256 on Windows
   ```

3. Measure decode speed the way you would use it: to a file, to `null` (pure decode), or
   piped into your replay:

   ```
   freeidea decompress -j 8 20251128.fi null
   freeidea decompress 20251128.fi - | your_replay
   ```

   `-` is standard input or output for both commands, so FreeIdea sits inside a pipe, for
   example straight from storage into a replay, or from a download into an archive:

   ```
   aws s3 cp s3://bucket/20251128.fi - | freeidea decompress - - | your_replay
   curl -s https://host/20251128.itch.gz | gunzip | freeidea compress - 20251128.fi
   ```

4. Compare with what you store today (zstd, gzip, kdb+, Parquet ...): the size of the same day
   in your current format.

5. Optional: `freeidea stats 20251128.itch` prints where the bits go per message type. It
   helps us if a day compresses worse than expected.

## Options

| Option | Default | Effect |
|---|---|---|
| `-j N` | cores, at most 8 | worker threads for compress, decompress and verify |
| `--segment-mb M` | input size / threads: 64..256 (ITCH), 512..2048 (ITTO), 256..1024 (captures); from standard input the largest | larger segments: smaller files, less parallelism |
| `--feed itch\|itto\|pcap` | recognised from the input | force the input type |

Memory: FreeIdea holds up to threads + 2 segments at a time. Peaks measured at 8 threads: a
Nasdaq ITCH day (9 GB) 3.7 GB compressing and 3.3 GB decompressing, the IEX capture (3 GB)
3.7 and 3.5 GB, the ITTO file (7.2 GB, larger segments) 10.9 and 12.0 GB. Without `-j`,
FreeIdea uses fewer threads when a run would not fit in free memory, says so, and writes the
same file; with `-j` it keeps your setting and warns.

Data that is not a supported feed (other traffic, other formats) goes through a general
fallback that compresses poorly; `compress` says so when it is more than 30% of the input. A
segment that would not get smaller is stored as it is, so nothing grows by more than a few
bytes. Files with stored segments need FreeIdea 0.2.1 or newer to decompress; capture files
written by 0.4.0 need 0.4.0 or newer.

## Damage handling

Each segment carries its size and a 64-bit checksum. A truncated or altered `.fi` file makes
`decompress` and `verify` stop with an error; they never write silently different data.

## Please send back

| Day | Raw bytes | Your current format and bytes | FreeIdea bytes | verify ok | Compress s (threads) | Decompress s (threads) |
|---|---|---|---|---|---|---|
| | | | | | | |
