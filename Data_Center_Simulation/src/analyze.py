"""
analyze.py  — Milestone 5 Analysis & Validation Script
========================================================
Changes from M4:
  - All hardcoded "Fig N" labels removed from plot titles (Overleaf handles numbering)
  - Group D (timeout) now has its own dedicated figure
  - Group F (scenarios) runs 10 replicates each with 95% CIs
  - Group H added: Erlang-C theoretical vs simulated comparison
  - Sensitivity worked calculations exported to JSON
  - CIs added to sensitivity and scenario summaries in STATISTICAL_SUMMARY.json
 
Experiment groups
  A  : Sensitivity - vary arrival rate (5 values)
  B  : Sensitivity - vary service rate (5 values)
  C  : Sensitivity - vary server count (5 values)
  D  : Sensitivity - vary request timeout (5 values)
  E  : Algorithm comparison RR vs LL (10 reps each)
  F  : Scenario tests - 10 replicates each with CIs
  G  : Extreme / validation runs
  H  : Erlang-C theoretical vs simulated comparison
"""
 
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
 
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
 
from simulation_engine import SimulationEngine
 
BASE     = os.path.join(os.path.dirname(__file__), "..", "results")
FIG_DIR  = os.path.join(BASE, "figures")
JSON_DIR = os.path.join(BASE, "json")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
 
DEFAULTS = dict(
    num_servers=3, arrival_rate=2.0, service_rate=1.5,
    simulation_time=500.0, dt=1.0, request_timeout=50.0,
    failure_rate=0.0, recovery_rate=0.0,
)
 
ALL_RESULTS = []
 
STYLE = {
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "figure.dpi":        130,
    "font.size":         10,
}
 
# ── Helpers ───────────────────────────────────────────────────────────
 
def run_sim(run_id, **kwargs):
    params = {**DEFAULTS, **kwargs, "run_id": run_id}
    eng = SimulationEngine(**params)
    eng.run()
    r = eng.results()
    with open(os.path.join(JSON_DIR, f"{run_id}.json"), "w") as f:
        json.dump(r, f, indent=2)
    ALL_RESULTS.append(r)
    return r
 
def run_repeated(base_id, n_reps, **kwargs):
    results = []
    for i in range(n_reps):
        r = run_sim(f"{base_id}_rep{i+1:02d}", seed=100 + i, **kwargs)
        results.append(r)
    return results
 
def extract_metric(results, key):
    return [r["metrics"][key] for r in results]
 
def ci95(values):
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mu = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if n > 1 else 0.0
    hw = 1.96 * sd / math.sqrt(n)
    return mu, hw
 
def stats_block(values, label):
    mu_val, hw = ci95(values)
    return {
        "metric":     label,
        "mean":       round(mu_val, 4),
        "std":        round(float(np.std(values, ddof=1)), 4) if len(values) > 1 else 0.0,
        "min":        round(float(min(values)), 4),
        "max":        round(float(max(values)), 4),
        "ci95_lower": round(mu_val - hw, 4),
        "ci95_upper": round(mu_val + hw, 4),
    }
 
def save(name):
    path = os.path.join(FIG_DIR, name)
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"  saved {name}")
    return path
 
# ── Erlang-C ──────────────────────────────────────────────────────────
 
def erlang_c(lam, mu, n):
    rho = lam / mu
    a   = rho / n
    if a >= 1.0:
        return 1.0
    numerator   = (rho ** n / math.factorial(n)) * (1.0 / (1.0 - a))
    sum_terms   = sum((rho ** k) / math.factorial(k) for k in range(n))
    denominator = sum_terms + numerator
    return numerator / denominator
 
def theoretical_w(lam, mu, n):
    a = (lam / mu) / n
    if a >= 1.0:
        return float("inf")
    c  = erlang_c(lam, mu, n)
    wq = c / (n * mu - lam)
    return wq + 1.0 / mu
 
# ── Sensitivity worked calculation ────────────────────────────────────
 
def sens_coeff_worked(param_name, inputs, outputs):
    x0, x1 = float(inputs[0]),  float(inputs[-1])
    y0, y1 = float(outputs[0]), float(outputs[-1])
    pct_in  = (x1 - x0) / x0 * 100
    pct_out = (y1 - y0) / (y0 + 1e-9) * 100
    coeff   = abs(pct_out / pct_in) if pct_in != 0 else 0.0
    return {
        "parameter":               param_name,
        "input_start":             round(x0, 4),
        "input_end":               round(x1, 4),
        "pct_delta_input":         round(pct_in,  2),
        "output_start_avg_rt":     round(y0, 4),
        "output_end_avg_rt":       round(y1, 4),
        "pct_delta_output":        round(pct_out, 2),
        "sensitivity_coefficient": round(coeff, 4),
    }
 
# ── Group A: Sensitivity - arrival rate ───────────────────────────────
print("Running Group A: sensitivity - arrival rate...")
lambda_values = [0.5, 1.0, 2.0, 3.0, 4.0]
sens_lambda = []
for idx, lam in enumerate(lambda_values):
    r = run_sim(f"A_{idx+1:03d}", arrival_rate=lam, algorithm="round_robin", seed=42)
    sens_lambda.append(r)
 
# ── Group B: Sensitivity - service rate ───────────────────────────────
print("Running Group B: sensitivity - service rate...")
mu_values = [0.8, 1.0, 1.5, 2.0, 3.0]
sens_mu = []
for idx, mu in enumerate(mu_values):
    r = run_sim(f"B_{idx+1:03d}", service_rate=mu, algorithm="round_robin", seed=42)
    sens_mu.append(r)
 
# ── Group C: Sensitivity - server count ───────────────────────────────
print("Running Group C: sensitivity - server count...")
server_counts = [1, 2, 3, 5, 8]
sens_N = []
for idx, n in enumerate(server_counts):
    r = run_sim(f"C_{idx+1:03d}", num_servers=n, algorithm="round_robin", seed=42)
    sens_N.append(r)
 
# ── Group D: Sensitivity - timeout ────────────────────────────────────
print("Running Group D: sensitivity - timeout...")
timeout_values = [5.0, 10.0, 25.0, 50.0, 200.0]
sens_timeout = []
for idx, t in enumerate(timeout_values):
    r = run_sim(f"D_{idx+1:03d}", request_timeout=t, algorithm="round_robin", seed=42)
    sens_timeout.append(r)
 
# ── Group E: Algorithm comparison ─────────────────────────────────────
print("Running Group E: algorithm comparison (10 reps each)...")
rr_reps = run_repeated("E_RR", 10, algorithm="round_robin")
ll_reps = run_repeated("E_LL", 10, algorithm="least_loaded")
 
rr_rt    = extract_metric(rr_reps, "avg_response_time")
ll_rt    = extract_metric(ll_reps, "avg_response_time")
rr_p95   = extract_metric(rr_reps, "p95_response_time")
ll_p95   = extract_metric(ll_reps, "p95_response_time")
rr_drop  = extract_metric(rr_reps, "drop_rate")
ll_drop  = extract_metric(ll_reps, "drop_rate")
 
rr_rt_mean,   rr_rt_hw   = ci95(rr_rt)
ll_rt_mean,   ll_rt_hw   = ci95(ll_rt)
rr_p95_mean,  rr_p95_hw  = ci95(rr_p95)
ll_p95_mean,  ll_p95_hw  = ci95(ll_p95)
rr_drop_mean, rr_drop_hw = ci95(rr_drop)
ll_drop_mean, ll_drop_hw = ci95(ll_drop)
 
# ── Group F: Scenario tests - 10 reps each ────────────────────────────
print("Running Group F: scenario tests (10 reps each)...")
scenario_defs = [
    ("F_light",    dict(arrival_rate=0.5, service_rate=1.5, num_servers=3)),
    ("F_normal",   dict(arrival_rate=2.0, service_rate=1.5, num_servers=3)),
    ("F_peak",     dict(arrival_rate=3.5, service_rate=1.5, num_servers=3)),
    ("F_overload", dict(arrival_rate=6.0, service_rate=1.5, num_servers=3)),
    ("F_failure",  dict(arrival_rate=2.0, service_rate=1.5, num_servers=1)),
]
scenario_labels = ["Light (lam=0.5)", "Normal (lam=2.0)", "Peak (lam=3.5)",
                   "Overload (lam=6.0)", "Failure (N=1)"]
 
scenario_reps = []
for base_id, kw in scenario_defs:
    reps = run_repeated(base_id, 10, algorithm="least_loaded", **kw)
    scenario_reps.append(reps)
 
scenario_rt_stats  = [stats_block(extract_metric(r, "avg_response_time"), "Avg RT")
                      for r in scenario_reps]
scenario_dr_stats  = [stats_block([v*100 for v in extract_metric(r, "drop_rate")], "Drop Rate (%)")
                      for r in scenario_reps]
scenario_p95_stats = [stats_block(extract_metric(r, "p95_response_time"), "P95 RT")
                      for r in scenario_reps]
 
# ── Group G: Extreme conditions ───────────────────────────────────────
print("Running Group G: validation / extreme conditions...")
extreme_cases = [
    ("G_001_zero_load",     dict(arrival_rate=0.01, service_rate=1.5, num_servers=3)),
    ("G_002_overload",      dict(arrival_rate=9.0,  service_rate=1.5, num_servers=3)),
    ("G_003_single_server", dict(arrival_rate=1.0,  service_rate=1.5, num_servers=1)),
    ("G_004_high_mu",       dict(arrival_rate=2.0,  service_rate=5.0, num_servers=3)),
    ("G_005_tight_timeout", dict(arrival_rate=2.0,  service_rate=1.5, num_servers=3,
                                  request_timeout=2.0)),
]
extreme_results = []
for rid, kw in extreme_cases:
    r = run_sim(rid, algorithm="round_robin", seed=42, **kw)
    extreme_results.append(r)
 
# ── Group H: Erlang-C validation ──────────────────────────────────────
print("Computing Group H: Erlang-C theoretical validation...")
erlang_cases = [
    dict(lam=0.5, mu=1.5, n=3),
    dict(lam=1.0, mu=1.5, n=3),
    dict(lam=2.0, mu=1.5, n=3),
    dict(lam=1.0, mu=1.5, n=1),
    dict(lam=2.0, mu=3.0, n=3),
    dict(lam=2.0, mu=2.0, n=3),
]
erlang_table = []
for case in erlang_cases:
    lam, mu, n = case["lam"], case["mu"], case["n"]
    rho    = lam / (n * mu)
    theo_w = theoretical_w(lam, mu, n)
    rid    = f"H_lam{lam}_mu{mu}_N{n}"
    sim_r  = run_sim(rid, arrival_rate=lam, service_rate=mu, num_servers=n,
                     algorithm="round_robin", seed=42)
    sim_w  = sim_r["metrics"]["avg_response_time"]
    pct_diff = abs(sim_w - theo_w) / theo_w * 100 if theo_w != float("inf") else None
    erlang_table.append({
        "lam": lam, "mu": mu, "N": n,
        "rho":           round(rho, 4),
        "theoretical_W": round(theo_w, 4) if theo_w != float("inf") else "inf",
        "simulated_W":   round(sim_w, 4),
        "pct_diff":      round(pct_diff, 2) if pct_diff is not None else "N/A",
    })
 
# ── Worked sensitivity calculations ───────────────────────────────────
rt_lam = [r["metrics"]["avg_response_time"] for r in sens_lambda]
rt_mu2 = [r["metrics"]["avg_response_time"] for r in sens_mu]
rt_N2  = [r["metrics"]["avg_response_time"] for r in sens_N]
rt_to  = [r["metrics"]["avg_response_time"] for r in sens_timeout]
 
worked_lam = sens_coeff_worked("Arrival Rate (lambda)", lambda_values, rt_lam)
worked_mu  = sens_coeff_worked("Service Rate (mu)",     mu_values,     rt_mu2)
worked_N   = sens_coeff_worked("Server Count (N)",      server_counts, rt_N2)
worked_to  = sens_coeff_worked("Timeout (T)",           timeout_values, rt_to)
 
s_lam = worked_lam["sensitivity_coefficient"]
s_mu  = worked_mu["sensitivity_coefficient"]
s_N   = worked_N["sensitivity_coefficient"]
s_to  = worked_to["sensitivity_coefficient"]
 
# ── FIGURES ───────────────────────────────────────────────────────────
 
# Sensitivity: lambda
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    dr_vals  = [r["metrics"]["drop_rate"] * 100 for r in sens_lambda]
    rho_vals = [r["metrics"]["theoretical_utilization"] for r in sens_lambda]
    ax1.plot(lambda_values, rt_lam, "o-", color="#2563EB", linewidth=2)
    ax1.set_xlabel("Arrival Rate (req/time-unit)")
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Avg Response Time vs Arrival Rate")
    for x, y, rho in zip(lambda_values, rt_lam, rho_vals):
        ax1.annotate(f"rho={rho:.2f}", (x, y), textcoords="offset points",
                     xytext=(0, 7), ha="center", fontsize=8, color="#6B7280")
    ax2.bar(lambda_values, dr_vals, color="#EF4444", alpha=0.7, width=0.3)
    ax2.set_xlabel("Arrival Rate (req/time-unit)")
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Drop Rate vs Arrival Rate")
    fig.suptitle("Sensitivity Analysis: Arrival Rate", fontweight="bold")
    plt.tight_layout()
save("fig_sensitivity_lambda.png")
 
# Sensitivity: mu
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    p95_mu  = [r["metrics"]["p95_response_time"] for r in sens_mu]
    util_mu = [r["metrics"]["theoretical_utilization"] for r in sens_mu]
    ax1.plot(mu_values, rt_mu2,  "s-",  color="#059669", linewidth=2, label="Mean RT")
    ax1.plot(mu_values, p95_mu,  "^--", color="#D97706", linewidth=2, label="P95 RT")
    ax1.set_xlabel("Service Rate (completions/time-unit)")
    ax1.set_ylabel("Response Time (time-units)")
    ax1.set_title("Response Time vs Service Rate")
    ax1.legend()
    ax2.plot(mu_values, util_mu, "o-", color="#7C3AED", linewidth=2)
    ax2.axhline(1.0, linestyle="--", color="red", alpha=0.5, label="rho=1 (saturation)")
    ax2.set_xlabel("Service Rate")
    ax2.set_ylabel("Theoretical Utilization")
    ax2.set_title("Utilization vs Service Rate")
    ax2.legend()
    fig.suptitle("Sensitivity Analysis: Service Rate", fontweight="bold")
    plt.tight_layout()
save("fig_sensitivity_mu.png")
 
# Sensitivity: N
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    dr_N = [r["metrics"]["drop_rate"] * 100 for r in sens_N]
    ax1.plot(server_counts, rt_N2, "o-", color="#0891B2", linewidth=2)
    ax1.set_xlabel("Number of Servers")
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Response Time vs Server Count")
    ax2.plot(server_counts, dr_N, "s--", color="#DC2626", linewidth=2)
    ax2.set_xlabel("Number of Servers")
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Drop Rate vs Server Count")
    fig.suptitle("Sensitivity Analysis: Number of Servers", fontweight="bold")
    plt.tight_layout()
save("fig_sensitivity_N.png")
 
# Sensitivity: timeout
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    dr_to = [r["metrics"]["drop_rate"] * 100 for r in sens_timeout]
    ax1.plot(timeout_values, rt_to, "o-", color="#7C3AED", linewidth=2)
    ax1.set_xlabel("Timeout Threshold (time-units)")
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Response Time vs Timeout Threshold")
    ax2.plot(timeout_values, dr_to, "s--", color="#DC2626", linewidth=2)
    ax2.set_xlabel("Timeout Threshold (time-units)")
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Drop Rate vs Timeout Threshold")
    fig.suptitle("Sensitivity Analysis: Request Timeout", fontweight="bold")
    plt.tight_layout()
save("fig_sensitivity_timeout.png")
 
# Sensitivity coefficients bar chart
with plt.rc_context(STYLE):
    params_lbl = ["Arrival Rate", "Service Rate", "Server Count", "Timeout"]
    s_vals     = [s_lam, s_mu, s_N, s_to]
    bar_c      = ["#EF4444" if v > 1 else "#2563EB" for v in s_vals]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(params_lbl, s_vals, color=bar_c, alpha=0.8)
    ax.axhline(1.0, linestyle="--", color="gray", alpha=0.6, label="Sensitivity = 1.0")
    ax.set_ylabel("Sensitivity Coefficient  (|% delta output / % delta input|)")
    ax.set_title("Sensitivity Coefficients for Avg Response Time")
    ax.legend()
    for bar, v in zip(bars, s_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{v:.2f}", ha="center", fontsize=9)
    plt.tight_layout()
save("fig_sensitivity_coefficients.png")
 
# Algorithm comparison box plots
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
        ax.set_title(label)
    fig.suptitle("Algorithm Comparison: Round Robin vs Least Loaded (10 reps each)",
                 fontweight="bold")
    plt.tight_layout()
save("fig_algorithm_comparison.png")
 
# Scenario comparison with error bars
with plt.rc_context(STYLE):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    bar_colors = ["#10B981", "#2563EB", "#F59E0B", "#EF4444", "#8B5CF6"]
    x = range(len(scenario_defs))
    rt_means = [s["mean"]                  for s in scenario_rt_stats]
    rt_hws   = [s["mean"] - s["ci95_lower"] for s in scenario_rt_stats]
    dr_means = [s["mean"]                  for s in scenario_dr_stats]
    dr_hws   = [s["mean"] - s["ci95_lower"] for s in scenario_dr_stats]
    ax1.bar(x, rt_means, yerr=rt_hws, color=bar_colors, alpha=0.8,
            capsize=5, error_kw=dict(ecolor="black", linewidth=1.5))
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(scenario_labels, fontsize=8)
    ax1.set_ylabel("Avg Response Time (time-units)")
    ax1.set_title("Response Time by Scenario (mean +/- 95% CI)")
    ax2.bar(x, dr_means, yerr=dr_hws, color=bar_colors, alpha=0.8,
            capsize=5, error_kw=dict(ecolor="black", linewidth=1.5))
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(scenario_labels, fontsize=8)
    ax2.set_ylabel("Drop Rate (%)")
    ax2.set_title("Drop Rate by Scenario (mean +/- 95% CI)")
    fig.suptitle("Scenario Analysis Results (10 replicates each)", fontweight="bold")
    plt.tight_layout()
save("fig_scenario_comparison.png")
 
# Per-server utilization heatmap
with plt.rc_context(STYLE):
    eng_rr = SimulationEngine(algorithm="round_robin",  run_id="heatmap_rr", seed=42, **DEFAULTS)
    eng_ll = SimulationEngine(algorithm="least_loaded", run_id="heatmap_ll", seed=42, **DEFAULTS)
    eng_rr.run()
    eng_ll.run()
    psu_rr    = eng_rr.per_server_utilization()
    psu_ll    = eng_ll.per_server_utilization()
    data_heat = np.array([psu_rr, psu_ll])
    fig, ax = plt.subplots(figsize=(6, 3))
    im = ax.imshow(data_heat, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(psu_rr)))
    ax.set_xticklabels([f"Server {i}" for i in range(len(psu_rr))])
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Round Robin", "Least Loaded"])
    plt.colorbar(im, ax=ax, label="Empirical Utilization")
    for row in range(2):
        for col in range(len(psu_rr)):
            val = data_heat[row, col]
            ax.text(col, row, f"{val:.3f}", ha="center", va="center",
                    fontsize=11, color="black" if val < 0.6 else "white")
    ax.set_title("Per-Server Empirical Utilization: Round Robin vs Least Loaded")
    plt.tight_layout()
save("fig_perserver_utilization.png")
 
# Queue depth over time
with plt.rc_context(STYLE):
    T      = 150
    qd_rr  = eng_rr.queue_depth_history()
    qd_ll  = eng_ll.queue_depth_history()
    tot_rr = [sum(qd_rr[s][t] for s in range(len(qd_rr))) for t in range(T)]
    tot_ll = [sum(qd_ll[s][t] for s in range(len(qd_ll))) for t in range(T)]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(T), tot_rr, label="Round Robin",  color="#2563EB", linewidth=1.5)
    ax.plot(range(T), tot_ll, label="Least Loaded", color="#059669", linewidth=1.5)
    ax.set_xlabel("Simulation Tick")
    ax.set_ylabel("Total Queue Depth (all servers)")
    ax.set_title("Queue Depth Over Time: Round Robin vs Least Loaded (first 150 ticks)")
    ax.legend()
    plt.tight_layout()
save("fig_queue_depth_time.png")
 
# Erlang-C: simulated vs theoretical W
with plt.rc_context(STYLE):
    stable     = [e for e in erlang_table if e["theoretical_W"] != "inf"]
    rho_vals_e = [e["rho"]           for e in stable]
    theo_vals  = [e["theoretical_W"] for e in stable]
    sim_vals_e = [e["simulated_W"]   for e in stable]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(rho_vals_e, theo_vals,  "o--", color="#7C3AED", linewidth=2,
            label="Theoretical W (Erlang-C M/M/N)")
    ax.plot(rho_vals_e, sim_vals_e, "s-",  color="#059669", linewidth=2,
            label="Simulated W")
    ax.set_xlabel("System Utilization (rho)")
    ax.set_ylabel("Mean Sojourn Time W (time-units)")
    ax.set_title("Simulated vs Theoretical Mean Sojourn Time (Erlang-C Validation)")
    ax.legend()
    plt.tight_layout()
save("fig_erlang_validation.png")
 
# ── STATISTICAL SUMMARY JSON ──────────────────────────────────────────
 
scenario_names = ["Light", "Normal", "Peak", "Overload", "Failure"]
scenario_summary = []
for name, rt_s, dr_s, p95_s in zip(
        scenario_names, scenario_rt_stats, scenario_dr_stats, scenario_p95_stats):
    scenario_summary.append({
        "scenario":          name,
        "avg_response_time": rt_s,
        "p95_response_time": p95_s,
        "drop_rate_pct":     dr_s,
    })
 
stat_summary = {
    "sensitivity": {
        "worked_calculations": [worked_lam, worked_mu, worked_N, worked_to],
        "coefficients": {"lambda": s_lam, "mu": s_mu, "N": s_N, "timeout": s_to},
        "sweep_stats": {
            "lambda":  [{"lambda": lam,
                         "avg_rt":    round(r["metrics"]["avg_response_time"], 4),
                         "drop_rate": round(r["metrics"]["drop_rate"] * 100, 4),
                         "rho":       round(r["metrics"]["theoretical_utilization"], 4)}
                        for lam, r in zip(lambda_values, sens_lambda)],
            "mu":      [{"mu": mu,
                         "avg_rt":    round(r["metrics"]["avg_response_time"], 4),
                         "drop_rate": round(r["metrics"]["drop_rate"] * 100, 4),
                         "rho":       round(r["metrics"]["theoretical_utilization"], 4)}
                        for mu, r in zip(mu_values, sens_mu)],
            "N":       [{"N": n,
                         "avg_rt":    round(r["metrics"]["avg_response_time"], 4),
                         "drop_rate": round(r["metrics"]["drop_rate"] * 100, 4),
                         "rho":       round(r["metrics"]["theoretical_utilization"], 4)}
                        for n, r in zip(server_counts, sens_N)],
            "timeout": [{"timeout":   t,
                         "avg_rt":    round(r["metrics"]["avg_response_time"], 4),
                         "drop_rate": round(r["metrics"]["drop_rate"] * 100, 4)}
                        for t, r in zip(timeout_values, sens_timeout)],
        },
    },
    "scenarios": scenario_summary,
    "algorithms": {
        "round_robin":  [stats_block(rr_rt,  "Avg Response Time"),
                         stats_block(rr_p95, "P95 Response Time"),
                         stats_block([v*100 for v in rr_drop], "Drop Rate (%)")],
        "least_loaded": [stats_block(ll_rt,  "Avg Response Time"),
                         stats_block(ll_p95, "P95 Response Time"),
                         stats_block([v*100 for v in ll_drop], "Drop Rate (%)")],
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
                "round_robin_mean":  round(rr_drop_mean * 100, 4),
                "least_loaded_mean": round(ll_drop_mean * 100, 4),
            },
        },
    },
    "erlang_validation": erlang_table,
}
 
with open(os.path.join(JSON_DIR, "STATISTICAL_SUMMARY.json"), "w") as f:
    json.dump(stat_summary, f, indent=2)
print("  saved STATISTICAL_SUMMARY.json")
 
print("\nAll experiments complete.")
print(f"Figures  -> {FIG_DIR}")
print(f"JSON     -> {JSON_DIR}\n")