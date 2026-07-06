"""Compatibility facade — ``tools.py`` split into the ``tools/`` package (P34A-T11D).

Re-exports the tool envelopes/contracts (``envelopes``), registry building
(``registry``), and execution + per-tool projections (``executors``) so
existing ``from app.services.agent_team.tools import ...`` paths keep
resolving to the same objects. New code should import from the specific
submodule. Facade retained; flat re-export cleaned up alongside T11F.
"""

from app.services.agent_team.tools.envelopes import *  # noqa: F401,F403
from app.services.agent_team.tools.executors import *  # noqa: F401,F403
from app.services.agent_team.tools.registry import *  # noqa: F401,F403
