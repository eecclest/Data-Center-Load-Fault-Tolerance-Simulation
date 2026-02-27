"""
metrics.py
Tracks and reports simulation statistics.

Collected metrics
-----------------
    completed_requests  : count of successfully served requests
    dropped_requests    : count of requests dropped due to timeout
    total_response_time : sum of response times for completed requests
    response_times      : list of individual response times (for percentiles)
"""

from request import ClientRequest


class MetricsCollector:
    """
    Aggregates performance metrics across the full simulation run.
    
    Usage
    -----
    Call record_completion() for each finished request and record_drop()
    for each timed-out request.
    Call report() at the end to print a summary.
    """

    def __init__(self):
        self.completed_requests: int = 0
        self.dropped_requests: int = 0
        self.total_response_time: float = 0.0
        self.response_times: list[float] = []

    # ------------------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------------------
    
    def record_completion(self, request: ClientRequest) -> None:
        """Register a successfully completed request."""
        rt = request.response_time
        if rt is None:
            return  # Incomplete data; skip
        self.completed_requests += 1
        self.total_response_time += rt
        self.response_times.append(rt)

    def record_drop(self, request: ClientRequest) -> None:
        """Register a reqest dropped due to timeout."""
        self.dropped_requests += 1

    # ------------------------------------------------------------------------------
    # Derived statistics
    # ------------------------------------------------------------------------------

    @property
    def average_response_time(self) -> float:
        """Mean response time across all completed requests."""
        if self.completed_requests == 0:
            return 0.0
        return self.total_response_time / self.completed_requests
    
    @property
    def total_requests(self) -> int:
        return self.completed_requests + self.dropped_requests
    
    @property
    def drop_rate(self) -> float:
        """Fraction of all requests that were dropped."""
        if self.total_requests == 0:
            return 0.0
        return self.dropped_requests / self.total_requests
    
    def percentile(self, p: float) -> float:
        """
        Compute the p-th percentile of response times (0 ≤ p ≤ 100).
        Returns 0.0 if no completions recorded.
        """
        if not self.response_times:
            return 0.0
        sorted_rt = sorted(self.response_times)
        idx = max(0, int(len(sorted_rt) * p / 100) - 1)
        return sorted_rt[idx]
    
    # ------------------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------------------

    def report(self, utilization: float | None = None) -> None:
        """Print a formatted metrics summary to stdout."""
        separator = "=" * 50
        print(separator)
        print("       Data Center Simulation - Metrics Reports")
        print(separator)
        print(f"  Total requests arrived  : {self.total_requests}")
        print(f"  Completed requests      : {self.completed_requests}")
        print(f"  Dropped requests        : {self.dropped_requests}")
        print(f"  Drop rate               : {self.drop_rate:.2%}")
        print(f"  Avg response time       : {self.average_response_time:.4f} time units")
        if self.response_times:
            print(f"  Median response time          : {self.percentile(50):.4f} time units")
            print(f"  95th percentile response time : {self.percentile(95):.4f} time units")
        if utilization is not None:
            print(f"  Theoretical utilisation : ρ = {utilization:.4f}")
        print(separator)

    def __repr__(self) -> str:
        return (
            f"MetricsCollector(completed={self.completed_requests}, "
            f"dropped={self.dropped_requests}, "
            f"avg_rt={self.average_response_time:.4f})"
        )