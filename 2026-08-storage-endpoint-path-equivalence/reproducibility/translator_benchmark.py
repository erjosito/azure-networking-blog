#!/usr/bin/env python3
import argparse
import base64
import gzip
import hashlib
import http.client
import json
import socket
import statistics
import time
import urllib.parse
import urllib.request


BODY = json.dumps([{"Text": "Network path probe."}], separators=(",", ":")).encode()


def token():
    resource = urllib.parse.quote("https://cognitiveservices.azure.com/", safe="")
    url = (
        "http://169.254.169.254/metadata/identity/oauth2/token"
        f"?api-version=2018-02-01&resource={resource}"
    )
    request = urllib.request.Request(url, headers={"Metadata": "true"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)["access_token"]


def tcp_counter(name):
    try:
        with open("/proc/net/snmp", encoding="utf-8") as handle:
            lines = handle.read().splitlines()
        for index in range(0, len(lines) - 1, 2):
            keys = lines[index].split()
            values = lines[index + 1].split()
            if keys[0] == "Tcp:" and values[0] == "Tcp:" and name in keys:
                return int(values[keys.index(name)])
    except (OSError, ValueError):
        pass
    return None


def one_request(host, bearer, connection=None, injected_delay_ms=0):
    started = time.perf_counter()
    record = {
        "success": False,
        "status": None,
        "error": None,
        "timeout": False,
        "latency_ms": None,
        "remote_ip": None,
        "response_bytes": 0,
        "response_sha256": None,
        "input_bytes": len(BODY),
        "injected_delay_ms": injected_delay_ms,
    }
    owned = connection is None
    conn = connection or http.client.HTTPSConnection(host, timeout=30)
    try:
        if injected_delay_ms:
            time.sleep(injected_delay_ms / 1000)
        path = "/translator/text/v3.0/translate?api-version=3.0&to=fr"
        conn.request(
            "POST",
            path,
            body=BODY,
            headers={
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json; charset=UTF-8",
                "Ocp-Apim-Subscription-Region": "swedencentral",
            },
        )
        response = conn.getresponse()
        payload = response.read()
        peer = conn.sock.getpeername()[0] if conn.sock else None
        record.update(
            {
                "success": response.status == 200,
                "status": response.status,
                "remote_ip": peer,
                "response_bytes": len(payload),
                "response_sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    except (TimeoutError, socket.timeout) as exc:
        record["timeout"] = True
        record["error"] = type(exc).__name__
    except Exception as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        record["latency_ms"] = (time.perf_counter() - started) * 1000
        if owned:
            conn.close()
    return record


def run_phase(host, bearer, variant, count, interval, injected_delay_ms=0):
    records = []
    conn = None
    if variant == "reused":
        conn = http.client.HTTPSConnection(host, timeout=30)
    try:
        for _ in range(count):
            record = one_request(host, bearer, conn, injected_delay_ms)
            records.append(record)
            if variant == "reused" and record["error"]:
                conn.close()
                conn = http.client.HTTPSConnection(host, timeout=30)
            time.sleep(interval)
    finally:
        if conn:
            conn.close()
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--mode", required=True, choices=("public", "service_endpoint", "private"))
    parser.add_argument("--variant", required=True, choices=("fresh", "reused", "both"))
    parser.add_argument("--block", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--warmup", type=int, default=20)
    parser.add_argument("--samples", type=int, default=40)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--gzip-base64", action="store_true")
    parser.add_argument("--calibration-delay-ms", type=float, default=0)
    args = parser.parse_args()

    host = urllib.parse.urlparse(args.endpoint).hostname
    addresses = sorted({row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    bearer = token()

    def benchmark_variant(variant, injected_delay_ms=0, calibration_label=None):
        run_phase(host, bearer, variant, args.warmup, args.interval, injected_delay_ms)
        retrans_before = tcp_counter("RetransSegs")
        out_before = tcp_counter("OutSegs")
        started = time.time()
        records = run_phase(host, bearer, variant, args.samples, args.interval, injected_delay_ms)
        duration = time.time() - started
        retrans_after = tcp_counter("RetransSegs")
        out_after = tcp_counter("OutSegs")
        success = [row for row in records if row["success"]]
        latencies = [row["latency_ms"] for row in success]
        return {
        "schema": "sepath.translator.benchmark.v1",
        "block": args.block,
        "seed": args.seed,
        "mode": args.mode,
        "variant": variant,
        "calibration_label": calibration_label,
        "injected_delay_ms": injected_delay_ms,
        "concurrency": 1,
        "warmup_requests": args.warmup,
        "measured_requests": len(records),
        "started_epoch": started,
        "duration_s": duration,
        "dns_addresses": addresses,
        "successes": len(success),
        "errors": len(records) - len(success),
        "timeouts": sum(1 for row in records if row["timeout"]),
        "requests_per_s": len(success) / duration if duration else 0,
        "input_bytes_per_s": sum(row["input_bytes"] for row in success) / duration if duration else 0,
        "latency_p50_ms": statistics.median(latencies) if latencies else None,
        "latency_p95_ms": (
            sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] if latencies else None
        ),
        "jitter_ms": (
            sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)] - statistics.median(latencies)
            if latencies else None
        ),
        "tcp_retrans_segments": (
            retrans_after - retrans_before
            if retrans_before is not None and retrans_after is not None
            else None
        ),
        "tcp_original_segments": (
            out_after - out_before if out_before is not None and out_after is not None else None
        ),
        "records": records,
        }

    if args.calibration_delay_ms:
        if args.variant != "reused":
            raise SystemExit("Calibration requires --variant reused")
        arms = (
            (("control", 0), ("injected", args.calibration_delay_ms))
            if args.block % 2 else
            (("injected", args.calibration_delay_ms), ("control", 0))
        )
        results = [
            benchmark_variant("reused", delay, label)
            for label, delay in arms
        ]
        for result in results:
            result["schema"] = "sepath.translator.calibration.v1"
            result["arm_order"] = [label for label, _ in arms]
    else:
        variants = ("fresh", "reused") if args.variant == "both" else (args.variant,)
        results = [benchmark_variant(variant) for variant in variants]
    payload = json.dumps(results, separators=(",", ":"))
    if args.gzip_base64:
        payload = base64.b64encode(gzip.compress(payload.encode())).decode()
    print(payload)


if __name__ == "__main__":
    main()
