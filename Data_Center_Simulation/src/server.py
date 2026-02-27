"""
server.py
Defines the ServerNode class. Each server maintains a FIFO queue of
ClientRequests and processes the mone at a time using an exponential
service time distribution.
"""

from collections import deque
from request import ClientRequest


class ServerNode:
    """
    Models a single server node in the data center.
    
    Processing model
    ----------------
    - THe server works in discrete simulation time-steps.
    - When idle and the queue is non-empty it picks the next request,
      records start_service_time, and schedules a completion_time drawn
      from Exp(service_rate).
    - On each tick the server checks whether the in-progress request has
      completed and, if so, moves to the next one.
      
    Attributes:
        server_id    : Unique server identifier
        service_rate : μ - exponential rate parameter (mean service = 1/μ)
        queue        : FIFO queue of waiting ClientRequests
        current_request : Request currently being served (None if idle)
    """

    def __init__(self, server_id: int, service_rate: float):
        self.server_id: int = server_id
        self.service_rate: float = service_rate         # u
        self.queue: deque[ClientRequest] = deque()
        self.current_request: ClientRequest | None = None

        # Internal book-keeping
        self._completed: list[ClientRequest] = []       # Finished this run

    # ------------------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------------------

    def enqueue(self, request: ClientRequest) -> None:
        """Add a new request to the server's waiting queue."""
        self.queue.append(request)

    def queue_length(self) -> int:
        """Return total number of waiting requests (excludes in-service)."""
        return len(self.queue)
    
    def is_busy(self) -> bool:
        """Retrun True if the server is currently processing a request."""
        return self.current_request is not None

    def tick(self, current_time: float) -> list[ClientRequest]:
        """
        Advance the server by one simulation time-step.
        
        Steps:
            1. If a request is in service and its completion_time has passed,
               mark it complete and free the server.
            2. If the server is free and the queue is non-empty, start the
               next request (set start_service_time; completion_time is
               determined by the service_time sampled at request creation).
        
        Parameters:
            current_time : current simulation clock value
            
        Returns:
            List of ClientRequest objects completed during this tick.
        """
        completed_this_tick: list[ClientRequest] = []

        # Step 1: Check if current request has finished
        if self.current_request is not None:
            req = self.current_request
            if current_time >= req.completion_time:  # type: ignore[operator]
                req.completion_time = current_time   # snap to tick boundary
                completed_this_tick.append(req)
                self._completed.append(req)
                self.current_request = None
            
        # Step 2: Pull next request from queue if free
        if self.current_request is None and self.queue:
            next_req = self.queue.popleft()
            next_req.start_service_time = current_time
            # completion schedled based on pre-drawn service_time
            next_req.completion_time = current_time + next_req.service_time
            self.current_request = next_req

        return completed_this_tick
    
    def drop_timed_out(self, current_time: float) -> list[ClientRequest]:
        """
        Remove and return requests that have exceeded their timeout
        while waiting in queue (not yet in service).
        """
        timed_out: list[ClientRequest] = []
        remaining: deque[ClientRequest] = deque()
        for req in self.queue:
            if req.is_timed_out(current_time):
                timed_out.append(req)
            else:
                remaining.append(req)
        self.queue = remaining
        return timed_out
    
    def __repr__(self) -> str:
        status = "busy" if self.is_busy() else "idle"
        return (
            f"ServerNode(id={self.server_id}, μ={self.service_rate}, "
            f"status={status}, queue_len={self.queue_length()})"
        )
    