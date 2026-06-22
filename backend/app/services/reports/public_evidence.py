"""Offline public evidence projection helpers for saved Agent Team reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import threading
import time
from typing import Any, Mapping, Protocol
from urllib import error as urlerror
from urllib import request as urlrequest

from app.schemas.reports import (
    AgentTeamPublicRoleName,
    SavedEvidencePackageRead,
    SavedPublicEvidenceFactRead,
    SavedPublicEvidencePackageRead,
    SavedPublicEvidenceRightsStatus,
    SavedPublicEvidenceSectionRead,
    SavedPublicRoleEvidenceProjectionRead,
    SavedPublicRoleInstrumentContextRead,
)
from app.services.agent_team.report_output_safety import ROLE_ALLOWED_EVIDENCE_KEYS

_EDGAR_PROCESS_RATE_LIMIT_SECONDS = 1.0
_EDGAR_PROCESS_RATE_LOCK = threading.Lock()
_EDGAR_LAST_REQUEST_MONOTONIC = 0.0


@dataclass(frozen=True)
class PublicEvidenceProjectionRequest:
    symbol_or_underlying: str | None = None


@dataclass(frozen=True)
class EdgarCompanyProfileSourcePolicy:
    """Fail-closed source policy for SEC EDGAR company-profile evidence."""

    enabled: bool = False
    external_access_enabled: bool = False
    runtime_environment: str = "test"
    allowed_runtime_environments: tuple[str, ...] = ("local", "dev", "test")
    declared_user_agent: str | None = None
    request_timeout_seconds: float = 5.0
    response_size_cap_bytes: int = 1_000_000
    request_budget_per_run: int = 2
    source_key: str = "sec_edgar_submissions"
    source_label: str = "SEC EDGAR metadata - company profile only"
    rights_status: SavedPublicEvidenceRightsStatus = "reviewed"
    retention_label: str = "Normalized identity facts only; raw EDGAR payloads are not retained."
    attribution_label: str = (
        "Source: SEC EDGAR submissions metadata. Company identity and listing metadata only. "
        "Not investment advice or a trading signal."
    )
    caveat_label: str = (
        "SEC SIC metadata may be broad, legacy, and may lag company changes; EDGAR metadata does not "
        "include financial analysis, filing text, or investment conclusions."
    )

    def live_client_ready(self) -> bool:
        """Return whether policy allows a future live EDGAR HTTP client to run."""

        return (
            self.enabled
            and self.external_access_enabled
            and self.runtime_environment in self.allowed_runtime_environments
            and _valid_declared_user_agent(self.declared_user_agent)
            and 0 < self.request_timeout_seconds <= 10
            and 1_000 <= self.response_size_cap_bytes <= 5_000_000
            and 2 <= self.request_budget_per_run <= 10
        )


class EdgarCompanyProfileClient(Protocol):
    """Replayable client boundary for SEC EDGAR submissions-shaped metadata."""

    def fetch_company_tickers(self) -> Mapping[str, Any]:
        """Return SEC-published company tickers mapping data."""

    def fetch_submissions(self, cik_reference: str) -> Mapping[str, Any]:
        """Return SEC submissions metadata for a normalized CIK reference."""


class EdgarHttpTransport(Protocol):
    """Bounded JSON transport for a future explicit EDGAR live smoke."""

    def fetch_json(
        self,
        endpoint_url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
        response_size_cap_bytes: int,
    ) -> Mapping[str, Any]:
        """Return a JSON object from a reviewed EDGAR endpoint."""


class EdgarSourceUnavailableError(RuntimeError):
    """Sanitized EDGAR acquisition failure."""


class UrllibEdgarHttpTransport:
    """Small dependency-free EDGAR HTTP transport; unused unless explicitly wired."""

    def fetch_json(
        self,
        endpoint_url: str,
        *,
        user_agent: str,
        timeout_seconds: float,
        response_size_cap_bytes: int,
    ) -> Mapping[str, Any]:
        request = urlrequest.Request(
            endpoint_url,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "identity",
            },
        )
        try:
            _respect_edgar_process_rate_limit()
            with urlrequest.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read(response_size_cap_bytes + 1)
        except (OSError, urlerror.URLError) as exc:
            raise EdgarSourceUnavailableError("SEC EDGAR metadata request failed") from None
        if len(body) > response_size_cap_bytes:
            raise EdgarSourceUnavailableError("SEC EDGAR metadata response exceeded the size cap")
        try:
            decoded = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise EdgarSourceUnavailableError("SEC EDGAR metadata response was not valid JSON") from None
        if not isinstance(decoded, Mapping):
            raise EdgarSourceUnavailableError("SEC EDGAR metadata response was not a JSON object")
        return decoded


class EdgarCompanyProfileHttpClient:
    """Policy-gated EDGAR submissions client for explicit future live source slices."""

    _COMPANY_TICKERS_ENDPOINT = "https://www.sec.gov/files/company_tickers.json"
    _SUBMISSIONS_ENDPOINT_TEMPLATE = "https://data.sec.gov/submissions/CIK{cik_digits}.json"

    def __init__(
        self,
        *,
        policy: EdgarCompanyProfileSourcePolicy,
        transport: EdgarHttpTransport | None = None,
    ) -> None:
        if not policy.live_client_ready():
            raise EdgarSourceUnavailableError("SEC EDGAR live-client policy is not ready")
        self._policy = policy
        self._transport = transport or UrllibEdgarHttpTransport()
        self._request_count = 0

    @property
    def request_count(self) -> int:
        return self._request_count

    def fetch_company_tickers(self) -> Mapping[str, Any]:
        return self._fetch_json(self._COMPANY_TICKERS_ENDPOINT)

    def fetch_submissions(self, cik_reference: str) -> Mapping[str, Any]:
        cik_digits = _cik_digits_from_reference(cik_reference)
        if cik_digits is None:
            raise EdgarSourceUnavailableError("SEC EDGAR CIK reference was invalid")
        return self._fetch_json(self._SUBMISSIONS_ENDPOINT_TEMPLATE.format(cik_digits=cik_digits))

    def _fetch_json(self, endpoint_url: str) -> Mapping[str, Any]:
        if self._request_count >= self._policy.request_budget_per_run:
            raise EdgarSourceUnavailableError("SEC EDGAR request budget was exhausted")
        self._request_count += 1
        assert self._policy.declared_user_agent is not None
        return self._transport.fetch_json(
            endpoint_url,
            user_agent=self._policy.declared_user_agent,
            timeout_seconds=self._policy.request_timeout_seconds,
            response_size_cap_bytes=self._policy.response_size_cap_bytes,
        )


def build_edgar_company_profile_live_smoke_projection(
    *,
    symbol_or_underlying: str,
    declared_user_agent: str,
    runtime_environment: str = "local",
    transport: EdgarHttpTransport | None = None,
) -> SavedPublicEvidencePackageRead:
    """Run one explicit local/internal EDGAR profile lookup through the reviewed seam."""

    policy = EdgarCompanyProfileSourcePolicy(
        enabled=True,
        external_access_enabled=True,
        runtime_environment=runtime_environment,
        allowed_runtime_environments=("local", "dev", "test"),
        declared_user_agent=declared_user_agent,
        request_timeout_seconds=5.0,
        response_size_cap_bytes=1_000_000,
        request_budget_per_run=2,
    )
    client = EdgarCompanyProfileHttpClient(policy=policy, transport=transport)
    return build_public_evidence_projection(
        symbol_or_underlying=symbol_or_underlying,
        edgar_policy=policy,
        edgar_client=client,
    )


class NoReviewedPublicEvidenceProvider:
    """Default provider boundary until public source rights are reviewed."""

    def snapshot(self, request: PublicEvidenceProjectionRequest) -> SavedPublicEvidencePackageRead:
        return SavedPublicEvidencePackageRead.not_reviewed(request.symbol_or_underlying)


class EdgarCompanyProfileProvider:
    """Normalize replayed EDGAR submissions metadata into public company profile evidence."""

    def __init__(
        self,
        *,
        client: EdgarCompanyProfileClient | None,
        policy: EdgarCompanyProfileSourcePolicy,
    ) -> None:
        self._client = client
        self._policy = policy

    def snapshot(self, request: PublicEvidenceProjectionRequest) -> SavedPublicEvidencePackageRead:
        public_evidence = SavedPublicEvidencePackageRead.not_reviewed(request.symbol_or_underlying)
        profile = self.company_profile_section(request.symbol_or_underlying)
        return public_evidence.model_copy(
            update={
                "public_evidence_mode": (
                    "provider_reference" if profile.availability in {"available", "limited"} else "not_reviewed"
                ),
                "public_company_profile": profile,
                "limitations": _public_package_limitations(profile),
            }
        )

    def company_profile_section(self, symbol_or_underlying: str | None) -> SavedPublicEvidenceSectionRead:
        if not self._policy.enabled:
            return _edgar_unavailable_section(
                source_label="SEC EDGAR source disabled",
                summary_label="SEC EDGAR company profile evidence is disabled for this run.",
                caveat_codes=("edgar_source_disabled",),
            )
        if self._policy.external_access_enabled and not self._policy.live_client_ready():
            return _edgar_unavailable_section(
                source_label=self._policy.source_label,
                summary_label="SEC EDGAR company profile evidence is unavailable because live-client policy is not ready.",
                caveat_codes=("edgar_live_policy_not_ready",),
            )
        if self._client is None:
            return _edgar_unavailable_section(
                source_label=self._policy.source_label,
                summary_label="SEC EDGAR company profile evidence is unavailable because no approved client is configured.",
                caveat_codes=("edgar_client_not_configured",),
            )

        symbol = _normalize_symbol(symbol_or_underlying)
        if symbol is None:
            return _edgar_unavailable_section(
                source_label=self._policy.source_label,
                summary_label="SEC EDGAR company profile evidence is unavailable because no normalized symbol was provided.",
                caveat_codes=("public_company_symbol_missing",),
            )

        try:
            company_tickers = self._client.fetch_company_tickers()
            if _payload_size_exceeds_cap(company_tickers, self._policy.response_size_cap_bytes):
                return _edgar_unavailable_section(
                    source_label=self._policy.source_label,
                    summary_label="SEC EDGAR company profile evidence is unavailable because replay metadata exceeded the response-size cap.",
                    caveat_codes=("edgar_response_too_large",),
                )
            ticker_row = _resolve_sec_ticker_row(company_tickers, symbol)
            if ticker_row is None:
                return _edgar_unavailable_section(
                    source_label=self._policy.source_label,
                    summary_label="SEC EDGAR company profile evidence is unavailable because the symbol was not resolved to a CIK.",
                    caveat_codes=("edgar_symbol_unresolved",),
                )
            cik_reference = _format_cik_reference(ticker_row.get("cik_str"))
            if cik_reference is None:
                return _edgar_unavailable_section(
                    source_label=self._policy.source_label,
                    summary_label="SEC EDGAR company profile evidence is unavailable because the resolved CIK was invalid.",
                    caveat_codes=("edgar_cik_unavailable",),
                )
            submissions = self._client.fetch_submissions(cik_reference)
            if _payload_size_exceeds_cap(submissions, self._policy.response_size_cap_bytes):
                return _edgar_unavailable_section(
                    source_label=self._policy.source_label,
                    summary_label="SEC EDGAR company profile evidence is unavailable because replay submissions metadata exceeded the response-size cap.",
                    caveat_codes=("edgar_response_too_large",),
                )
        except Exception:
            return _edgar_unavailable_section(
                source_label=self._policy.source_label,
                summary_label="SEC EDGAR company profile evidence is unavailable from the replay client.",
                caveat_codes=("edgar_replay_unavailable",),
            )

        return _normalize_edgar_profile_section(
            symbol=symbol,
            ticker_row=ticker_row,
            cik_reference=cik_reference,
            submissions=submissions,
            policy=self._policy,
        )


def build_public_evidence_projection(
    *,
    symbol_or_underlying: str | None,
    edgar_policy: EdgarCompanyProfileSourcePolicy | None = None,
    edgar_client: EdgarCompanyProfileClient | None = None,
) -> SavedPublicEvidencePackageRead:
    """Build the default generation-time public evidence projection."""

    if edgar_policy is not None:
        return EdgarCompanyProfileProvider(client=edgar_client, policy=edgar_policy).snapshot(
            PublicEvidenceProjectionRequest(symbol_or_underlying=symbol_or_underlying)
        )
    return NoReviewedPublicEvidenceProvider().snapshot(
        PublicEvidenceProjectionRequest(symbol_or_underlying=symbol_or_underlying)
    )


_PUBLIC_ROLE_SECTION_KEYS: dict[AgentTeamPublicRoleName, tuple[str, ...]] = {
    "fundamentals_analyst": (
        "public_company_profile",
        "public_fundamentals_snapshot",
        "public_events_calendar",
    ),
    "news_analyst": (
        "public_news_snapshot",
        "public_events_calendar",
        "public_market_context",
    ),
    "technical_analyst": (
        "public_technical_context",
        "public_market_context",
    ),
}


def build_public_role_evidence_projection(
    evidence: SavedEvidencePackageRead,
    *,
    role_name: AgentTeamPublicRoleName,
) -> SavedPublicRoleEvidenceProjectionRead:
    """Narrow generation-time public evidence to a single public role boundary."""

    public_evidence = evidence.public_evidence or build_public_evidence_projection(
        symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying
    )
    allowed_section_keys = tuple(
        section_key
        for section_key in _PUBLIC_ROLE_SECTION_KEYS[role_name]
        if section_key in ROLE_ALLOWED_EVIDENCE_KEYS[role_name]
    )
    sections = tuple(getattr(public_evidence, section_key) for section_key in allowed_section_keys)
    citable_section_keys = tuple(
        section.section_key for section in sections if section.availability in {"available", "limited"}
    )
    return SavedPublicRoleEvidenceProjectionRead(
        role_name=role_name,
        instrument_context=SavedPublicRoleInstrumentContextRead(
            symbol_or_underlying=evidence.trade_intent_summary.symbol_or_underlying,
            review_flow_label=evidence.trade_intent_summary.review_flow_label,
        ),
        allowed_section_keys=allowed_section_keys,
        sections=sections,
        citable_section_keys=citable_section_keys,
        degrade_reason=_public_projection_degrade_reason(sections, citable_section_keys),
    )


def _public_projection_degrade_reason(sections: tuple[object, ...], citable_section_keys: tuple[str, ...]) -> str | None:
    if citable_section_keys:
        return None
    availability = {getattr(section, "availability", None) for section in sections}
    if "not_available" in availability:
        return "public_evidence_not_available"
    if availability == {"not_reviewed"}:
        return "no_reviewed_public_evidence"
    if availability == {"not_applicable"}:
        return "public_evidence_not_applicable"
    return "public_evidence_unavailable"


def _normalize_symbol(symbol_or_underlying: str | None) -> str | None:
    symbol = (symbol_or_underlying or "").strip().upper()
    if not symbol or len(symbol) > 12:
        return None
    if not all(char.isalnum() or char in {".", "-"} for char in symbol):
        return None
    return symbol


def _valid_declared_user_agent(value: str | None) -> bool:
    if value is None:
        return False
    cleaned = " ".join(value.strip().split())
    if len(cleaned) < 12 or len(cleaned) > 160:
        return False
    lowered = cleaned.lower()
    if "@" not in cleaned and "contact" not in lowered:
        return False
    if any(token in lowered for token in ("api_key", "access_token", "bearer ", "secret")):
        return False
    return True


def _payload_size_exceeds_cap(payload: Mapping[str, Any], cap_bytes: int) -> bool:
    if cap_bytes <= 0:
        return True
    return len(repr(payload).encode("utf-8")) > cap_bytes


def _respect_edgar_process_rate_limit() -> None:
    global _EDGAR_LAST_REQUEST_MONOTONIC
    with _EDGAR_PROCESS_RATE_LOCK:
        now = time.monotonic()
        elapsed = now - _EDGAR_LAST_REQUEST_MONOTONIC
        if elapsed < _EDGAR_PROCESS_RATE_LIMIT_SECONDS:
            time.sleep(_EDGAR_PROCESS_RATE_LIMIT_SECONDS - elapsed)
            now = time.monotonic()
        _EDGAR_LAST_REQUEST_MONOTONIC = now


def _resolve_sec_ticker_row(company_tickers: Mapping[str, Any], symbol: str) -> Mapping[str, Any] | None:
    rows: list[Mapping[str, Any]]
    if isinstance(company_tickers.get("data"), list):
        rows = [row for row in company_tickers["data"] if isinstance(row, Mapping)]
    else:
        rows = [row for row in company_tickers.values() if isinstance(row, Mapping)]
    exact_matches = [
        row for row in rows if str(row.get("ticker") or "").strip().upper() == symbol
    ]
    if len(exact_matches) != 1:
        return None
    return exact_matches[0]


def _format_cik_reference(value: object) -> str | None:
    raw = str(value).strip()
    if not raw.isdigit() or len(raw) > 10:
        return None
    cik_int = int(raw)
    if cik_int <= 0:
        return None
    return f"CIK {cik_int:010d}"


def _cik_digits_from_reference(value: str) -> str | None:
    raw = value.strip().upper()
    if raw.startswith("CIK "):
        raw = raw.removeprefix("CIK ").strip()
    if not raw.isdigit() or len(raw) != 10:
        return None
    return raw


def _normalize_edgar_profile_section(
    *,
    symbol: str,
    ticker_row: Mapping[str, Any],
    cik_reference: str,
    submissions: Mapping[str, Any],
    policy: EdgarCompanyProfileSourcePolicy,
) -> SavedPublicEvidenceSectionRead:
    company_name = _first_non_empty(submissions.get("name"), ticker_row.get("title"))
    ticker = _first_matching_value(submissions.get("tickers"), symbol) or symbol
    exchange = _first_non_empty(_first_sequence_value(submissions.get("exchanges")))
    sic_label = _first_non_empty(submissions.get("sicDescription"))
    fiscal_year_end = _format_fiscal_year_end(submissions.get("fiscalYearEnd"))

    facts = [
        _public_fact("company_name", "Company name", company_name, source_label=policy.source_label),
        _public_fact("ticker", "Ticker", ticker, source_label=policy.source_label),
        _public_fact("exchange", "Exchange", exchange, source_label=policy.source_label),
        _public_fact("cik_reference", "CIK reference", cik_reference, source_label=policy.source_label),
        _public_fact("sic_label", "SIC label", sic_label, source_label=policy.source_label),
        _public_fact("fiscal_year_end", "Fiscal year end", fiscal_year_end, source_label=policy.source_label),
    ]
    safe_facts = tuple(fact for fact in facts if fact is not None)
    useful_fact_keys = {fact.fact_key for fact in safe_facts if fact.value_label}
    if not {"company_name", "ticker", "cik_reference"}.issubset(useful_fact_keys):
        return _edgar_unavailable_section(
            source_label=policy.source_label,
            summary_label="SEC EDGAR company profile evidence is unavailable because required identity metadata was incomplete.",
            caveat_codes=("edgar_profile_metadata_incomplete",),
        )

    missing_optional = {"exchange", "sic_label", "fiscal_year_end"} - useful_fact_keys
    availability = "limited" if missing_optional else "available"
    caveats = ("edgar_profile_partial_metadata",) if missing_optional else ()
    return SavedPublicEvidenceSectionRead(
        section_key="public_company_profile",
        section_label="Public company profile",
        availability=availability,
        freshness_category="fresh",
        freshness_label="Collected from SEC EDGAR submissions metadata for this saved report",
        source_label=policy.source_label,
        source_key=policy.source_key,
        rights_status=policy.rights_status,
        collected_at=datetime.now(UTC),
        summary_label=f"SEC EDGAR profile metadata resolved for {ticker}.",
        facts=safe_facts,
        limitations=(
            "SEC EDGAR profile evidence is limited to structured company identity metadata.",
            policy.retention_label,
            policy.caveat_label,
        ),
        caveat_codes=caveats,
    )


def _public_fact(
    fact_key: str,
    fact_label: str,
    value_label: str | None,
    *,
    source_label: str,
) -> SavedPublicEvidenceFactRead | None:
    if value_label is None:
        return None
    return SavedPublicEvidenceFactRead(
        fact_key=fact_key,
        fact_label=fact_label,
        value_label=value_label,
        source_label=source_label,
    )


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return " ".join(value.strip().split())
    return None


def _first_sequence_value(value: object) -> object:
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return None


def _first_matching_value(value: object, symbol: str) -> str | None:
    if isinstance(value, (list, tuple)):
        for item in value:
            if str(item).strip().upper() == symbol:
                return symbol
    return None


def _format_fiscal_year_end(value: object) -> str | None:
    raw = _first_non_empty(value)
    if raw is None:
        return None
    digits = "".join(char for char in raw if char.isdigit())
    if len(digits) != 4:
        return raw
    return f"{digits[:2]}/{digits[2:]}"


def _edgar_unavailable_section(
    *,
    source_label: str,
    summary_label: str,
    caveat_codes: tuple[str, ...],
) -> SavedPublicEvidenceSectionRead:
    return SavedPublicEvidenceSectionRead(
        section_key="public_company_profile",
        section_label="Public company profile",
        availability="not_available",
        freshness_category="not_available",
        freshness_label="SEC EDGAR company profile evidence is not available for this saved report",
        source_label=source_label,
        rights_status="reviewed",
        summary_label=summary_label,
        limitations=("SEC EDGAR company profile evidence was not attached to this saved evidence package.",),
        caveat_codes=caveat_codes,
    )


def _public_package_limitations(profile: SavedPublicEvidenceSectionRead) -> tuple[str, ...]:
    if profile.availability in {"available", "limited"}:
        return (
            "Public company profile evidence is limited to reviewed structured identity metadata.",
            "Other public evidence sections remain unavailable until separately reviewed.",
        )
    return ("Public company profile evidence was unavailable for this saved evidence package.",)
