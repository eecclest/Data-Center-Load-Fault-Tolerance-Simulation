"""
request.py
Defines the ClientRequest data class representing a single client request
in the data center simulation
"""


class ClientRequest:
    """
    Represents a client request entering the simulation.
    
    Attributes:
        request_id      : Unique identifier for this request
        arrival_time    : Simulation time at which the request arrived
        service_time    : Required service duration (drawn from Exp(1/μ))
        timeout         : Maximum time the request can sit before being dropped
        start_service_time  : Time at which service actually began (None until started)
        completion_time     : Time at which service completed (None until finished)
    """

    _id_counter = 0 # Class-level counter to assign unique IDs

    def __init__(self, arrival_time: float, service_time: float, timeout: float = float("inf")):
        ClientRequest._id_counter += 1
        self.request_id: int = ClientRequest._id_counter
        self.arrival_time: float = arrival_time
        self.service_time: float = service_time          # Exp(1/μ) sample
        self.timeout: float = timeout                    # Drop if wait > timeout
        self.start_service_time: float | None = None     # Set when server picks up request
        self.completion_time: float | None = None        # Set when service finishes

    # ------------------------------------------------------------------------------
    # Derived metrics (available after completion)
    # ------------------------------------------------------------------------------

    @property
    def wait_time(self) -> float | None:
        """Time spent waiting in queue before service started."""
        if self.start_service_time is None:
            return None
        return self.start_service_time - self.arrival_time
    
    @property
    def response_time(self) -> float | None:
        """Total time from arrival to completion (wait + service)."""
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time
    
    def is_timed_out(self, current_time: float) -> bool:
        """Return True if the request has been waiting longer than its timeout."""
        if self.start_service_time is not None:
            return False    # Already in service; not considered timed-out
        return (current_time - self.arrival_time) > self.timeout
    
    def __repr__(self) -> str:
        return (
            f"ClientRequest(id={self.request_id}, "
            f"arrival={self.arrival_time:.3f}, "
            f"service_time={self.service_time:.3f}, "
            f"timeout={self.timeout})"
        )