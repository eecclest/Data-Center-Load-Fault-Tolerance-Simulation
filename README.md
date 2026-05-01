# Intelligent Data Center Load and Fault-Tolerance Simulation

Repository for CS 4632 Modeling and Simulation

---

## Project Overview

**Project Title:** Intelligent Data Center Load and Fault-Tolerance Simulation  
**Domain:** Network Systems / Cloud Computing / Distributed Systems

Modern cloud data centers must handle unpredictable user traffic while
maintaining high availability despite server failures. This project
addresses three core questions:

- How do different load balancing algorithms affect system response time
  and throughput?
- How resilient is the system under random server failures?
- Which routing strategies minimize congestion and request loss under
  peak load conditions?

---

## Scope

**Included:**
- Discrete-time M/M/N queuing simulation built from scratch in Python
- Poisson arrival process and exponential service time distribution
- Two load balancing algorithms: Round Robin and Least Loaded
- Stochastic server failure and recovery model (two-state Markov chain)
- Request timeout enforcement and drop tracking
- Per-server utilization, queue depth time-series, and event logging
- Sensitivity analysis across four parameters with worked calculations
- Replicated scenario testing with 95% confidence intervals
- Algorithm comparison across ten independent replicates
- Erlang-C theoretical validation against closed-form M/M/N predictions
- Automated multi-run experiment execution with JSON and CSV export

**Not Included:**
- Real network packet-level simulation
- Real cloud APIs or physical hardware modeling
- Machine learning or adaptive routing algorithms

---

## Mathematical Model

The simulation follows an M/M/N queuing model:

| Symbol | Meaning |
|--------|---------|
| λ | Poisson arrival rate (requests / time unit) |
| μ | Exponential service rate per server (1/μ = mean service time) |
| N | Number of server nodes |
| ρ | System utilisation = λ / (N · μ) |
| pf | Server failure probability per tick = failure_rate · dt |
| pr | Server recovery probability per tick = recovery_rate · dt |

The system is stable when ρ = λ / (N · μ) < 1.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/Data_Center_Simulation.git
cd Data_Center_Simulation

# 2. Recommended: create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

### Single simulation run
```bash
python src/main.py
```
Runs both Round Robin and Least Loaded at baseline configuration and
prints a metrics report for each.

### Full analysis — all experiments, figures, and JSON output
```bash
python src/analyze.py
```
Executes all eight experiment groups (100+ runs), generates all ten
matplotlib figures, and exports structured JSON data including the
full statistical summary. All outputs are saved to `results/`.

---

## Configuration

All parameters are controlled through the `DEFAULTS` dictionary at the
top of `src/analyze.py`, or passed directly to `SimulationEngine`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_servers` | 3 | Number of ServerNode instances (N) |
| `arrival_rate` | 2.0 | Poisson arrival rate λ |
| `service_rate` | 1.5 | Exponential service rate μ per server |
| `simulation_time` | 500.0 | Total simulation duration (time units) |
| `dt` | 1.0 | Discrete time step size |
| `algorithm` | round_robin | `round_robin` or `least_loaded` |
| `request_timeout` | 50.0 | Max wait time before request is dropped |
| `failure_rate` | 0.0 | Per-server failure probability per tick |
| `recovery_rate` | 0.0 | Per-server recovery probability per tick |
| `seed` | 42 | Random seed for reproducibility |

---

## Sample Output
Running Group A: sensitivity - arrival rate...
[Sim] Starting simulation  lambda=2.0, mu=1.5, rho=0.444, duration=500.0, dt=1.0
[Sim] Servers: 3, Algorithm: least_loaded
[Sim] Simulation complete.
==================================================
DATA CENTER SIMULATION — METRICS REPORT
Total requests arrived  : 1004
Completed requests      : 1004
Dropped requests        : 0
Drop rate               : 0.00%
Avg response time       : 2.841 time units
Median response time    : 2.000 time units
95th pct response time  : 7.000 time units
Theoretical utilisation : rho = 0.4444

---

## Experiment Groups — Milestone 4 and 5

Eight experiment groups were executed via `src/analyze.py`:

| Group | Purpose | Runs |
|-------|---------|------|
| A | Sensitivity: arrival rate λ | 5 |
| B | Sensitivity: service rate μ | 5 |
| C | Sensitivity: server count N | 5 |
| D | Sensitivity: timeout threshold | 5 |
| E | Algorithm comparison: RR vs LL (10 reps each) | 20 |
| F | Scenario tests (5 scenarios × 10 reps each) | 50 |
| G | Extreme condition validation | 5 |
| H | Erlang-C theoretical validation | 6 |

---

## Data Collection

Three output files are generated per run in `results/json/`:

| File | Format | Contents |
|------|--------|----------|
| `run_XXX_summary.json` | JSON | Parameters, aggregate metrics, per-server breakdown |
| `run_XXX_timeseries.csv` | CSV | Per-tick queue length and active server count |
| `run_XXX_events.csv` | CSV | Timestamped arrivals, completions, drops, failures |

A single `STATISTICAL_SUMMARY.json` aggregates all results including
worked sensitivity calculations, scenario confidence intervals, algorithm
comparison statistics, and the Erlang-C validation table.

---

## Key Results — Milestone 5

### Sensitivity Analysis

| Parameter | Sensitivity Coefficient | Interpretation |
|-----------|------------------------|----------------|
| Arrival Rate (λ) | 4.98 | Very high — non-linear cliff at ρ = 0.667 |
| Service Rate (μ) | 0.35 | Moderate — diminishing returns |
| Server Count (N) | 0.14 | Low overall — critical threshold at N = 3 |
| Timeout (T) | 0.004 | Negligible at baseline |

### Algorithm Comparison (10 replicates each, baseline ρ = 0.444)

| Metric | Round Robin | Least Loaded | Improvement |
|--------|-------------|--------------|-------------|
| Avg Response Time | 3.551 | 3.013 | 15.2% |
| P95 Response Time | 9.400 | 6.900 | 26.6% |
| Drop Rate | 0.00% | 0.00% | N/A |

95% confidence intervals are non-overlapping, confirming statistical
significance.

### Scenario Analysis (10 replicates each, Least Loaded)

| Scenario | λ | N | ρ | Avg RT | Drop Rate |
|----------|---|---|---|--------|-----------|
| Light Load | 0.5 | 3 | 0.111 | 1.332 | 0.00% |
| Normal | 2.0 | 3 | 0.444 | 2.841 | 0.00% |
| Peak | 3.5 | 3 | 0.778 | 42.910 | 25.23% |
| Overload | 6.0 | 3 | 1.333 | 46.922 | 55.36% |
| Server Failure | 2.0 | 1 | 1.333 | 46.511 | 52.95% |

```

## Architecture Overview
┌──────────────────────────────────────────────────────┐
│                  SimulationEngine                    │
│  - Manages simulation clock (discrete time-steps)    │
│  - Applies failure/recovery model each tick          │
│  - Generates Poisson arrivals each tick              │
│  - Calls LoadBalancer.dispatch() per new request     │
│  - Calls ServerNode.tick() for each active server    │
│  - Passes completions/drops to MetricsCollector      │
│  - Writes JSON summary, timeseries CSV, event CSV    │
└────────────┬─────────────────────┬───────────────────┘
│                     │
┌───────▼────────┐  ┌─────────▼───────────┐
│  LoadBalancer  │  │   MetricsCollector  │
│  - round_robin │  │  - completed count  │
│  - least_loaded│  │  - dropped count    │
│  - active-only │  │  - failure count    │
│    filtering   │  │  - avg response time│
└───────┬────────┘  │  - P95 percentile   │
│                   └─────────────────────┘
┌────────▼──────────┐
│  ServerNode       │
│  - FIFO queue     │
│  - service_rate μ │
│  - is_active flag │
│  - failure model  │
│  - tick() method  │
└────────┬──────────┘
│
┌────────▼──────────┐
│   ClientRequest   │
│  - arrival_time   │
│  - service_time   │
│  - timeout        │
│  - response_time  │
└───────────────────┘

```
### Component Responsibilities

| Class | File | Role |
|-------|------|------|
| `SimulationEngine` | `simulation_engine.py` | Orchestrates tick loop, owns all components, exports output |
| `LoadBalancer` | `load_balancer.py` | Routes requests via Round Robin or Least Loaded |
| `ServerNode` | `server.py` | Manages FIFO queue, processes requests, handles failure state |
| `ClientRequest` | `request.py` | Data class carrying all timing attributes for a single request |
| `MetricsCollector` | `metrics.py` | Aggregates completions, drops, failures, and computes statistics |

See `docs/UML_Activity_Diagram_Updated.png` for the full activity diagram.

```

## Project Structure
Data_Center_Simulation/
├── src/
│   ├── main.py                ← entry point and baseline configuration
│   ├── simulation_engine.py   ← discrete-time tick loop and file export
│   ├── load_balancer.py       ← Round Robin and Least Loaded algorithms
│   ├── server.py              ← ServerNode with queue and failure model
│   ├── request.py             ← ClientRequest data class
│   ├── metrics.py             ← statistics collection and reporting
│   └── analyze.py             ← full analysis script (M4/M5)
├── results/
│   ├── figures/               ← generated matplotlib figures (PNG)
│   └── json/                  ← per-run JSON files and summary
├── docs/
│   └── UML_Activity_Diagram_Updated.png
├── examples/
│   ├── sample_config.json
│   └── example_output.json
├── config.json                ← default simulation parameters
├── run_experiments.py         ← M3 batch runner
├── requirements.txt
├── README.md
└── .gitignore

```

## Milestone Status

| Milestone | Status |
|-----------|--------|
| M1 — Project Proposal & Design | ✅ Complete |
| M2 — Core Simulation | ✅ Complete |
| M3 — Fault Tolerance & Testing | ✅ Complete |
| M4 — Sensitivity Analysis & Validation | ✅ Complete |
| M5 — Final Report & Presentation | ✅ Complete |

### Completed Features
- [x] Poisson arrival process and exponential service times
- [x] Round Robin and Least Loaded load balancing
- [x] Stochastic server failure and recovery model
- [x] Request timeout enforcement and drop tracking
- [x] Per-server utilization and queue depth tracking
- [x] JSON summary, timeseries CSV, and event log per run
- [x] Sensitivity analysis across four parameters with worked calculations
- [x] Replicated scenario testing with 95% confidence intervals
- [x] Algorithm comparison across ten independent replicates
- [x] Erlang-C closed-form theoretical validation
- [x] Ten matplotlib figures for report and presentation
- [x] Full statistical summary exported to JSON


## Dependencies

- Python 3.10+
- numpy >= 1.24.0
- matplotlib >= 3.7.0

## License

Developed for academic purposes at Kennesaw State University, CS 4632
Modeling and Simulation.
