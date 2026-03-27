# Data-Center-Load-Fault-Tolerance-Simulation
The repository for my CS4632 Modeling and Simulation Project

## Project Overview

Project Title:
Intelligent Data Center Load \& Fault-Tolerance Simulation

## Domain:
Network Systems / Cloud Computing / Distributed Systems

## Problem Statement:
Modern cloud data centers must handle unpredictable user traffic while maintaining high availability despite server failures. My project seeks to answer the following questions
- How do different load balancing algorithms affect system response time and throughput?
- How resilient is the system under random server failures?
- Which routing strategies minimize congestion and request lost under peak load conditions?


## Scope

**Included:**
- Simulation of client requests, server nodes, and a load balancer
- Stochastic arrival and service times (Poisson arrivals, exponential service)
- Multiple load balancing strategies (Round Robin, Least Loaded)
- Probabilistic server failures and exponential recovery times
- Comprehensive data collection and performance analysis
- Automated multi-run experiment execution with CSV/JSON export

**Not Included:**
- Real network packet-level simulation
- Real cloud APIs
- Machine learning model training
- Physical hardware modeling
- Adaptive routing algorithm (deferred to M4)

---

## Mathematical Model

The simulation follows an **M/M/N queueing model**:

| Symbol | Meaning |
|--------|---------|
| λ | Poisson arrival rate (requests / time unit) |
| μ | Exponential service rate per server (1/μ = mean service time) |
| N | Number of server nodes |
| ρ | System utilisation = λ / (N · μ) |
| f_r | Server failure rate (Bernoulli per tick) |
| r_r | Recovery rate — recovery time ~ Exp(r_r) |

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd Data_Center_Simulation

# 2. (Recommended) Create a virtual environment
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
Runs both Round Robin and Least Loaded experiments back-to-back using `config.json` and prints a metrics report for each.

### Full experiment batch (10 runs)
```bash
python run_experiments.py
```
Executes all 10 parameterized runs, writes per-run config files, and saves results to `results/`.

---

## Configuration

Edit `config.json` in the project root to change parameters:

```json
{
  "num_servers": 5,
  "arrival_rate": 2.0,
  "service_rate": 3.0,
  "failure_rate": 0.1,
  "recovery_rate": 0.5,
  "simulation_time": 1000.0,
  "dt": 1.0,
  "algorithm": "least_loaded",
  "seed": 42
}
```

| Parameter | Description |
|-----------|-------------|
| `num_servers` | Number of ServerNode instances |
| `arrival_rate` | λ — mean requests per time unit (Poisson) |
| `service_rate` | μ — exponential service rate per server |
| `failure_rate` | Probability of server failure per tick |
| `recovery_rate` | Rate parameter for exponential recovery time |
| `simulation_time` | Total simulation duration (time units) |
| `dt` | Discrete time step size |
| `algorithm` | `"round_robin"` or `"least_loaded"` |
| `seed` | Random seed for reproducibility |

---

## Sample Output

```
[Sim] Starting simulation  lambda=2.0, mu=3.0, rho=0.133, duration=1000.0, dt=1.0
[Sim] Servers: 5, Algorithm: least_loaded
[Sim] Simulation complete.

==================================================
       Data Center Simulation - Metrics Report
==================================================
  Total requests arrived  : 2003
  Completed requests      : 2003
  Dropped requests        : 0
  Drop rate               : 0.00%
  Server failures         : 384
  Avg response time       : 1.6601 time units
  Median response time    : 1.0000 time units
  95th percentile         : 5.0000 time units
  Theoretical utilisation : rho = 0.1333
==================================================
```

---

## Experiment Runs — Milestone 3

10 distinct simulation runs were completed via `run_experiments.py`, varying parameters across arrival rate, service rate, failure rate, recovery rate, and algorithm:

| Run | Purpose | Key Parameter Change | Status |
|-----|---------|----------------------|--------|
| 001 | Baseline low load | λ = 2.0 (default) | ✅ Complete |
| 002 | Moderate load | λ = 4.0 | ✅ Complete |
| 003 | Fast servers | μ = 5.0 | ✅ Complete |
| 004 | High failure rate | failure_rate = 0.2 | ✅ Complete |
| 005 | Fast recovery | recovery_rate = 1.0 | ✅ Complete |
| 006 | Round Robin | algorithm = round_robin | ✅ Complete |
| 007 | Least Loaded | algorithm = least_loaded | ✅ Complete |
| 008 | High load + failures | λ = 6.0, failure_rate = 0.3 | ✅ Complete |
| 009 | Heavy load | λ = 8.0 | ✅ Complete |
| 010 | Slow servers | μ = 2.0 | ✅ Complete |

---

## Data Collection

Three output files are generated per run in the `results/` directory:

| File | Format | Contents |
|------|--------|----------|
| `run_XXX_summary.json` | JSON | Aggregate statistics (completed, dropped, avg RT, P95, failures) |
| `run_XXX_timeseries.csv` | CSV | Per-tick snapshots: time, queue_length, active_servers |
| `run_XXX_events.csv` | CSV | Timestamped log of every arrival, completion, drop, failure, recovery |

### Metrics Tracked
- Completed and dropped request counts
- Drop rate
- Average response time
- P95 (95th percentile) response time
- Total server failure events

---

## Key Results — Milestone 3

| Metric | Round Robin (Run 006) | Least Loaded (Run 007) |
|--------|-----------------------|------------------------|
| Completed Requests | 3968 | 3994 |
| Avg Response Time | 301.49 | 293.37 |
| P95 Response Time | 569.0 | 564.0 |
| Drop Rate | 0.00% | 0.00% |
| Server Failures | 234 | 242 |

**Least Loaded outperforms Round Robin by ~2.7% in average response time** and achieves lower tail latency, confirming that queue-aware dispatching is more resilient under server failure conditions.

---

## Architecture Overview

```
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
             │           └─────────────────────┘
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
| `SimulationEngine` | `simulation_engine.py` | Orchestrates event loop; owns clock, servers, load balancer, metrics, and file export |
| `LoadBalancer` | `load_balancer.py` | Routes requests to active servers via Round Robin or Least Loaded |
| `ServerNode` | `server.py` | Maintains per-server queue; processes requests; handles failure/recovery state |
| `ClientRequest` | `request.py` | Data object carrying timing attributes for a single request |
| `MetricsCollector` | `metrics.py` | Aggregates statistics including failures; exports `compute_summary()` |

---

## Project Structure

```
Data_Center_Simulation/
├── src/
│   ├── main.py                ← entry point, CONFIG, run_experiment()
│   ├── simulation_engine.py   ← discrete-time event loop + file export
│   ├── load_balancer.py       ← Round Robin & Least Loaded (active-only)
│   ├── server.py              ← ServerNode with FIFO queue + failure model
│   ├── request.py             ← ClientRequest data class
│   └── metrics.py             ← statistics collection, compute_summary()
├── results/                   ← auto-generated output files (gitignored)
│   ├── run_001_summary.json
│   ├── run_001_timeseries.csv
│   ├── run_001_events.csv
│   └── ...
├── config.json                ← default simulation parameters
├── run_experiments.py         ← batch runner for all 10 experiment runs
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Milestone Status

| Milestone | Status |
|-----------|--------|
| M1 — Project Proposal | ✅ Complete |
| M2 — Core Simulation | ✅ Complete |
| M3 — Full Implementation & Testing | ✅ Complete |
| M4 — Sensitivity Analysis & Validation | 🔜 Upcoming |
| M5 — Final Presentation & Report | 🔜 Upcoming |

### M3 Completed Features
- [x] Probabilistic server failure model (Bernoulli per tick)
- [x] Exponential recovery time distribution
- [x] Active-server filtering in both load balancing algorithms
- [x] JSON summary export per run
- [x] Timeseries CSV export per run
- [x] Event log CSV export per run
- [x] 10 parameterized experiment runs via `run_experiments.py`
- [x] `compute_summary()` and `record_failure()` in MetricsCollector

### Next Steps — Milestone 4
- Sensitivity analysis: failure_rate sweep (0.01 → 0.3)
- High-load stress testing at ρ > 0.7
- Adaptive routing algorithm implementation
- matplotlib visualizations of queue length and response time over time
- pytest unit test suite for each component
