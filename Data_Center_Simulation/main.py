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
import json

# Load config
config_path = sys.argv[2] if len(sys.argv) > 2 else "config.json"
with open("config.json") as f:
    config = json.load(f)

print(f"[Debug] Loaded config: arrival_rate={config['arrival_rate']}, rho={config['arrival_rate'] / (config['num_servers'] * config['service_rate']):.3f}")
# Run ID
run_id = sys.argv[1] if len(sys.argv) > 1 else "000"

# Allow imports from the same src/ directory
sys.path.insert(0, os.path.dirname(__file__))

from simulation_engine import SimulationEngine

# ----------------------------------------------------------------------------------
# Simulation configuration
# ----------------------------------------------------------------------------------
CONFIG = {
    
    "arrival_rate" : config["arrival_rate"],
    "service_rate" : config["service_rate"],
    "failure_rate" : config["failure_rate"],
    "recovery_rate" : config["recovery_rate"],
    "num_servers" : config["num_servers"],
    "simulation_time" : config["simulation_time"],
    "algorithm" : config["algorithm"],
    "seed" : config["seed"],

}

sim = SimulationEngine(
    num_servers=CONFIG["num_servers"],
    arrival_rate=CONFIG["arrival_rate"],
    service_rate=CONFIG["service_rate"],
    failure_rate=CONFIG["failure_rate"],
    recovery_rate=CONFIG["recovery_rate"],
    algorithm=CONFIG["algorithm"],
    simulation_time=CONFIG["simulation_time"],
    seed=CONFIG["seed"],
    run_id=run_id   
)

sim.run()

def run_experiment(algorithm: str) -> None:
    print("=" * 60)
    print(f"  Experiment - algorithm: {algorithm.upper().replace('_', ' ')}")
    print("=" * 60)

    cfg = {**CONFIG, "algorithm": algorithm}    # ← override algorithm cleanly
    engine = SimulationEngine(**cfg, run_id=run_id)
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
    