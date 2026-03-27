import os
import json
import subprocess

runs = [
    {"id": "001", "arrival_rate": 2.0},
    {"id": "002", "arrival_rate": 4.0},
    {"id": "003", "service_rate": 5.0},
    {"id": "004", "failure_rate": 0.2},
    {"id": "005", "recovery_rate": 1.0},
    {"id": "006", "algorithm": "round_robin"},
    {"id": "007", "algorithm": "least_loaded"},
    {"id": "008", "arrival_rate": 6.0, "failure_rate": 0.3},
    {"id": "009", "arrival_rate": 8.0},
    {"id": "010", "service_rate": 2.0},
]

for run in runs:
    config = {
        "num_servers": 5,
        "arrival_rate": run.get("arrival_rate", 2.0),
        "service_rate": run.get("service_rate", 3.0),
        "failure_rate": run.get("failure_rate", 0.1),
        "recovery_rate": run.get("recovery_rate", 0.5),
        "simulation_time": 1000,
        "algorithm": run.get("algorithm", "least_loaded"),
        "seed": 42,
    }

    # ← WRITE config with run ID in filename to avoid overwriting between runs
    config_path = f"config_{run['id']}.json"
    with open(config_path, "w") as f:
        json.dump(config, f)

    # ← REPLACE os.system with subprocess for error handling
    result = subprocess.run(
        ["python", "src/main.py", run["id"], config_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[ERROR] Run {run['id']} failed:\n{result.stderr}")
    else:
        print(f"[OK] Run {run['id']} completed.")