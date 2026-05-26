import requests
import time
import statistics
import random

BASE_URL = "http://127.0.0.1:8000"
DEVICE_ID = "sensor_01"
NUM_READS = 50  # reads per endpoint


# Helpers

def measure_latency(url: str) -> float | None:
    """Hit a GET endpoint once and return latency in ms, or None on error."""
    try:
        start = time.perf_counter()
        response = requests.get(url)
        latency_ms = (time.perf_counter() - start) * 1000
        response.raise_for_status()
        return latency_ms
    except requests.RequestException as e:
        print(f"  ❌ Request failed ({url}): {e}")
        return None


def run_reads(label: str, url: str, n: int) -> list[float]:
    """Run n reads against a URL and return the list of latencies."""
    print(f"\nRunning {n} reads → {label}")
    latencies = []

    for i in range(1, n + 1):
        latency = measure_latency(url)
        if latency is not None:
            latencies.append(latency)
            print(f"  [{i:>3}] {latency:.2f} ms")

    return latencies


def print_stats(label: str, latencies: list[float]):
    if not latencies:
        print(f"\n{label}: no data collected.")
        return

    avg = statistics.mean(latencies)
    median = statistics.median(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    minimum = min(latencies)
    maximum = max(latencies)
    stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    print(f"\n  {'Avg':<10} {avg:.2f} ms")
    print(f"  {'Median':<10} {median:.2f} ms")
    print(f"  {'P95':<10} {p95:.2f} ms")
    print(f"  {'Min':<10} {minimum:.2f} ms")
    print(f"  {'Max':<10} {maximum:.2f} ms")
    print(f"  {'Std Dev':<10} {stdev:.2f} ms")


def print_comparison(redis_latencies: list[float], pg_latencies: list[float]):
    if not redis_latencies or not pg_latencies:
        print("\nNot enough data for comparison.")
        return

    redis_avg = statistics.mean(redis_latencies)
    pg_avg = statistics.mean(pg_latencies)
    redis_p95 = sorted(redis_latencies)[int(len(redis_latencies) * 0.95)]
    pg_p95 = sorted(pg_latencies)[int(len(pg_latencies) * 0.95)]

    avg_reduction = ((pg_avg - redis_avg) / pg_avg) * 100
    p95_reduction = ((pg_p95 - redis_p95) / pg_p95) * 100

    faster_label = "Redis (cache)" if redis_avg < pg_avg else "PostgreSQL"

    print("\n" + "=" * 55)
    print("BENCHMARK COMPARISON")
    print("=" * 55)
    print(f"  {'Metric':<20} {'Redis':>12} {'PostgreSQL':>12}")
    print(f"  {'-'*44}")
    print(f"  {'Avg latency':<20} {redis_avg:>11.2f}ms {pg_avg:>11.2f}ms")
    print(f"  {'P95 latency':<20} {redis_p95:>11.2f}ms {pg_p95:>11.2f}ms")
    print(f"  {'Min latency':<20} {min(redis_latencies):>11.2f}ms {min(pg_latencies):>11.2f}ms")
    print(f"  {'Max latency':<20} {max(redis_latencies):>11.2f}ms {max(pg_latencies):>11.2f}ms")
    print(f"  {'Reads completed':<20} {len(redis_latencies):>12} {len(pg_latencies):>12}")
    print(f"  {'-'*44}")
    print(f"  Faster source    : {faster_label}")
    print(f"  Avg reduction    : {avg_reduction:+.1f}%  (Redis vs PostgreSQL)")
    print(f"  P95 reduction    : {p95_reduction:+.1f}%  (Redis vs PostgreSQL)")
    print("=" * 55)


# ── Main ─────────────────────────────────────────────────────────────────────

def run_benchmark():
    redis_url = f"{BASE_URL}/sensors/{DEVICE_ID}/latest"   # cache-first
    pg_url    = f"{BASE_URL}/sensors/{DEVICE_ID}/history"  # PostgreSQL always

    print("=" * 55)
    print("REDIS vs POSTGRESQL READ LATENCY BENCHMARK")
    print("=" * 55)
    print(f"  Device  : {DEVICE_ID}")
    print(f"  Reads   : {NUM_READS} per endpoint")
    print(f"  Redis   : GET /sensors/{{id}}/latest")
    print(f"  PG      : GET /sensors/{{id}}/history")

    # ── Redis reads ───────────────────────────────────────────
    redis_latencies = run_reads("Redis  — /latest", redis_url, NUM_READS)
    print("\nRedis Stats")
    print_stats("Redis", redis_latencies)

    # ── PostgreSQL reads ──────────────────────────────────────
    pg_latencies = run_reads("PostgreSQL — /history", pg_url, NUM_READS)
    print("\nPostgreSQL Stats")
    print_stats("PostgreSQL", pg_latencies)

    # ── Side-by-side comparison ───────────────────────────────
    print_comparison(redis_latencies, pg_latencies)

    # ── Save raw data for C5 writeup ──────────────────────────
    with open("benchmark_results.txt", "w") as f:
        f.write("reading,redis_ms,pg_ms\n")
        for i, (r, p) in enumerate(zip(redis_latencies, pg_latencies), 1):
            f.write(f"{i},{r:.4f},{p:.4f}\n")

    print(f"\n  Raw data saved → benchmark_results.txt")


if __name__ == "__main__":
    run_benchmark()