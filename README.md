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


## Scope:
**Included:**
- Simulation of client requests, server nodes, and a load balancer
- Stochastic arrival and service times
- Multiple load balancing strategies
- Random server failures and recovery
- Data collection and performance analysis
        
**Not Included:**
- Real network packet-level simulation
- Real cloud APIs
- Machine learning model training
- Item Physical hardware modeling

The simulation follows a **M/M/N queuing model**:

| Symbol | Meaning |
|--------|---------|
| λ | Poisson arrival rate (requests / time unit) |
| μ | Exponential service rate per server (1/μ = mean service time) |
| N | Number of server nodes |
| ρ | System utilisation = λ / (N · μ) |

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd data_center_sim

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

```bash
python src/main.py
```

The script runs two back-to-back experiments (Round Robin and Least Loaded)
and prints a metrics report for each:

```

  Intelligent Data Center Load & Fault-Tolerance Simulation

============================================================
  EXPERIMENT — algorithm: ROUND ROBIN
============================================================
[Sim] Starting simulation  λ=2.0, μ=1.5, ρ=0.444, duration=500.0, dt=1.0
...
==================================================
      DATA CENTER SIMULATION — METRICS REPORT
==================================================
  Total requests arrived  : 1007
  Completed requests      : 1003
  Dropped requests        : 4
  Drop rate               : 0.40%
  Avg response time       : 0.8341 time units
  Median response time    : 0.6203 time units
  95th pct response time  : 2.1847 time units
  Theoretical utilisation : ρ = 0.4444
==================================================
```

### Configuration

Edit the `CONFIG` dictionary at the top of `src/main.py` to change parameters:

```python
CONFIG = {
    "num_servers":     3,
    "arrival_rate":    2.0,    # λ
    "service_rate":    1.5,    # μ
    "sim_duration":  500.0,
    "dt":              1.0,
    "request_timeout": 50.0,   # set to float("inf") to disable drops
    "seed":           42,
}
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  SimulationEngine                    │
│  - Manages simulation clock (discrete time-steps)    │
│  - Generates Poisson arrivals each tick              │
│  - Calls LoadBalancer.dispatch() per new request     │
│  - Calls ServerNode.tick() for each server           │
│  - Passes completions/drops to MetricsCollector      │
└────────────┬───────────────────-───┬─────────────────┘
             │                       │
     ┌───────▼────-───┐    ┌─────────▼──────-────┐
     │  LoadBalancer  │    │   MetricsCollector  │
     │  - round_robin │    │  - completed count  │
     │  - least_loaded│    │  - dropped count    │
     └───────┬────────┘    │  - avg response time│
             │             │  - percentiles      │
    ┌────────▼──────────┐  └─────────────────────┘
    │  ServerNode       │
    │  - FIFO queue     │
    │  - service_rate μ │
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
| `SimulationEngine` | `simulation_engine.py` | Orchestrates the event loop; owns clock, servers, load balancer, and metrics |
| `LoadBalancer` | `load_balancer.py` | Routes requests to servers via Round Robin or Least Loaded |
| `ServerNode` | `server.py` | Maintains per-server queue; processes one request at a time |
| `ClientRequest` | `request.py` | Data object carrying timing attributes for a single request |
| `MetricsCollector` | `metrics.py` | Aggregates and reports simulation statistics |

---

## Current Status — Milestone 2

Core simulation implemented:

- [x] Poisson arrival process
- [x] Exponential service time distribution
- [x] Multiple server nodes with FIFO queues
- [x] Round Robin load balancing
- [x] Least Loaded load balancing (argmin queue length)
- [x] Request timeout / drop mechanism
- [x] Metrics: completed, dropped, avg/median/P95 response time
- [x] Theoretical utilisation ρ reported alongside empirical metrics

---

## Next Steps — Milestone 3+

- **Fault tolerance**: random server failures, restart logic, health-checks
- **Adaptive load balancing**: feedback-driven algorithm that switches strategy at runtime
- **Priority queues**: differentiate request classes (SLA tiers)
- **Visualisation**: matplotlib plots of queue length and response time over time
- **Parameter sweep**: automated sensitivity analysis across λ and μ values
- **Unit tests**: pytest suite covering each component in isolation

---

## Project Structure

```
data_center_sim/
├── src/
│   ├── main.py               ← entry point & configuration
│   ├── simulation_engine.py  ← discrete-time event loop
│   ├── load_balancer.py      ← Round Robin & Least Loaded
│   ├── server.py             ← ServerNode with FIFO queue
│   ├── request.py            ← ClientRequest data class
│   └── metrics.py            ← statistics collection & reporting
├── requirements.txt
├── README.md
└── .gitignore
