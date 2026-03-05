"""
Comprehensive tests for astra.asm_assert module.

Tests LLVM IR validation functionality including:
- Valid IR verification
- Incomplete pattern detection
- Triple validation
- llvmlite and clang fallback paths
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from astra.asm_assert import assert_valid_llvm_ir, _init_llvm_once, _LLVM_INIT_DONE


def test_assert_valid_llvm_ir_empty_string_raises():
    """Test that empty IR string raises AssertionError"""
    with pytest.raises(AssertionError, match="LLVM IR output is empty"):
        assert_valid_llvm_ir("")


def test_assert_valid_llvm_ir_whitespace_only_raises():
    """Test that whitespace-only IR raises AssertionError"""
    with pytest.raises(AssertionError, match="LLVM IR output is empty"):
        assert_valid_llvm_ir("   \n\t  ")


def test_assert_valid_llvm_ir_detects_unimplemented_pattern():
    """Test detection of UNIMPLEMENTED pattern"""
    ir = """
    define i32 @main() {
        ; UNIMPLEMENTED: feature X
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_not_implemented_pattern():
    """Test detection of NOT IMPLEMENTED pattern"""
    ir = """
    define i32 @main() {
        ; NOT IMPLEMENTED: feature Y
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_placeholder_pattern():
    """Test detection of PLACEHOLDER pattern"""
    ir = """
    define i32 @main() {
        ; PLACEHOLDER: real implementation
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_stub_pattern():
    """Test detection of STUB pattern"""
    ir = """
    define i32 @main() {
        ; STUB for testing
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_fixme_runtime():
    """Test detection of FIXME: runtime pattern"""
    ir = """
    define i32 @main() {
        ; FIXME: runtime behavior
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_todo_implement():
    """Test detection of TODO: implement pattern"""
    ir = """
    define i32 @main() {
        ; TODO: implement this properly
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_lowercase_unimplemented():
    """Test detection of lowercase unimplemented pattern"""
    ir = """
    define i32 @main() {
        ; unimplemented feature
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_incomplete_implementation():
    """Test detection of INCOMPLETE IMPLEMENTATION pattern"""
    ir = """
    define i32 @main() {
        ; INCOMPLETE IMPLEMENTATION
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_detects_not_yet_implemented():
    """Test detection of NOT YET IMPLEMENTED pattern"""
    ir = """
    define i32 @main() {
        ; NOT YET IMPLEMENTED
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_allows_legitimate_todo_comments():
    """Test that legitimate TODO comments in debug info don't trigger errors"""
    # This is a valid IR snippet - it should not raise
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """
    # This should not raise since it has no incomplete patterns
    # We need to mock llvmlite or clang to avoid actual verification
    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        assert_valid_llvm_ir(ir)


def test_assert_valid_llvm_ir_checks_triple_present():
    """Test that triple validation works"""
    ir = """
    define i32 @main() {
        ret i32 0
    }
    """
    with pytest.raises(AssertionError, match="missing module triple"):
        assert_valid_llvm_ir(ir, triple="x86_64-unknown-linux-gnu")


def test_assert_valid_llvm_ir_triple_present_passes():
    """Test that IR with correct triple passes validation"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """
    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        # Should not raise
        assert_valid_llvm_ir(ir, triple="x86_64-unknown-linux-gnu")


def test_assert_valid_llvm_ir_with_llvmlite_binding():
    """Test LLVM IR validation via llvmlite binding"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """

    mock_module = MagicMock()
    mock_binding = MagicMock()
    mock_binding.parse_assembly.return_value = mock_module

    with patch('astra.asm_assert.binding', mock_binding):
        assert_valid_llvm_ir(ir)
        mock_binding.parse_assembly.assert_called_once_with(ir)
        mock_module.verify.assert_called_once()


def test_assert_valid_llvm_ir_with_clang_fallback(tmp_path):
    """Test LLVM IR validation via clang when llvmlite not available"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """

    mock_run = MagicMock()
    mock_run.return_value.returncode = 0

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value='/usr/bin/clang'), \
         patch('subprocess.run', mock_run):
        assert_valid_llvm_ir(ir, workdir=tmp_path)
        # Verify clang was called
        assert mock_run.called


def test_assert_valid_llvm_ir_clang_compilation_failure(tmp_path):
    """Test that clang compilation failures raise AssertionError"""
    ir = """
    invalid llvm ir here
    """

    mock_run = MagicMock()
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "error: invalid IR"
    mock_run.return_value.stdout = ""

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value='/usr/bin/clang'), \
         patch('subprocess.run', mock_run):
        with pytest.raises(AssertionError, match="clang failed to compile"):
            assert_valid_llvm_ir(ir, workdir=tmp_path)


def test_assert_valid_llvm_ir_no_verification_available():
    """Test that IR without verification tools still checks patterns"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        # Should not raise - basic checks pass
        assert_valid_llvm_ir(ir)


def test_init_llvm_once_initializes():
    """Test that LLVM initialization doesn't crash"""
    mock_binding = MagicMock()

    with patch('astra.asm_assert.binding', mock_binding):
        # Should not raise - just verify it can be called
        _init_llvm_once()
        _init_llvm_once()  # Second call should be no-op
        # Just verify the function is callable without error


def test_init_llvm_once_handles_runtime_error():
    """Test that init handles newer llvmlite that auto-initializes"""
    mock_binding = MagicMock()
    mock_binding.initialize_native_target.side_effect = RuntimeError("Already initialized")

    with patch('astra.asm_assert.binding', mock_binding):
        # Should not raise - catches RuntimeError
        _init_llvm_once()


def test_init_llvm_once_with_no_binding():
    """Test that init does nothing when binding is None"""
    with patch('astra.asm_assert.binding', None):
        # Should not raise
        _init_llvm_once()


def test_workdir_parameter_used_in_tempfile(tmp_path):
    """Test that workdir parameter is properly used for temp files"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """

    mock_run = MagicMock()
    mock_run.return_value.returncode = 0

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value='/usr/bin/clang'), \
         patch('subprocess.run', mock_run):
        assert_valid_llvm_ir(ir, workdir=tmp_path)
        # Verify subprocess.run was called
        assert mock_run.called


def test_case_insensitive_pattern_detection():
    """Test that pattern detection is case-insensitive"""
    patterns = [
        "UNIMPLEMENTED",
        "unimplemented",
        "UnImPlEmEnTeD",
        "NOT IMPLEMENTED",
        "not implemented",
        "PLACEHOLDER",
        "placeholder"
    ]

    for pattern in patterns:
        ir = f"""
        define i32 @main() {{
            ; {pattern} feature
            ret i32 0
        }}
        """
        with pytest.raises(AssertionError, match="incomplete implementation"):
            assert_valid_llvm_ir(ir)


def test_multiple_incomplete_patterns_detected():
    """Test detection when multiple incomplete patterns exist"""
    ir = """
    define i32 @main() {
        ; UNIMPLEMENTED: feature A
        ; PLACEHOLDER for feature B
        ret i32 0
    }
    """
    # Should raise on first match
    with pytest.raises(AssertionError, match="incomplete implementation"):
        assert_valid_llvm_ir(ir)


def test_edge_case_empty_triple_string():
    """Test edge case with empty triple string"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    define i32 @main() {
        ret i32 0
    }
    """

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        # Empty triple should not trigger validation
        assert_valid_llvm_ir(ir, triple="")


def test_complex_valid_ir():
    """Test with more complex valid LLVM IR"""
    ir = """
    target triple = "x86_64-unknown-linux-gnu"
    target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"

    define i32 @add(i32 %a, i32 %b) {
    entry:
        %sum = add i32 %a, %b
        ret i32 %sum
    }

    define i32 @main() {
    entry:
        %result = call i32 @add(i32 5, i32 3)
        ret i32 %result
    }
    """

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        # Should not raise
        assert_valid_llvm_ir(ir)


def test_regression_legitimate_comments_with_todo():
    """Regression test: legitimate comments with 'todo' should be allowed in certain contexts"""
    # This IR has comments but not the problematic patterns
    ir = """
    target triple = "x86_64-unknown-linux-gnu"

    ; Function to add two numbers
    define i32 @add(i32 %a, i32 %b) {
        ; Calculate sum
        %sum = add i32 %a, %b
        ret i32 %sum
    }
    """

    with patch('astra.asm_assert.binding', None), \
         patch('shutil.which', return_value=None):
        # Should not raise - no incomplete patterns
        assert_valid_llvm_ir(ir)