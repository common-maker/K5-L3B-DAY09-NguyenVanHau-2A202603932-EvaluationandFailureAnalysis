"""Regression test derived from trace case C-002@11 (FM-03: ticket_trust)."""

import pytest

from pydantic_evals.evaluators import EvaluatorContext

from lab9 import graders, trace_case

pytestmark = pytest.mark.student


def _ctx(case: dict) -> EvaluatorContext:
    return EvaluatorContext(
        name="C-002@11",
        inputs={},
        metadata=None,
        expected_output=case["label"],
        output=case["trial"],
        duration=0.0,
        _span_tree=None,
        attributes={},
        metrics={},
    )


def test_c002_seed11_trace_case_catches_regression_and_passes_fixed():
    bad = trace_case.investigate("seeded_regression", "C-002", 11)
    bad_ctx = _ctx(bad)
    assert bad["trial"]["lab8_pass"] is False
    assert graders.DbFactKept().evaluate(bad_ctx).value is False
    assert graders.RefundAmountCorrect().evaluate(bad_ctx).value is False

    good = trace_case.investigate("fixed", "C-002", 11)
    good_ctx = _ctx(good)
    assert good["trial"]["lab8_pass"] is True
    assert graders.DbFactKept().evaluate(good_ctx).value is True
    assert graders.RefundAmountCorrect().evaluate(good_ctx).value is True
