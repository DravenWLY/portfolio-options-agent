from importlib.machinery import ModuleSpec

import pytest

from app.services.tradingagents_adapter.dependency import (
    TradingAgentsDependencyResult,
    detect_tradingagents_dependency,
)


pytestmark = [pytest.mark.unit]


def test_detect_tradingagents_dependency_reports_available_without_importing() -> None:
    calls: list[str] = []

    def fake_find_spec(module_name: str) -> ModuleSpec:
        calls.append(module_name)
        return ModuleSpec(name=module_name, loader=None)

    result = detect_tradingagents_dependency(find_spec=fake_find_spec)

    assert isinstance(result, TradingAgentsDependencyResult)
    assert result.status == "available"
    assert result.available is True
    assert result.module_name == "tradingagents"
    assert result.detection_method == "importlib.util.find_spec"
    assert calls == ["tradingagents"]
    assert "not been imported or executed" in (result.message or "")
    assert "vendor" not in result.message.lower()


def test_detect_tradingagents_dependency_reports_missing_with_safe_guidance() -> None:
    def fake_find_spec(module_name: str) -> None:
        assert module_name == "tradingagents"
        return None

    result = detect_tradingagents_dependency(find_spec=fake_find_spec)

    assert result.status == "missing"
    assert result.available is False
    assert result.error_type is None
    assert "optional" in result.install_guidance.lower()
    assert "do not vendor" in result.install_guidance.lower()
    assert "not installed" in (result.message or "").lower()


def test_detect_tradingagents_dependency_reports_import_error_without_raising() -> None:
    def fake_find_spec(module_name: str) -> ModuleSpec | None:
        raise ImportError("synthetic import metadata failure")

    result = detect_tradingagents_dependency(find_spec=fake_find_spec)

    assert result.status == "import_error"
    assert result.available is False
    assert result.error_type == "ImportError"
    assert "deterministic app features remain available" in (result.message or "")
    assert "synthetic import metadata failure" not in repr(result)


def test_detect_tradingagents_dependency_accepts_custom_top_level_module_name() -> None:
    calls: list[str] = []

    def fake_find_spec(module_name: str) -> ModuleSpec:
        calls.append(module_name)
        return ModuleSpec(name=module_name, loader=None)

    result = detect_tradingagents_dependency(
        module_name=" tradingagents ",
        find_spec=fake_find_spec,
    )

    assert result.module_name == "tradingagents"
    assert result.status == "available"
    assert calls == ["tradingagents"]


def test_detect_tradingagents_dependency_rejects_dotted_module_name_before_find_spec() -> None:
    calls: list[str] = []

    def fake_find_spec(module_name: str) -> ModuleSpec:
        calls.append(module_name)
        return ModuleSpec(name=module_name, loader=None)

    with pytest.raises(ValueError, match="top-level module name"):
        detect_tradingagents_dependency(
            module_name="tradingagents.graph",
            find_spec=fake_find_spec,
        )

    assert calls == []


def test_detect_tradingagents_dependency_rejects_empty_module_name() -> None:
    with pytest.raises(ValueError, match="module_name must not be empty"):
        detect_tradingagents_dependency(module_name="  ", find_spec=lambda _: None)


def test_tradingagents_adapter_package_import_is_safe() -> None:
    import app.services.tradingagents_adapter as adapter

    assert adapter.detect_tradingagents_dependency is detect_tradingagents_dependency
