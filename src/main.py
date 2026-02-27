"""
main.py
Entry point for the Intelligent Data Center Load and Fault-Tolerance Simulation.

Run:
    python src/main.py

Two simulation runs are executed back to back so the results can be comapred 
directly in the console output.
"""

import sys
import os

# Allow imports from the same src/ directory
sys.path.insert(0, os.path.dirname(__file__))

from simulation_engine import SimulationEngine

# ----------------------------------------------------------------------------------
# Simulation configuration
# ----------------------------------------------------------------------------------
CONFIG = {
    "num_servers": 3,
    "arrival_rate": 2.0,        # λ - requests per time unit
    "service_rate": 1.5,        # μ - service completions per time unit per server
    "sim_duration": 500.0,      # total simulation time
    "dt": 1.0,                  # discrete time step size
    "request_timeout": 50.0,    # drop requests waiting longer than this
    "seed": 42,                 # for reproducibility
}


def run_experiment(algorithm: str) -> None:
    """Run a single simulation experiment with the given load-balancing algorithms."""
    print("=" * 60)
    print(f"  Experiment - algorithm: {algorithm.upper().replace('_', ' ')}")
    print("=" * 60)

    engine = SimulationEngine(algorithm=algorithm, **CONFIG)
    engine.run()
    engine.summary()
    print()


def main() -> None:
    print("\n Intelligent Data Center Load & Fault-Tolerance Simulation \n")
    
    # Run with both supported algorithms for comparison
    for algo in ("round_robin", "least_loaded"):
        run_experiment(algo)


if __name__ == "__main__":
    main()
    
