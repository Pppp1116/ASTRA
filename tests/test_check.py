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


def test_check_reports_lex_error_with_phase_code_and_span():
    src = 'fn main() -> Int { let s = "unterminated; return 0; }'
    res = run_check_source(src, filename="mem://lex.astra")
    assert not res.ok
    first = res.diagnostics[0]
    assert first.phase == "LEX"
    assert first.code == "ASTRA-LEX-0001"
    assert first.span.filename == "mem://lex.astra"
    assert first.span.line == 1
    assert first.span.col > 1


def test_check_reports_parse_error_with_phase_code_and_span():
    src = "fn main() -> Int { let x = ; return 0; }"
    res = run_check_source(src, filename="mem://parse.astra")
    assert not res.ok
    first = res.diagnostics[0]
    assert first.phase == "PARSE"
    assert first.code in {"ASTRA-PARSE-0001", "ASTRA-PARSE-0002"}
    assert first.span.filename == "mem://parse.astra"
    assert first.span.line == 1
    assert first.span.col > 1


def test_check_reports_c_style_for_as_parse_error():
    src = "fn main() -> Int { for let i = 0; i < 3; i += 1 { } return 0; }"
    res = run_check_source(src, filename="mem://for.astra")
    assert not res.ok
    first = res.diagnostics[0]
    assert first.phase == "PARSE"
    assert first.code.startswith("ASTRA-PARSE-")
    assert "for expects `for <ident> in <expr> { ... }`" in first.message
