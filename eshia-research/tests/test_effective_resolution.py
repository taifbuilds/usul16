"""Unit tests for the effective-resolution overlay (admin decision over rank-1)."""

import pytest

from eshia_research.models import PersonResolutionDecision
from eshia_research.rijal.effective_resolution import apply_admin_decision


def _decision(decision_type: str, selected_person_id: int | None = None):
    return PersonResolutionDecision(
        chain_node_id=1,
        selected_person_id=selected_person_id,
        decision_type=decision_type,
        confidence_tier="high",
        reviewer="codex-admin-external-v1",
        resolver_version="tamyiz_b1",
    )


def test_no_decision_passes_machine_through():
    eff = apply_admin_decision("resolved", 42, None)
    assert eff.person_id == 42
    assert eff.status == "resolved"
    assert eff.source == "machine"
    assert eff.confident is True


def test_machine_ambiguous_is_not_confident():
    eff = apply_admin_decision("ambiguous", 42, None)
    assert eff.confident is False


def test_machine_resolved_without_person_is_not_confident():
    eff = apply_admin_decision("resolved", None, None)
    assert eff.confident is False


def test_via_collective_is_confident():
    assert apply_admin_decision("via_collective", 7, None).confident is True


def test_override_replaces_person_and_promotes_ambiguous():
    # An ambiguous machine pick + admin override becomes confident on the target.
    eff = apply_admin_decision("ambiguous", 42, _decision("approve_external_override", 99))
    assert eff.person_id == 99
    assert eff.status == "approved_override"
    assert eff.source == "admin"
    assert eff.confident is True


def test_override_with_null_target_is_not_confident():
    eff = apply_admin_decision("resolved", 42, _decision("approve_external_override", None))
    assert eff.person_id is None
    assert eff.confident is False


def test_approve_current_keeps_machine_person_when_no_selected():
    eff = apply_admin_decision("resolved", 42, _decision("approve_current"))
    assert eff.person_id == 42
    assert eff.status == "approved_current"
    assert eff.confident is True


def test_keep_ambiguous_demotes():
    eff = apply_admin_decision("resolved", 42, _decision("keep_ambiguous"))
    assert eff.person_id is None
    assert eff.status == "kept_ambiguous"
    assert eff.confident is False


def test_flag_text_or_chain_issue_demotes():
    eff = apply_admin_decision("resolved", 42, _decision("flag_text_or_chain_issue"))
    assert eff.confident is False
    assert eff.status == "text_or_chain_issue"


@pytest.mark.parametrize("dtype", ["needs_external_review", "flag_contradiction", "unknown_future_type"])
def test_unknown_decision_types_pass_through_to_machine(dtype):
    # Advisory decisions must never silently demote a confident machine pick.
    eff = apply_admin_decision("resolved", 42, _decision(dtype))
    assert eff.person_id == 42
    assert eff.source == "machine"
    assert eff.confident is True
