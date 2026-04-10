"""
analyze.py  — Milestone 4 Analysis & Validation Script
========================================================
Runs all experiment groups, exports JSON data files, and
produces matplotlib figures used in the PDF report.

Experiment groups
-----------------
  A  : Sensitivity — vary arrival rate λ  (5 values)
  B  : Sensitivity — vary service rate μ  (5 values)
  C  : Sensitivity — vary server count N  (5 values)
  D  : Sensitivity — vary request timeout (5 values)
  E  : Algorithm comparison RR vs LL (baseline, matched seeds, 10 reps each)
  F  : Scenario tests (Light / Normal / Peak / Overload / Failure-sim)
  G  : Extreme / validation runs (λ→0, ρ>>1, single server)
"""

import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from simulation_engine import SimulationEngine

# output directories
BASE   = os.path.join(os.path.dirname(__file__), "..", "results")
FIG_DIR = os.path.join(BASE, "figures")
JSON_DIR = os.path.join(BASE, "json")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

# shared defaults
DEFAULTS = dict(num_servers=3, arrival_rate=2.0, service_rate=1.5,
                simulation_time=500.0, dt=1.0, request_timeout=50.0,
                failure_rate=0.0, recovery_rate=0.0)

ALL_RESULTS: list[dict] = []


# ─────────────────────────────────────────────────────────────────────
# Helper — run one simulation and save JSON
# ─────────────────────────────────────────────────────────────────────
def run_sim(run_id: str, **kwargs) -> dict:
    params = {**DEFAULTS, **kwargs, "run_id": run_id}
    eng = SimulationEngine(**params)
    eng.run()
    r = eng.results()
    path = os.path.join(JSON_DIR, f"{run_id}.json")
    with open(path, "w") as f:
        json.dump(r, f, indent=2)
    ALL_RESULTS.append(r)
    return r


# ─────────────────────────────────────────────────────────────────────
# Helper — repeated runs for statistics
# ─────────────────────────────────────────────────────────────────────
def run_repeated(base_id: str, n_reps: int, **kwargs) -> list[dict]:
    results = []
    for i in range(n_reps):
        rid = f"{base_id}_rep{i+1:02d}"
        r = run_sim(rid, seed=100 + i, **kwargs)
        results.append(r)
    return results


def extract_metric(results: list[dict], key: str) -> list[float]:
    return [r["metrics"][key] for r in results]


def ci95(values: list[float]) -> tuple[float, float]:
    """Return (mean, half-width) 95% CI."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mu = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if n > 1 else 0.0
    hw = 1.96 * sd / math.sqrt(n)
    return mu, hw


# ─────────────────────────────────────────────────────────────────────
# A  Sensitivity — arrival rate λ
# ─────────────────────────────────────────────────────────────────────
print("Running Group A: sensitivity — arrival rate...")
lambda_values = [0.5, 1.0, 2.0, 3.0, 4.0]
sens_lambda: list[dict] = []
for idx, lam in enumerate(lambda_values):
    r = run_sim(f"A_{idx+1:03d}", arrival_rate=lam, algorithm="round_robin", seed=42)
    sens_lambda.append(r)

# ─────────────────────────────────────────────────────────────────────
# B  Sensitivity — service rate μ
# ─────────────────────────────────────────────────────────────────────
print("Running Group B: sensitivity — service rate...")
mu_values = [0.8, 1.0, 1.5, 2.0, 3.0]
sens_mu: list[dict] = []
for idx, mu in enumerate(mu_values):
    r = run_sim(f"B_{idx+1:03d}", service_rate=mu, algorithm="round_robin", seed=42)
    sens_mu.append(r)

# ─────────────────────────────────────────────────────────────────────
# C  Sensitivity — server count N
# ─────────────────────────────────────────────────────────────────────
print("Running Group C: sensitivity — server count...")
server_counts = [1, 2, 3, 5, 8]
sens_N: list[dict] = []
for idx, n in enumerate(server_counts):
    r = run_sim(f"C_{idx+1:03d}", num_servers=n, algorithm="round_robin", seed=42)
    sens_N.append(r)

# ─────────────────────────────────────────────────────────────────────
# D  Sensitivity — request timeout
# ─────────────────────────────────────────────────────────────────────
print("Running Group D: sensitivity — timeout...")
timeout_values = [5.0, 10.0, 25.0, 50.0, 200.0]
sens_timeout: list[dict] = []
for idx, t in enumerate(timeout_values):
    r = run_sim(f"D_{idx+1:03d}", request_timeout=t, algorithm="round_robin", seed=42)
    sens_timeout.append(r)

# ─────────────────────────────────────────────────────────────────────
# E  Algorithm comparison: RR vs LL — 10 replicates each
# ─────────────────────────────────────────────────────────────────────
print("Running Group E: algorithm comparison (10 reps each)...")
rr_reps = run_repeated("E_RR", 10, algorithm="round_robin")
ll_reps = run_repeated("E_LL", 10, algorithm="least_loaded")

rr_rt  = extract_metric(rr_reps, "avg_response_time")
ll_rt  = extract_metric(ll_reps, "avg_response_time")
rr_p95 = extract_metric(rr_reps, "p95_response_time")
ll_p95 = extract_metric(ll_reps, "p95_response_time")
rr_drop = extract_metric(rr_reps, "drop_rate")
ll_drop = extract_metric(ll_reps, "drop_rate")

rr_rt_mean,  rr_rt_hw  = ci95(rr_rt)
ll_rt_mean,  ll_rt_hw  = ci95(ll_rt)
rr_p95_mean, rr_p95_hw = ci95(rr_p95)
ll_p95_mean, ll_p95_hw = ci95(ll_p95)
rr_drop_mean, rr_drop_hw = ci95(rr_drop)
ll_drop_mean, ll_drop_hw = ci95(ll_drop)

# ─────────────────────────────────────────────────────────────────────
# F  Scenario tests
# ─────────────────────────────────────────────────────────────────────
print("Running Group F: scenario tests...")
scenarios = [
    ("F_001_light",    dict(arrival_rate=0.5,  service_rate=1.5, num_servers=3)),
    ("F_002_normal",   dict(arrival_rate=2.0,  service_rate=1.5, num_servers=3)),
    ("F_003_peak",     dict(arrival_rate=3.5,  service_rate=1.5, num_servers=3)),
    ("F_004_overload", dict(arrival_rate=6.0,  service_rate=1.5, num_servers=3)),
    ("F_005_failure",  dict(arrival_rate=2.0,  service_rate=1.5, num_servers=1)),
]
scenario_results: list[dict] = []
for rid, kw in scenarios:
    r = run_sim(rid, algorithm="least_loaded", seed=42, **kw)
    scenario_results.append(r)

# ─────────────────────────────────────────────────────────────────────
# G  Validation / extreme conditions
# ─────────────────────────────────────────────────────────────────────
print("Running Group G: validation / extreme conditions...")
extreme_cases = [
    ("G_001_zero_load",     dict(arrival_rate=0.01, service_rate=1.5, num_servers=3)),
    ("G_002_overload",      dict(arrival_rate=9.0,  service_rate=1.5, num_servers=3)),
    ("G_003_single_server", dict(arrival_rate=1.0,  service_rate=1.5, num_servers=1)),
    ("G_004_high_mu",       dict(arrival_rate=2.0,  service_rate=5.0, num_servers=3)),
    ("G_005_tight_timeout", dict(arrival_rate=2.0,  service_rate=1.5, num_servers=3, request_timeout=2.0)),
]
extreme_results: list[dict] = []
for rid, kw in extreme_cases:
    r = run_sim(rid, algorithm="round_robin", seed=42, **kw)
    extreme_results.append(r)


# ─────────────────────────────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────────────────────────────

STYLE = {
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.3,
    "figure.dpi":         130,
    "font.size":          10,
}

def save(name: str):
    path = os.path.join(FIG_DIR, name)
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {name}")
    return path


# Fig 1 — λ sensitivity (response time + drop rate)
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    rt_vals  = [r["metrics"]["avg_response_time"] for r in sens_lambda]
    dr_vals  = [r["metrics"]["drop_rate"] * 100   for r in sens_lambda]
    rho_vals = [r["metrics"]["theoretical_utilization"] for r in sens_lambda]

    ax1.plot(lambda_values, rt_vals, "o-", color="#2563EB", linewidth=2)
    ax1.set_xlabel("Arrival Rate λ (req/time-unit)")
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Fig 1a — Avg Response Time vs λ")
    for x, y, r in zip(lambda_values, rt_vals, rho_vals):
        ax1.annotate(f"ρ={r:.2f}", (x, y), textcoords="offset points",
                     xytext=(0, 7), ha="center", fontsize=8, color="#6B7280")

    ax2.bar(lambda_values, dr_vals, color="#EF4444", alpha=0.7, width=0.3)
    ax2.set_xlabel("Arrival Rate λ (req/time-unit)")
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Fig 1b — Drop Rate vs λ")

    fig.suptitle("Sensitivity Analysis: Arrival Rate (λ)", fontweight="bold")
    plt.tight_layout()
save("fig01_sensitivity_lambda.png")


# Fig 2 — μ sensitivity
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    rt_mu = [r["metrics"]["avg_response_time"] for r in sens_mu]
    p95_mu = [r["metrics"]["p95_response_time"] for r in sens_mu]

    ax1.plot(mu_values, rt_mu,  "s-", color="#059669", linewidth=2, label="Mean RT")
    ax1.plot(mu_values, p95_mu, "^--", color="#D97706", linewidth=2, label="P95 RT")
    ax1.set_xlabel("Service Rate μ (completions/time-unit)")
    ax1.set_ylabel("Response Time (time-units)")
    ax1.set_title("Fig 2a — Response Time vs μ")
    ax1.legend()

    util_mu = [r["metrics"]["theoretical_utilization"] for r in sens_mu]
    ax2.plot(mu_values, util_mu, "o-", color="#7C3AED", linewidth=2)
    ax2.axhline(1.0, linestyle="--", color="red", alpha=0.5, label="ρ = 1 (saturation)")
    ax2.set_xlabel("Service Rate μ")
    ax2.set_ylabel("Theoretical Utilization ρ")
    ax2.set_title("Fig 2b — Utilization vs μ")
    ax2.legend()

    fig.suptitle("Sensitivity Analysis: Service Rate (μ)", fontweight="bold")
    plt.tight_layout()
save("fig02_sensitivity_mu.png")


# Fig 3 — N sensitivity
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    rt_N  = [r["metrics"]["avg_response_time"] for r in sens_N]
    dr_N  = [r["metrics"]["drop_rate"] * 100   for r in sens_N]

    ax1.plot(server_counts, rt_N, "o-", color="#0891B2", linewidth=2)
    ax1.set_xlabel("Number of Servers (N)")
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Fig 3a — Response Time vs Server Count")

    ax2.plot(server_counts, dr_N, "s--", color="#DC2626", linewidth=2)
    ax2.set_xlabel("Number of Servers (N)")
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Fig 3b — Drop Rate vs Server Count")

    fig.suptitle("Sensitivity Analysis: Number of Servers (N)", fontweight="bold")
    plt.tight_layout()
save("fig03_sensitivity_N.png")


# Fig 4 — Algorithm comparison box plot
with plt.rc_context(STYLE):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    data_pairs = [
        (rr_rt,  ll_rt,  "Avg Response Time", "time-units"),
        (rr_p95, ll_p95, "P95 Response Time", "time-units"),
        ([v*100 for v in rr_drop], [v*100 for v in ll_drop], "Drop Rate", "%"),
    ]
    colors = ["#2563EB", "#059669"]
    for ax, (rr_d, ll_d, label, unit) in zip(axes, data_pairs):
        bp = ax.boxplot([rr_d, ll_d], patch_artist=True,
                        medianprops=dict(color="black", linewidth=2))
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Round Robin", "Least Loaded"])
        ax.set_ylabel(f"{label} ({unit})")
        ax.set_title(f"Fig 4 — {label}")

    fig.suptitle("Algorithm Comparison: Round Robin vs Least Loaded (10 reps each)",
                 fontweight="bold")
    plt.tight_layout()
save("fig04_algorithm_comparison.png")


# Fig 5 — Scenario comparison bar chart
with plt.rc_context(STYLE):
    labels = ["Light\n(λ=0.5)", "Normal\n(λ=2.0)", "Peak\n(λ=3.5)",
              "Overload\n(λ=6.0)", "Failure\n(N=1)"]
    rt_sc  = [r["metrics"]["avg_response_time"] for r in scenario_results]
    dr_sc  = [r["metrics"]["drop_rate"] * 100   for r in scenario_results]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    bar_colors = ["#10B981", "#2563EB", "#F59E0B", "#EF4444", "#8B5CF6"]

    ax1.bar(labels, rt_sc, color=bar_colors, alpha=0.8)
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Fig 5a — Response Time by Scenario")

    ax2.bar(labels, dr_sc, color=bar_colors, alpha=0.8)
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Fig 5b — Drop Rate by Scenario")

    fig.suptitle("Scenario Analysis Results", fontweight="bold")
    plt.tight_layout()
save("fig05_scenario_comparison.png")


# Fig 6 — Per-server utilization heat-map (Normal scenario run)
with plt.rc_context(STYLE):
    # Re-run Normal scenario briefly to get per-server data
    eng_rr = SimulationEngine(algorithm="round_robin",  run_id="heatmap_rr",
                               seed=42, **DEFAULTS)
    eng_ll = SimulationEngine(algorithm="least_loaded", run_id="heatmap_ll",
                               seed=42, **DEFAULTS)
    eng_rr.run(); eng_ll.run()

    psu_rr = eng_rr.per_server_utilization()
    psu_ll = eng_ll.per_server_utilization()
    data_heat = np.array([psu_rr, psu_ll])

    fig, ax = plt.subplots(figsize=(6, 3))
    im = ax.imshow(data_heat, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(psu_rr)))
    ax.set_xticklabels([f"Server {i}" for i in range(len(psu_rr))])
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Round Robin", "Least Loaded"])
    plt.colorbar(im, ax=ax, label="Empirical Utilization")
    for r in range(2):
        for c in range(len(psu_rr)):
            val = data_heat[r, c]
            ax.text(c, r, f"{val:.3f}", ha="center", va="center",
                    fontsize=11, color="black" if val < 0.6 else "white")
    ax.set_title("Fig 6 — Per-Server Utilization Heatmap")
    plt.tight_layout()
save("fig06_perserver_utilization.png")


# Fig 7 — Queue depth over time (first 100 ticks, Normal scenario, RR vs LL)
with plt.rc_context(STYLE):
    T = 150
    qd_rr = eng_rr.queue_depth_history()
    qd_ll = eng_ll.queue_depth_history()
    total_rr = [sum(qd_rr[s][t] for s in range(len(qd_rr))) for t in range(T)]
    total_ll = [sum(qd_ll[s][t] for s in range(len(qd_ll))) for t in range(T)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(T), total_rr, label="Round Robin",   color="#2563EB", linewidth=1.5)
    ax.plot(range(T), total_ll, label="Least Loaded",  color="#059669", linewidth=1.5)
    ax.set_xlabel("Simulation Tick")
    ax.set_ylabel("Total Queue Depth (all servers)")
    ax.set_title("Fig 7 — Queue Depth Over Time: RR vs LL (first 150 ticks)")
    ax.legend()
    plt.tight_layout()
save("fig07_queue_depth_time.png")


# Fig 8 — Sensitivity summary: normalised sensitivity coefficients
with plt.rc_context(STYLE):
    # Compute sensitivity = % change output / % change input
    # Using first and last values in each sensitivity sweep
    def sens_coeff(inputs, outputs):
        pct_in  = (inputs[-1] - inputs[0])  / inputs[0]  * 100
        pct_out = (outputs[-1] - outputs[0]) / (outputs[0] + 1e-9) * 100
        return abs(pct_out / pct_in) if pct_in != 0 else 0.0

    rt_lam = [r["metrics"]["avg_response_time"] for r in sens_lambda]
    rt_mu2 = [r["metrics"]["avg_response_time"] for r in sens_mu]
    rt_N2  = [r["metrics"]["avg_response_time"] for r in sens_N]
    rt_to  = [r["metrics"]["avg_response_time"] for r in sens_timeout]

    s_lam = sens_coeff(lambda_values, rt_lam)
    s_mu  = sens_coeff(mu_values,     rt_mu2)
    s_N   = sens_coeff([float(n) for n in server_counts], rt_N2)
    s_to  = sens_coeff(timeout_values, rt_to)

    params_lbl = ["Arrival Rate\n(λ)", "Service Rate\n(μ)", "Server Count\n(N)", "Timeout\n(T)"]
    s_vals = [s_lam, s_mu, s_N, s_to]
    bar_c  = ["#EF4444" if v > 1 else "#2563EB" for v in s_vals]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(params_lbl, s_vals, color=bar_c, alpha=0.8)
    ax.axhline(1.0, linestyle="--", color="gray", alpha=0.6, label="Sensitivity = 1.0")
    ax.set_ylabel("Sensitivity Coefficient\n(|%Δ output / %Δ input|)")
    ax.set_title("Fig 8 — Sensitivity Coefficients for Avg Response Time")
    ax.legend()
    for bar, v in zip(bars, s_vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f"{v:.2f}", ha="center", fontsize=9)
    plt.tight_layout()
save("fig08_sensitivity_coefficients.png")


# ─────────────────────────────────────────────────────────────────────
# Statistical summary table — exported as JSON for report
# ─────────────────────────────────────────────────────────────────────
def stats_block(values: list[float], label: str) -> dict:
    mu_val, hw = ci95(values)
    return {
        "metric": label,
        "mean":   round(mu_val, 4),
        "std":    round(float(np.std(values, ddof=1)), 4) if len(values) > 1 else 0.0,
        "min":    round(float(min(values)), 4),
        "max":    round(float(max(values)), 4),
        "ci95_lower": round(mu_val - hw, 4),
        "ci95_upper": round(mu_val + hw, 4),
    }

stat_summary = {
    "round_robin": [
        stats_block(rr_rt,  "Avg Response Time"),
        stats_block(rr_p95, "P95 Response Time"),
        stats_block([v*100 for v in rr_drop], "Drop Rate (%)"),
    ],
    "least_loaded": [
        stats_block(ll_rt,  "Avg Response Time"),
        stats_block(ll_p95, "P95 Response Time"),
        stats_block([v*100 for v in ll_drop], "Drop Rate (%)"),
    ],
    "direct_comparison": {
        "avg_response_time": {
            "round_robin_mean":   round(rr_rt_mean, 4),
            "least_loaded_mean":  round(ll_rt_mean, 4),
            "difference":         round(rr_rt_mean - ll_rt_mean, 4),
            "pct_improvement_LL": round((rr_rt_mean - ll_rt_mean) / rr_rt_mean * 100, 2),
        },
        "p95_response_time": {
            "round_robin_mean":   round(rr_p95_mean, 4),
            "least_loaded_mean":  round(ll_p95_mean, 4),
            "difference":         round(rr_p95_mean - ll_p95_mean, 4),
            "pct_improvement_LL": round((rr_p95_mean - ll_p95_mean) / rr_p95_mean * 100, 2),
        },
        "drop_rate_pct": {
            "round_robin_mean":   round(rr_drop_mean*100, 4),
            "least_loaded_mean":  round(ll_drop_mean*100, 4),
        },
    },
    "sensitivity_coefficients": {
        "lambda": round(s_lam, 4),
        "mu":     round(s_mu, 4),
        "N":      round(s_N, 4),
        "timeout": round(s_to, 4),
    },
}

with open(os.path.join(JSON_DIR, "STATISTICAL_SUMMARY.json"), "w") as f:
    json.dump(stat_summary, f, indent=2)
print("  saved STATISTICAL_SUMMARY.json")

print("\nAll experiments complete.")
print(f"Figures  → {FIG_DIR}")
print(f"JSON     → {JSON_DIR}\n")


