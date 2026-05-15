import pytest


pytestmark = [
    pytest.mark.adapter,
    pytest.mark.external,
    pytest.mark.skip(reason="Real SnapTrade tests require explicit user approval and out-of-repo credentials."),
]


def test_real_snaptrade_connection_placeholder() -> None:
    """Document the external-test boundary without touching credentials or the network."""
    raise AssertionError("This placeholder should remain skipped unless a real external test is approved.")
