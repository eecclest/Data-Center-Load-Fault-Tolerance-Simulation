"""
load_balancer.py
Implements the LoadBalancer class with two scheduling algorithms:
    - Round Robin   : deterministic cycling through servers
    - Least Loaded   : argmin(queue_length_i) across all servers
"""

from server import ServerNode
from request import ClientRequest


class LoadBalancer:
    """
    Distributes incoming ClientRequests to ServerNodes.
    
    Supported algorithms
    --------------------
    "round_robin"   - cycles through servers in fixed order
    "least_loaded"   - always selects the server with the shortest queue
                        (ties are broken by lower server_id)    argmin(|Q_i|)
    """

    ALGORITHMS = ("round_robin", "least_loaded")

    def __init__(self, servers: list[ServerNode], algorithm: str = "round_robin"):
        if algorithm not in self.ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. Choose from {self.ALGORITHMS}."
            )
        self.servers: list[ServerNode] = servers
        self.algorithm: str = algorithm
        self._rr_index: int = 0     # Round-Robin pointer

    # -------------------------------------------------------------------------------
    # Core dispatch
    # -------------------------------------------------------------------------------

    def dispatch(self, request: ClientRequest) -> ServerNode:
        """
        Route *request* to a server and enqueue it there.
        
        Returns the chosen ServerNode.
        """
        if not self.servers:
            raise RuntimeError("LoadBalancer has no servers to dispatch to.")
        
        if self.algorithm == "round_robin":
            target = self._round_robin()
        else:   # least_loaded
            target = self._least_loaded()

        target.enqueue(request)
        return target
    
    # ------------------------------------------------------------------------------
    # Implementing Algorithms
    # ------------------------------------------------------------------------------

    def _round_robin(self) -> ServerNode:
        """
        Round Robin - deterministically cycle through servers.
        Pointer advances modulo the number of servers.
        """
        server = self.servers[self._rr_index % len(self.servers)]
        self._rr_index += 1
        return server
    
    def _least_loaded(self) -> ServerNode:
        """
        Least Loaded - selects argmin(queue_length_i).
        In case of ties the server with the lower index is chosen.
        """
        # queue_length counts *waiting requests; does not include the request 
        # currently in service, matching the theoretical mdoel.
        return min(self.servers, key = lambda s: s.queue_length())
    
    # ------------------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------------------

    def status(self) -> str:
        lines = [f"LoadBalancer [{self.algorithm}]"]
        for s in self.servers:
            lines.append(f" {s}")
        return "\n".join(lines)
    
    def __repr__(self) -> str: 
        return f"LoadBalancer(algorithm={self.algorithm}, servers={len(self.servers)})"
    