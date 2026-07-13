from __future__ import annotations

import pytest

from app.services.agent_team.safety.report_output_safety import validate_agent_team_report_output


pytestmark = [pytest.mark.unit]


def _payload(markdown: str) -> dict[str, object]:
    return {
        "final_synthesis_markdown": markdown,
        "evidence_references": (),
    }


@pytest.mark.parametrize(
    "markdown",
    (
        "This would make you overweight semiconductors -- consider trimming SMH first.",
        "Your portfolio is too concentrated after this trade.",
        "You're well diversified, so this addition is fine.",
        "Cash is sufficient; you can safely proceed.",
        "A 7% position is a reasonable size for a new name.",
        "NVDA is attractive here given AI demand.",
        "Assignment is unlikely with the stock 8% above the strike.",
        "Selling these puts earns a 14% annualized yield on collateral.",
        "SMH already gives you plenty of NVDA exposure.",
        "Consider spreading this across two or three purchases.",
    ),
)
def test_p35_report_output_validator_rejects_wrong_pair_wording(markdown: str) -> None:
    with pytest.raises(ValueError):
        validate_agent_team_report_output(_payload(markdown), label="agent-team saved report")


@pytest.mark.parametrize(
    "markdown",
    (
        "Semiconductor-classified holdings would go from 35.0% to 42.0% of your portfolio.",
        "After this purchase, NVDA would be 12.4% of your portfolio, above the 10% single-company reference point used in this report.",
        "Your three largest holdings would make up 88% of the portfolio; two are exchange-traded funds -- one broad-market (VTI), one semiconductor-focused (SMH) -- whose individual holdings were not reviewed.",
        "The snapshot shows $12,000 in cash against this $7,000 purchase. Verify current buying power at your broker.",
        "This single purchase equals 7.0% of your portfolio's total value.",
        "The July 7 closing price ($103.20) is above the $95 strike. Whether assignment occurs depends on prices through August 15, which this review does not predict.",
        "Selling the puts would add $410 to cash and set aside $19,000 as collateral until August 15.",
        "This purchase would add a new $7,000 NVDA position to a portfolio that already holds $35,000 of SMH, a semiconductor ETF.",
    ),
)
def test_p35_report_output_validator_allows_right_pair_factual_wording(markdown: str) -> None:
    validate_agent_team_report_output(_payload(markdown), label="agent-team saved report")
