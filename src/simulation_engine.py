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
            self,
            num_servers: int = 3,
            arrival_rate: float = 2.0,
            service_rate: float = 1.5,
            sim_duration: float = 200.0,
            dt: float = 1.0,
            algorithm: str = "round_robin",
            request_timeout: float = float("inf"),
            seed: int | None = 42,
    ):
        if seed is not None:
            np.random.seed(seed)

        self.arrival_rate = arrival_rate    # λ
        self.service_rate = service_rate    # μ per server
        self.sim_duration = sim_duration
        self.dt = dt
        self.request_timeout = request_timeout
        self.clock: float = 0.0

        # Theoretical utilisation  ρ = λ / (N · μ)
        self.utilization: float = arrival_rate / (num_servers * service_rate)

        # Build servers, load balancer, and metrics collector
        self.servers: list[ServerNode] = [
            ServerNode(server_id = i, service_rate=service_rate)
            for i in range(num_servers)
        ]
        self.load_balancer = LoadBalancer(self.servers, algorithm=algorithm)
        self.metrics = MetricsCollector()

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
        print(f"[Sim] Starting simulation  λ={self.arrival_rate}, "
              f"μ={self.service_rate}, ρ={self.utilization:.3f}, "
              f"duration={self.sim_duration}, dt={self.dt}")
        print(f"[Sim] Servers: {len(self.servers)}, "
              f"Algorithm: {self.load_balancer.algorithm}\n")
        
        num_ticks = int(self.sim_duration / self.dt)

        for _ in range(num_ticks):
            self.clock += self.dt

            # 1. Generate new arrivals
            # numpy.random.poisson give exact poisson count per interval
            num_arrivals = np.random.poisson(self.arrival_rate * self.dt)
            for _ in range(num_arrivals):
                service_time = np.random.exponential(1.0 / self.service_rate)
                req = ClientRequest(
                    arrival_time = self.clock,
                    service_time = service_time,
                    timeout = self.request_timeout,
                )
                self.load_balancer.dispatch(req)
            # 2. Drop timed-out waiting requests
            for server in self.servers:
                dropped = server.drop_timed_out(self.clock)
                for req in dropped:
                    self.metrics.record_drop(req)
            
            # 3. Advance each server by one tick
            for server in self.servers:
                completed = server.tick(self.clock)
                for req in completed:
                    self.metrics.record_completion(req)

        # Drain in-progress requests at simulation end
        self._drain_remaining()

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

    def summary(self) -> None:
        """Prit metrics report with utilisation context."""
        self.metrics.report(utilization = self.utilization)
        
        