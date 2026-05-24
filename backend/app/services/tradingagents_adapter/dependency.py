"""Lazy optional dependency detection for TradingAgents.

This module must stay import-safe for FastAPI startup: it checks whether a
module is discoverable, but it does not import or execute TradingAgents.
"""

from dataclasses import dataclass
from importlib import util
from importlib.machinery import ModuleSpec
from typing import Callable, Literal


DependencyStatus = Literal["available", "missing", "import_error"]

DEFAULT_TRADINGAGENTS_MODULE = "tradingagents"
_INSTALL_GUIDANCE = (
    "TradingAgents is optional. Install it into the backend Python environment "
    "only after the public-research adapter boundary is reviewed; do not vendor "
    "or copy TradingAgents source into this repository."
)


@dataclass(frozen=True)
class TradingAgentsDependencyResult:
    """Safe, frontend/report-neutral dependency status for TradingAgents."""

    dependency_name: str
    module_name: str
    status: DependencyStatus
    available: bool
    install_guidance: str
    detection_method: str = "importlib.util.find_spec"
    error_type: str | None = None
    message: str | None = None


FindSpec = Callable[[str], ModuleSpec | None]


def detect_tradingagents_dependency(
    *,
    module_name: str = DEFAULT_TRADINGAGENTS_MODULE,
    find_spec: FindSpec | None = None,
) -> TradingAgentsDependencyResult:
    """Detect whether TradingAgents is installed without importing it."""

    normalized_module = module_name.strip()
    if not normalized_module:
        raise ValueError("module_name must not be empty")
    if "." in normalized_module:
        raise ValueError("module_name must be a top-level module name")

    finder = find_spec or util.find_spec
    try:
        spec = finder(normalized_module)
    except Exception as exc:
        return TradingAgentsDependencyResult(
            dependency_name="TradingAgents",
            module_name=normalized_module,
            status="import_error",
            available=False,
            install_guidance=_INSTALL_GUIDANCE,
            error_type=type(exc).__name__,
            message="TradingAgents availability could not be determined; deterministic app features remain available.",
        )

    if spec is None:
        return TradingAgentsDependencyResult(
            dependency_name="TradingAgents",
            module_name=normalized_module,
            status="missing",
            available=False,
            install_guidance=_INSTALL_GUIDANCE,
            message="TradingAgents is not installed; public research evidence is unavailable.",
        )

    return TradingAgentsDependencyResult(
        dependency_name="TradingAgents",
        module_name=normalized_module,
        status="available",
        available=True,
        install_guidance="TradingAgents module is discoverable; adapter execution remains disabled until later phases.",
        message="TradingAgents is installed but has not been imported or executed by this detector.",
    )
