import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import statistics

RESULTS_FILE = "benchmark_results.txt"


def load_results(filepath: str) -> tuple[list[float], list[float]]:
    redis_ms, pg_ms = [], []
    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            redis_ms.append(float(row["redis_ms"]))
            pg_ms.append(float(row["pg_ms"]))
    return redis_ms, pg_ms


def plot_benchmark(redis_ms: list[float], pg_ms: list[float]):
    readings = list(range(1, len(redis_ms) + 1))

    redis_avg = statistics.mean(redis_ms)
    pg_avg    = statistics.mean(pg_ms)
    redis_p95 = sorted(redis_ms)[int(len(redis_ms) * 0.95)]
    pg_p95    = sorted(pg_ms)[int(len(pg_ms) * 0.95)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Redis vs PostgreSQL — Read Latency Benchmark", fontsize=15, fontweight="bold", y=0.98)

    REDIS_COLOR = "#4FC3F7"   # light blue
    PG_COLOR    = "#EF9A9A"   # soft red

    # ── 1. Line chart — latency per reading ──────────────────
    ax1 = axes[0, 0]
    ax1.plot(readings, redis_ms, color=REDIS_COLOR, linewidth=1.2, label="Redis /latest")
    ax1.plot(readings, pg_ms,    color=PG_COLOR,    linewidth=1.2, label="PostgreSQL /history")
    ax1.axhline(redis_avg, color=REDIS_COLOR, linestyle="--", linewidth=0.9, alpha=0.7)
    ax1.axhline(pg_avg,    color=PG_COLOR,    linestyle="--", linewidth=0.9, alpha=0.7)
    ax1.set_title("Latency per Reading")
    ax1.set_xlabel("Reading #")
    ax1.set_ylabel("Latency (ms)")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # ── 2. Histogram — latency distribution ──────────────────
    ax2 = axes[0, 1]
    ax2.hist(redis_ms, bins=20, color=REDIS_COLOR, alpha=0.7, label="Redis")
    ax2.hist(pg_ms,    bins=20, color=PG_COLOR,    alpha=0.7, label="PostgreSQL")
    ax2.set_title("Latency Distribution")
    ax2.set_xlabel("Latency (ms)")
    ax2.set_ylabel("Frequency")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # ── 3. Bar chart — avg vs p95 ─────────────────────────────
    ax3 = axes[1, 0]
    metrics = ["Avg", "P95"]
    redis_vals = [redis_avg, redis_p95]
    pg_vals    = [pg_avg,    pg_p95]
    x = range(len(metrics))
    width = 0.35
    ax3.bar([i - width/2 for i in x], redis_vals, width, color=REDIS_COLOR, label="Redis")
    ax3.bar([i + width/2 for i in x], pg_vals,    width, color=PG_COLOR,    label="PostgreSQL")
    for i, (rv, pv) in enumerate(zip(redis_vals, pg_vals)):
        ax3.text(i - width/2, rv + 0.2, f"{rv:.1f}", ha="center", fontsize=8)
        ax3.text(i + width/2, pv + 0.2, f"{pv:.1f}", ha="center", fontsize=8)
    ax3.set_title("Avg vs P95 Latency")
    ax3.set_ylabel("Latency (ms)")
    ax3.set_xticks(list(x))
    ax3.set_xticklabels(metrics)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis="y")

    # ── 4. Stats summary text panel ──────────────────────────
    ax4 = axes[1, 1]
    ax4.axis("off")

    avg_reduction = ((pg_avg - redis_avg) / pg_avg) * 100
    p95_reduction = ((pg_p95 - redis_p95) / pg_p95) * 100

    summary = (
        f"{'Metric':<18} {'Redis':>9} {'PostgreSQL':>12}\n"
        f"{'─'*41}\n"
        f"{'Avg (ms)':<18} {redis_avg:>9.2f} {pg_avg:>12.2f}\n"
        f"{'P95 (ms)':<18} {redis_p95:>9.2f} {pg_p95:>12.2f}\n"
        f"{'Min (ms)':<18} {min(redis_ms):>9.2f} {min(pg_ms):>12.2f}\n"
        f"{'Max (ms)':<18} {max(redis_ms):>9.2f} {max(pg_ms):>12.2f}\n"
        f"{'Std Dev (ms)':<18} {statistics.stdev(redis_ms):>9.2f} {statistics.stdev(pg_ms):>12.2f}\n"
        f"{'─'*41}\n"
        f"{'Avg reduction':<18} {avg_reduction:>+8.1f}%\n"
        f"{'P95 reduction':<18} {p95_reduction:>+8.1f}%\n"
    )
    ax4.text(
        0.05, 0.95, summary,
        transform=ax4.transAxes,
        fontsize=9, verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="#F5F5F5", alpha=0.8)
    )
    ax4.set_title("Summary Statistics")

    redis_patch = mpatches.Patch(color=REDIS_COLOR, label="Redis (cache)")
    pg_patch    = mpatches.Patch(color=PG_COLOR,    label="PostgreSQL")
    fig.legend(handles=[redis_patch, pg_patch], loc="lower center", ncol=2, fontsize=10, frameon=False)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig("benchmark_chart.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("Chart saved → benchmark_chart.png")


if __name__ == "__main__":
    redis_ms, pg_ms = load_results(RESULTS_FILE)
    plot_benchmark(redis_ms, pg_ms)