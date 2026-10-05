#!/usr/bin/env python3
"""What FreeIdea saves on your archive: storage, delivery and transfer time.

Uses the ratios measured on public data (RESULTS.md), or your own from the evaluation build.
No dependencies; Python 3.8 or later.

  python savings.py --kind capture --raw-tb 1000
  python savings.py --kind itch --raw-tb 2500 --copies 3 --egress-tb 200
  python savings.py --ratio 17.8 --baseline-ratio 5.4 --raw-tb 800 --price 0.0125

Units: 1 TB = 1,000 GB, prices in USD. --raw-tb is the uncompressed size of the data you keep;
--egress-tb is how much raw data you deliver per month (to clients, other regions or sites).
"""

import argparse

# Measured ratios (raw size / compressed size), RESULTS.md; FreeIdea with 8 threads.
MEASURED = {
    "capture": {"what": "IEX DEEP packet capture, first 3.0 GB", "freeidea": 19.344, "zstd": 5.810, "xz": 7.134},
    "itch": {"what": "Nasdaq TotalView-ITCH 5.0, full day 2019-10-30", "freeidea": 7.337, "zstd": 2.985, "xz": 3.297},
    "itto": {"what": "Nasdaq ITTO 4.0 options, first 7.23 GB", "freeidea": 6.156, "zstd": 2.920, "xz": 3.340},
}

# AWS list prices, US East (N. Virginia), AWS price list of 2026-09-28: S3 Standard above 500 TB
# per GB-month; data transfer out to the internet above 150 TB a month, per GB.
S3_STANDARD = 0.021
EGRESS = 0.05


def money(v):
    return f"${v:,.0f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", choices=sorted(MEASURED), default="capture", help="measured data type (default: capture)")
    ap.add_argument("--baseline", choices=["zstd", "xz"], default="zstd", help="what you store with today (default: zstd -19)")
    ap.add_argument("--ratio", type=float, help="your FreeIdea ratio, from 'freeidea compress' on your data")
    ap.add_argument("--baseline-ratio", type=float, help="your current ratio (raw / stored)")
    ap.add_argument("--raw-tb", type=float, default=1000, help="raw TB you keep (default: 1000 = 1 PB)")
    ap.add_argument("--copies", type=int, default=1, help="copies kept: production, disaster recovery, research ... (default: 1)")
    ap.add_argument("--price", type=float, default=S3_STANDARD, help=f"storage price per GB-month (default: {S3_STANDARD}, S3 Standard)")
    ap.add_argument("--egress-tb", type=float, default=0, help="raw TB delivered per month (default: 0)")
    ap.add_argument("--egress-price", type=float, default=EGRESS, help=f"delivery price per GB (default: {EGRESS}, S3 to internet)")
    ap.add_argument("--link-gbit", type=float, default=10, help="link speed for the transfer-time line (default: 10 Gbit/s)")
    a = ap.parse_args()

    m = MEASURED[a.kind]
    fi = a.ratio or m["freeidea"]
    base = a.baseline_ratio or m[a.baseline]
    src = "your ratios" if a.ratio or a.baseline_ratio else f"measured on {m['what']}"
    base_name = "current" if a.baseline_ratio else ("zstd -19" if a.baseline == "zstd" else "xz -9")

    stored_base = a.raw_tb / base * a.copies
    stored_fi = a.raw_tb / fi * a.copies
    year = 12 * 1000 * a.price
    cost_base, cost_fi = stored_base * year, stored_fi * year
    eg = 12 * 1000 * a.egress_price
    eg_base, eg_fi = a.egress_tb / base * eg, a.egress_tb / fi * eg
    link = a.link_gbit / 8 * 1e9  # bytes per second

    def hours(tb):
        return tb * 1e12 / link / 3600

    print(f"Ratios ({src}): FreeIdea {fi:.2f}x, {base_name} {base:.2f}x; FreeIdea stores {base / fi:.0%} of the {base_name} bytes")
    print(f"Raw data: {a.raw_tb:,.0f} TB, {a.copies} cop{'y' if a.copies == 1 else 'ies'}, storage ${a.price}/GB-month")
    print()
    print(f"{'':28}{base_name:>14}{'FreeIdea':>14}{'saved':>14}")
    print(f"{'Stored, TB':28}{stored_base:>14,.0f}{stored_fi:>14,.0f}{stored_base - stored_fi:>14,.0f}")
    print(f"{'Storage per year':28}{money(cost_base):>14}{money(cost_fi):>14}{money(cost_base - cost_fi):>14}")
    if a.egress_tb:
        print(f"{'Delivery per year':28}{money(eg_base):>14}{money(eg_fi):>14}{money(eg_base - eg_fi):>14}")
        print(f"{'Total per year':28}{money(cost_base + eg_base):>14}{money(cost_fi + eg_fi):>14}{money(cost_base + eg_base - cost_fi - eg_fi):>14}")
    print(f"{f'One copy over {a.link_gbit:g} Gbit/s, h':28}{hours(a.raw_tb / base):>14,.1f}{hours(a.raw_tb / fi):>14,.1f}")
    print()
    print("List prices before discounts. Your ratio: run the evaluation build on a few days of your data.")


if __name__ == "__main__":
    main()
