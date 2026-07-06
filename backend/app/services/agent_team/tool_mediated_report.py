"""Compatibility facade — split into orchestration/ + auditing/ (P34A-T11E).

The god-module was relocated to ``orchestration.tool_mediated_runner`` with
shared models in ``orchestration.models`` and the Evidence Auditor extracted
to ``auditing.evidence_auditor``. Re-exports here so existing
``from app.services.agent_team.tool_mediated_report import ...`` paths keep
resolving to the same objects. Cleaned up alongside T11F.
"""

from app.services.agent_team.orchestration.models import *  # noqa: F401,F403
from app.services.agent_team.auditing.evidence_auditor import *  # noqa: F401,F403
from app.services.agent_team.orchestration.tool_mediated_runner import *  # noqa: F401,F403
from app.services.agent_team.orchestration.tool_mediated_runner import _chain_metadata  # noqa: F401
