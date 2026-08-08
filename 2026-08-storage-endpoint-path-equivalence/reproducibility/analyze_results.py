#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
import math
import random
import statistics
from pathlib import Path


RATIO_MARGINS = {
    "latency_p50_ms": (0.90, 1.10),
    "latency_p95_ms": (0.85, 1.15),
    "requests_per_s": (0.90, 1.10),
    "jitter_ms": (0.80, 1.20),
}
ABS_MARGINS = {"error_rate": 0.005, "retransmit_rate": 0.002}
PAIRS = (("public", "service_endpoint"), ("public", "private"), ("service_endpoint", "private"))


def stable_seed(*parts):
    digest = hashlib.sha256("|".join(parts).encode()).digest()
    return int.from_bytes(digest[:4], "big")


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * p
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return values[low]
    return values[low] * (high - position) + values[high] * (position - low)


def bootstrap(values, statistic, seed, iterations=10000):
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        draw = [values[rng.randrange(len(values))] for _ in values]
        samples.append(statistic(draw))
    return percentile(samples, 0.025), percentile(samples, 0.975)


def load_results(path):
    rows = []
    for file in sorted(path.glob("performance/block-*/mode-*/benchmark-*.json")):
        with file.open(encoding="utf-8") as handle:
            content = json.load(handle)
            rows.extend(content if isinstance(content, list) else [content])
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = load_results(args.run_dir)
    output = args.run_dir / "analysis"
    output.mkdir(exist_ok=True)

    with (output / "block-aggregates.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "block", "seed", "mode", "variant", "concurrency", "measured_requests",
            "successes", "errors", "timeouts", "latency_p50_ms", "latency_p95_ms",
            "jitter_ms", "requests_per_s", "input_bytes_per_s", "tcp_retrans_segments",
            "tcp_original_segments",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fields})

    indexed = {(r["block"], r["mode"], r["variant"]): r for r in rows}
    verdicts = []
    for variant in ("fresh", "reused"):
        for left, right in PAIRS:
            paired = [
                (indexed[(block, left, variant)], indexed[(block, right, variant)])
                for block in range(1, 11)
                if (block, left, variant) in indexed and (block, right, variant) in indexed
            ]
            for metric, margin in RATIO_MARGINS.items():
                ratios = [
                    b[metric] / a[metric] for a, b in paired
                    if a.get(metric) not in (None, 0) and b.get(metric) is not None
                ]
                estimate = math.exp(statistics.mean(math.log(x) for x in ratios)) if ratios else None
                ci = bootstrap(
                    [math.log(x) for x in ratios],
                    lambda x: math.exp(statistics.mean(x)),
                    stable_seed(variant, left, right, metric),
                ) if ratios else (None, None)
                passed = bool(ratios) and ci[0] >= margin[0] and ci[1] <= margin[1]
                if metric == "jitter_ms" and paired:
                    absolute = [b[metric] - a[metric] for a, b in paired]
                    passed = passed and max(abs(x) for x in absolute) <= 2
                verdict = "equivalent" if passed else (
                    "not equivalent" if ci[1] < margin[0] or ci[0] > margin[1] else "inconclusive"
                )
                verdicts.append({
                    "variant": variant, "pair": f"{left}_vs_{right}", "metric": metric,
                    "estimate": estimate, "ci95_low": ci[0], "ci95_high": ci[1],
                    "margin_low": margin[0], "margin_high": margin[1],
                    "blocks": len(ratios), "verdict": verdict,
                })
            for metric, margin in ABS_MARGINS.items():
                differences = []
                for a, b in paired:
                    if metric == "error_rate":
                        av = a["errors"] / a["measured_requests"]
                        bv = b["errors"] / b["measured_requests"]
                    else:
                        if not a.get("tcp_original_segments") or not b.get("tcp_original_segments"):
                            continue
                        av = a["tcp_retrans_segments"] / a["tcp_original_segments"]
                        bv = b["tcp_retrans_segments"] / b["tcp_original_segments"]
                    differences.append(bv - av)
                estimate = statistics.mean(differences) if differences else None
                ci = bootstrap(
                    differences, statistics.mean,
                    stable_seed(variant, left, right, metric),
                ) if differences else (None, None)
                passed = bool(differences) and ci[0] >= -margin and ci[1] <= margin
                verdict = "equivalent" if passed else (
                    "not equivalent" if differences and (ci[0] > margin or ci[1] < -margin)
                    else "inconclusive"
                )
                verdicts.append({
                    "variant": variant, "pair": f"{left}_vs_{right}", "metric": metric,
                    "estimate": estimate, "ci95_low": ci[0], "ci95_high": ci[1],
                    "margin_low": -margin, "margin_high": margin,
                    "blocks": len(differences), "verdict": verdict,
                })

    with (output / "equivalence-verdicts.json").open("w", encoding="utf-8") as handle:
        json.dump(verdicts, handle, indent=2)
    print(json.dumps({"input_files": len(rows), "verdict_rows": len(verdicts)}, indent=2))


if __name__ == "__main__":
    main()
