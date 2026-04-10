"""
simulation_engine.py
Core discrete-time simulation loop for the Intelligent Data Center Load and Fault-Tolerance
Simulation

Math Model
----------
    Arrival process : Poisson(λ)
        P(arrival in one timestep dt) ≈ λ * dt      (Bernoulli approx)
        Implemented by drawing from numpy.random.poisson(λ * dt) arrivals
        per tick, which is exact for Poisson inter-arrivals.
        
    Service time : Exponential with mean 1/µ
        Sampled at request creation via numpy.random.exponential(1/µ).
        
    Utilisation : ρ = λ / (N · μ) where N = number of servers
"""

import numpy as np
import json, csv, os
from request import ClientRequest
from server import ServerNode
from load_balancer import LoadBalancer
from metrics import MetricsCollector


class SimulationEngine:
    """
    Drives the discrete-time simulation.

    Parameters
    ----------
    num_servers     : Number of ServerNode instances to create
    arrival_rate    : λ - mean requests per time unit (Poisson)
    service_rate    : μ - exponential service rate per server
    sim_duration    : Total simulation time (time units)
    dt              : Time-step size (default 1.0)
    algorithm       : Load-balancing algorithm ("round_robin" | "least_loaded")
    request_timeout : Max wait time before a request is dropped (default ∞)
    seed            : Random seed for reproducibility (optional)
    """

    def __init__(
            self, num_servers, arrival_rate, service_rate,
                 failure_rate, recovery_rate, algorithm,
                 simulation_time, seed, run_id,dt=1.0, 
                 request_timeout=float("inf") 
    ):
        if seed is not None:
            np.random.seed(seed)

        self.run_id = run_id
        self.algorithm = algorithm
        self.num_servers = num_servers
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.failure_rate = failure_rate
        self.recovery_rate = recovery_rate
        self.simulation_time = simulation_time
        self.sim_duration = simulation_time

        self.dt = dt
        self.clock = 0.0
        self.request_timeout = request_timeout

        self.timeseries_data = []
        self.event_log = []

        # Theoretical utilisation  ρ = λ / (N · μ)
        self.utilization: float = arrival_rate / (num_servers * service_rate)

        # Build servers, load balancer, and metrics collector
        self.servers: list[ServerNode] = [
            ServerNode(server_id = i, service_rate=service_rate)
            for i in range(num_servers)
        ]
        self.load_balancer = LoadBalancer(self.servers, algorithm=algorithm)
        self.metrics = MetricsCollector()

        self._queue_depth_history: list[list[int]] = [[] for _ in self.servers]
        self._busy_ticks: list[int] = [0] * num_servers
        self._total_ticks: int = 0

    # ------------------------------------------------------------------------------
    # Main simulation loop
    # ------------------------------------------------------------------------------

    def run(self) -> MetricsCollector:
        """
        Execute the simulation from t=0 to t=sim_duration.
        
        Each tick:
            1. Generate arrivals using Poisson(λ · dt) - exact Poisson sampling.
            2. Drop tiemd-out requests from all server queues.
            3. Advance each server by one tick (complete + start service).
            4. Collect completed-request metrics.
            
        Returns the populated MetricsCollector.
        """
        print(f"[Sim] Starting simulation  lambda={self.arrival_rate}, "
            f"mu={self.service_rate}, rho={self.utilization:.3f}, "
            f"duration={self.sim_duration}, dt={self.dt}")
        print(f"[Sim] Servers: {len(self.servers)}, "
            f"Algorithm: {self.load_balancer.algorithm}\n")
        
        num_ticks = int(self.sim_duration / self.dt)

        for _ in range(num_ticks):
            self.clock += self.dt
            self._total_ticks += 1

            # 1. Apply failure/recovery model to each server
            for server in self.servers:
                event = server.apply_failure_model(
                    current_time=self.clock,
                    failure_rate=self.failure_rate,
                    recovery_rate=self.recovery_rate,
                )
                if event == "failed":
                    self.metrics.record_failure()
                    self.event_log.append(("failure", self.clock))
                elif event == "recovered":
                    self.event_log.append(("recovery", self.clock))

            # 2. Generate new arrivals
            # numpy.random.poisson give exact poisson count per interval
            num_arrivals = np.random.poisson(self.arrival_rate * self.dt)
            for _ in range(num_arrivals):
                req = ClientRequest(
                    arrival_time = self.clock,
                    service_time = float(np.random.exponential(1.0 / self.service_rate)),
                    timeout = self.request_timeout,
                )
                result = self.load_balancer.dispatch(req)
                if result is None:
                    self.metrics.record_drop(req)
                    self.event_log.append(("dropped_no_servers", self.clock))
                else:
                    self.event_log.append(("arrival", self.clock))

            # 3. Drop timed-out waiting requests
            for server in self.servers:
                dropped = server.drop_timed_out(self.clock)
                for req in dropped:
                    self.metrics.record_drop(req)
                    self.event_log.append(("dropped", self.clock))
            
            # 4. Advance each server by one tick (now skips failed servers)
            for i, server in enumerate(self.servers):
                if not server.is_active:
                    continue
                if server.is_busy():
                    self._busy_ticks[i] += 1
                for req in server.tick(self.clock):
                    self.metrics.record_completion(req)
                    self.event_log.append(("completion", self.clock))

            for i, server in enumerate(self.servers):
                self._queue_depth_history[i].append(server.queue_length())

            total_queue_length = sum(len(s.queue) for s in self.servers)
            active_servers = sum(1 for s in self.servers if s.is_active)

            self.timeseries_data.append([
                self.clock,
                total_queue_length,
                active_servers
            ])

        # Drain in-progress requests at simulation end
        self._drain_remaining()

        # ← Save results HERE, after simulation is fully complete
    
        os.makedirs("results", exist_ok=True)

        # Save summary JSON
        metrics = self.metrics.compute_summary()
        with open(f"results/run_{self.run_id}_summary.json", "w") as f:
            json.dump(metrics, f, indent=4)

        # Save time-series CSV
        with open(f"results/run_{self.run_id}_timeseries.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "queue_length", "active_servers"])
            writer.writerows(self.timeseries_data)

        # Save event log
        with open(f"results/run_{self.run_id}_events.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["event_type", "time"])
            writer.writerows(self.event_log)

        print("[Sim] Simulation complete. \n")
        return self.metrics
    
    #-------------------------------------------------------------------------------
    # Helpers
    #-------------------------------------------------------------------------------

    def _drain_remaining(self) -> None:
        """
        After the main loop, finalise any request currently in service
        (do not process queue - those are abandoned at end-of-sim).
        """
        for server in self.servers:
            if server.current_request is not None:
                req = server.current_request
                # Mark completion at the scheduled time even if past sim end
                req.completion_time = req.completion_time or self.clock
                self.metrics.record_completion(req)
                server.current_request = None

    def per_server_utilization(self) -> list[float]:
        if self._total_ticks == 0:
            return [0.0] * len(self.servers)
        return [b / self._total_ticks for b in self._busy_ticks]

    def avg_queue_depth_per_server(self) -> list[float]:
        result = []
        for history in self._queue_depth_history:
            result.append(float(np.mean(history)) if history else 0.0)
        return result

    def max_queue_depth_per_server(self) -> list[int]:
        return [int(max(h)) if h else 0 for h in self._queue_depth_history]

    def queue_depth_history(self) -> list[list[int]]:
        return self._queue_depth_history

    def results(self) -> dict:
        psu = self.per_server_utilization()
        aqd = self.avg_queue_depth_per_server()
        mqd = self.max_queue_depth_per_server()
        m = self.metrics
        return {
            "run_id": self.run_id,
            "algorithm": self.algorithm,
            "parameters": {
                "num_servers": len(self.servers),
                "arrival_rate": self.arrival_rate,
                "service_rate": self.service_rate,
                "sim_duration": self.sim_duration,
                "request_timeout": (
                    self.request_timeout if self.request_timeout != float("inf") else "inf"
                ),
            },
            "metrics": {
                "total_requests": m.total_requests,
                "completed_requests": m.completed_requests,
                "dropped_requests": m.dropped_requests,
                "drop_rate": round(m.drop_rate, 6),
                "avg_response_time": round(m.average_response_time, 6),
                "median_response_time": round(m.percentile(50), 6),
                "p95_response_time": round(m.percentile(95), 6),
                "theoretical_utilization": round(self.utilization, 6),
            },
            "per_server": {
                f"server_{i}": {
                    "empirical_utilization": round(psu[i], 6),
                    "avg_queue_depth": round(aqd[i], 6),
                    "max_queue_depth": mqd[i],
                }
                for i in range(len(self.servers))
            },
        }

    def summary(self) -> None:
        """Prit metrics report with utilisation context."""
        self.metrics.report(utilization = self.utilization)
        
        