from astra.check import run_check_source


def test_check_emits_structured_type_mismatch_diagnostic_with_notes():
    src = 'fn main() -> Int { return "x"; }'
    res = run_check_source(src, filename="<mem>")
    assert not res.ok
    assert res.diagnostics
    first = res.diagnostics[0]
    assert first.code == "ASTRA-TYPE-0001"
    note_messages = {n.message for n in first.notes}
    assert any(msg.startswith("expected:") for msg in note_messages)
    assert any(msg.startswith("got:") for msg in note_messages)


def test_check_collects_multiple_semantic_errors():
    src = """
fn a() -> Int { return "x"; }
fn b() -> Int { return true; }
fn main() -> Int { return 0; }
"""
    res = run_check_source(src, filename="<mem>", collect_errors=True)
    assert not res.ok
    assert len(res.diagnostics) >= 2
