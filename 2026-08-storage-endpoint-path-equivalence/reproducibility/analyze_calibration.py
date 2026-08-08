#!/usr/bin/env python3
import argparse
import hashlib
import json
import random
import statistics
from pathlib import Path


def percentile(values, p):
    values = sorted(values)
    position = (len(values) - 1) * p
    low = int(position)
    high = min(low + 1, len(values) - 1)
    fraction = position - low
    return values[low] * (1 - fraction) + values[high] * fraction


def bootstrap_mean(values, label, iterations=10000):
    seed = int.from_bytes(hashlib.sha256(label.encode()).digest()[:4], "big")
    rng = random.Random(seed)
    draws = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in values]
        draws.append(statistics.mean(sample))
    return percentile(draws, 0.025), percentile(draws, 0.975)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = []
    for path in sorted((args.run_dir / "calibration").glob("block-*/calibration.json")):
        rows.extend(json.loads(path.read_text(encoding="utf-8")))
    indexed = {(row["block"], row["calibration_label"]): row for row in rows}
    pairs = [(indexed[(block, "control")], indexed[(block, "injected")]) for block in range(1, 11)]

    p50_deltas = [injected["latency_p50_ms"] - control["latency_p50_ms"] for control, injected in pairs]
    p95_deltas = [injected["latency_p95_ms"] - control["latency_p95_ms"] for control, injected in pairs]
    control_p50 = [control["latency_p50_ms"] for control, _ in pairs]
    control_center = statistics.median(control_p50)
    noise_floor = percentile([abs(value - control_center) for value in control_p50], 0.95)
    equivalence_floor = control_center * 0.10
    detection_floor = max(noise_floor, equivalence_floor, 5.0)
    p50_ci = bootstrap_mean(p50_deltas, "calibration-p50")
    p95_ci = bootstrap_mean(p95_deltas, "calibration-p95")
    observed_p50 = statistics.mean(p50_deltas)
    observed_p95 = statistics.mean(p95_deltas)

    output = {
        "schema": "sepath.translator.calibration.analysis.v1",
        "blocks": 10,
        "measured_requests": sum(row["measured_requests"] for row in rows),
        "warmup_requests": sum(row["warmup_requests"] for row in rows),
        "errors": sum(row["errors"] for row in rows),
        "timeouts": sum(row["timeouts"] for row in rows),
        "predeclared_injected_delay_ms": 25.0,
        "predeclared_expected_shift_ms": [20.0, 30.0],
        "control_p50_ms": control_center,
        "noise_floor_ms": noise_floor,
        "equivalence_margin_floor_ms": equivalence_floor,
        "detection_floor_ms": detection_floor,
        "observed_p50_delta_ms": observed_p50,
        "p50_delta_ci95_ms": list(p50_ci),
        "observed_p95_delta_ms": observed_p95,
        "p95_delta_ci95_ms": list(p95_ci),
        "sensitivity_detected": (
            p50_ci[0] > detection_floor
            and 20.0 <= observed_p50 <= 30.0
        ),
        "interpretation": "Positive-control sensitivity only; this does not establish endpoint path identity.",
    }
    output_path = args.run_dir / "calibration" / "calibration-analysis.json"
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
