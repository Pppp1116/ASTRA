import json
from pathlib import Path

from astra.layout_optimizer import load_profile, optimize_llvm_layout, write_profile_template


def test_profile_template_is_written(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ir = '''define i64 @foo() {
entry:
  br label %bb1
bb1:
  br label %bb2
bb2:
  ret i64 0
}
'''
    payload = write_profile_template(["foo", "bar"], ir)
    profile = tmp_path / ".build" / "astra-profile.json"
    assert profile.exists()
    parsed = json.loads(profile.read_text())
    assert parsed == payload
    assert "foo" in parsed["functions"]
    assert any(k.startswith("foo:") for k in parsed["edges"])


def test_optimize_layout_reorders_functions_by_hotness():
    ir = '''; ModuleID = 'x'

define i64 @cold() {
entry:
  ret i64 0
}

define i64 @hot() {
entry:
  ret i64 1
}
'''
    profile = {"functions": {"hot": 1000, "cold": 1}, "edges": {}, "indirect_calls": {}}
    out = optimize_llvm_layout(ir, profile)
    assert out.find("define i64 @hot()") < out.find("define i64 @cold()")


def test_load_profile_defaults_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data = load_profile()
    assert data == {"functions": {}, "edges": {}, "indirect_calls": {}}
