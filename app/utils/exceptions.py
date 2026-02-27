class OrchestratorError(Exception):
    """Base exception for orchestrator-related errors."""
    pass


class AgentError(Exception):
    """Raised when an agent integration fails."""
    pass
