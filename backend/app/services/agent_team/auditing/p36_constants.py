"""Shared reviewed constants for P36 prompt and output gates."""

P36_ATTRIBUTION_MARKERS: tuple[str, ...] = (
    "the saved",
    "per this run's",
    "computed from",
    "calculation",
    "the freshness inventory",
    "in conventional",
)

# The PM synthesizes accepted sections rather than independently interpreting
# a source snapshot. Keep its attribution vocabulary separate so analyst gates
# continue to require calculation/source attribution.
P36_PM_ATTRIBUTION_MARKERS: tuple[str, ...] = (
    *P36_ATTRIBUTION_MARKERS,
    "section",
    "the deterministic findings",
    "the analysts",
    "per the",
)

# P36 F-6 treats these as ordinary topic vocabulary, never as identifiers by
# themselves. This constant governs only the PM's accepted-section prompt
# projection; the identifier gate retains its independent ambiguity checks.
P36_F6_VOCABULARY_ONLY_TOKENS: frozenset[str] = frozenset(
    {"account", "holdings", "cash", "positions", "portfolio", "exposure", "nickname"}
)
