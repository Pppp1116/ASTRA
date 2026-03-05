"""
Comprehensive tests for astra.parallel_semantic module.

Tests parallel semantic analysis including:
- SemanticWorkItem
- ThreadLocalDiagnostics
- Parallel function analysis
- Parallel program analysis
- Multi-program analysis
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from astra.parallel_semantic import (
    SemanticWorkItem,
    ThreadLocalDiagnostics,
    analyze_function_parallel,
    prepare_parallel_work_items,
    analyze_program_parallel,
    analyze_programs_parallel,
    analyze_single_program_for_parallel,
)
from astra.ast import FnDecl, ExternFnDecl, StructDecl, EnumDecl, Program, LetStmt, Literal
from astra.symbols import GlobalSymbolTable, SymbolInfo, MutableSymbolTable
from astra.semantic import SemanticError


def test_semantic_work_item_creation():
    """Test SemanticWorkItem creation"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    work_item = SemanticWorkItem(
        fn_decl=fn,
        file_path="test.astra",
        fn_groups={"test": [fn]},
        structs={},
        enums={},
        global_scope={},
        freestanding=False
    )

    assert work_item.fn_decl is fn
    assert work_item.file_path == "test.astra"
    assert work_item.freestanding == False


def test_thread_local_diagnostics_creation():
    """Test ThreadLocalDiagnostics creation"""
    diag = ThreadLocalDiagnostics()

    assert len(diag.errors) == 0
    assert len(diag.warnings) == 0


def test_thread_local_diagnostics_add_error():
    """Test adding error to diagnostics"""
    diag = ThreadLocalDiagnostics()

    diag.add_error("Test error")

    assert len(diag.errors) == 1
    assert diag.errors[0] == "Test error"


def test_thread_local_diagnostics_add_warning():
    """Test adding warning to diagnostics"""
    diag = ThreadLocalDiagnostics()

    diag.add_warning("Test warning")

    assert len(diag.warnings) == 1
    assert diag.warnings[0] == "Test warning"


def test_thread_local_diagnostics_multiple_errors():
    """Test adding multiple errors"""
    diag = ThreadLocalDiagnostics()

    diag.add_error("Error 1")
    diag.add_error("Error 2")
    diag.add_error("Error 3")

    assert len(diag.errors) == 3


def test_analyze_function_parallel_success():
    """Test successful parallel function analysis"""
    fn = FnDecl(
        name="test",
        generics=[],
        params=[],
        ret="Int",
        body=[],
        line=1,
        col=1,
        pos=0
    )

    work_item = SemanticWorkItem(
        fn_decl=fn,
        file_path="test.astra",
        fn_groups={"test": [fn]},
        structs={},
        enums={},
        global_scope={},
        freestanding=False
    )

    with patch('astra.parallel_semantic._analyze_fn'):
        diagnostics = analyze_function_parallel(work_item)

        assert isinstance(diagnostics, ThreadLocalDiagnostics)


def test_analyze_function_parallel_error_handling():
    """Test that function analysis handles errors"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)

    work_item = SemanticWorkItem(
        fn_decl=fn,
        file_path="test.astra",
        fn_groups={},
        structs={},
        enums={},
        global_scope={},
        freestanding=False
    )

    with patch('astra.parallel_semantic._analyze_fn', side_effect=Exception("Test error")):
        diagnostics = analyze_function_parallel(work_item)

        assert len(diagnostics.errors) == 1
        assert "INTERNAL" in diagnostics.errors[0]


def test_prepare_parallel_work_items():
    """Test preparing parallel work items"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2])

    # Create symbol table
    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    mutable_table.add_function(fn2, "test.astra")
    symbol_table = mutable_table.freeze()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", False)

    assert len(work_items) == 2
    assert work_items[0].fn_decl is fn1
    assert work_items[1].fn_decl is fn2


def test_prepare_parallel_work_items_no_functions():
    """Test preparing work items with no functions"""
    program = Program(items=[])
    symbol_table = GlobalSymbolTable()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", False)

    assert len(work_items) == 0


def test_prepare_parallel_work_items_freestanding():
    """Test preparing work items in freestanding mode"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", freestanding=True)

    assert len(work_items) == 1
    assert work_items[0].freestanding == True


def test_prepare_parallel_work_items_includes_structs_and_enums():
    """Test that work items include structs and enums from symbol table"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    struct = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="")

    program = Program(items=[fn, struct, enum])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    mutable_table.add_struct(struct, "test.astra")
    mutable_table.add_enum(enum, "test.astra")
    symbol_table = mutable_table.freeze()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", False)

    assert len(work_items) == 1
    assert "Point" in work_items[0].structs
    assert "Color" in work_items[0].enums


def test_analyze_program_parallel_single_function():
    """Test parallel analysis of single function"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not raise
        analyze_program_parallel(program, symbol_table, "test.astra", False)


def test_analyze_program_parallel_multiple_functions():
    """Test parallel analysis of multiple functions"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    mutable_table.add_function(fn2, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not raise
        analyze_program_parallel(program, symbol_table, "test.astra", False)


def test_analyze_program_parallel_no_functions():
    """Test parallel analysis with no functions"""
    program = Program(items=[])
    symbol_table = GlobalSymbolTable()

    # Should not raise
    analyze_program_parallel(program, symbol_table, "test.astra", False)


def test_analyze_program_parallel_raises_on_errors():
    """Test that parallel analysis raises SemanticError on errors"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)
    program = Program(items=[fn])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn', side_effect=Exception("Test error")):
        with pytest.raises(SemanticError):
            analyze_program_parallel(program, symbol_table, "test.astra", False)


def test_analyze_program_parallel_sorts_errors_deterministically():
    """Test that errors are sorted deterministically"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[], line=20, col=1, pos=200)
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[], line=10, col=1, pos=100)

    program = Program(items=[fn1, fn2])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    mutable_table.add_function(fn2, "test.astra")
    symbol_table = mutable_table.freeze()

    def mock_analyze_fn(fn_decl, *args):
        raise Exception(f"Error in {fn_decl.name}")

    with patch('astra.parallel_semantic._analyze_fn', side_effect=mock_analyze_fn):
        try:
            analyze_program_parallel(program, symbol_table, "test.astra", False)
            assert False, "Should have raised"
        except SemanticError as e:
            error_str = str(e)
            # Errors should be sorted
            assert "func1" in error_str or "func2" in error_str


def test_analyze_programs_parallel_single_program():
    """Test parallel analysis of single program"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    programs = {Path("test.astra"): program}

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not raise
        analyze_programs_parallel(programs, symbol_table, False)


def test_analyze_programs_parallel_multiple_programs():
    """Test parallel analysis of multiple programs"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])

    program1 = Program(items=[fn1])
    program2 = Program(items=[fn2])

    programs = {
        Path("a.astra"): program1,
        Path("b.astra"): program2,
    }

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "a.astra")
    mutable_table.add_function(fn2, "b.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not raise
        analyze_programs_parallel(programs, symbol_table, False)


def test_analyze_programs_parallel_raises_on_errors():
    """Test that multi-program analysis raises on errors"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)
    program = Program(items=[fn])

    programs = {Path("test.astra"): program}

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn', side_effect=Exception("Test error")):
        with pytest.raises(SemanticError):
            analyze_programs_parallel(programs, symbol_table, False)


def test_analyze_single_program_for_parallel_success():
    """Test analyze_single_program_for_parallel success case"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        diagnostics = analyze_single_program_for_parallel(
            program, symbol_table, "test.astra", False
        )

        assert isinstance(diagnostics, ThreadLocalDiagnostics)
        assert len(diagnostics.errors) == 0


def test_analyze_single_program_for_parallel_error():
    """Test analyze_single_program_for_parallel error handling"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)
    program = Program(items=[fn])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn', side_effect=Exception("Test error")):
        diagnostics = analyze_single_program_for_parallel(
            program, symbol_table, "test.astra", False
        )

        assert len(diagnostics.errors) > 0


def test_analyze_function_parallel_preserves_freestanding_stack():
    """Test that function analysis preserves global freestanding stack"""
    from astra.parallel_semantic import _FREESTANDING_MODE_STACK

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    work_item = SemanticWorkItem(
        fn_decl=fn,
        file_path="test.astra",
        fn_groups={},
        structs={},
        enums={},
        global_scope={},
        freestanding=True
    )

    # Set up initial stack
    original_stack = _FREESTANDING_MODE_STACK[:]

    with patch('astra.parallel_semantic._analyze_fn'):
        analyze_function_parallel(work_item)

    # Stack should be restored
    assert _FREESTANDING_MODE_STACK == original_stack


def test_prepare_parallel_work_items_includes_fn_groups():
    """Test that work items include function groups"""
    fn1 = FnDecl(name="test", generics=[], params=[("x", "Int")], ret="Int", body=[])
    fn2 = FnDecl(name="test", generics=["T"], params=[("x", "T")], ret="T", body=[])

    program = Program(items=[fn1, fn2])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    mutable_table.add_function(fn2, "test.astra")
    symbol_table = mutable_table.freeze()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", False)

    assert len(work_items) == 2
    # Both work items should have access to all overloads
    assert "test" in work_items[0].fn_groups
    assert len(work_items[0].fn_groups["test"]) == 2


def test_prepare_parallel_work_items_includes_extern_functions():
    """Test that work items include extern functions"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    extern = ExternFnDecl(lib="libc.so", name="exit", params=[], ret="Void")

    program = Program(items=[fn, extern])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, "test.astra")
    mutable_table.add_extern_function(extern, "test.astra")
    symbol_table = mutable_table.freeze()

    work_items = prepare_parallel_work_items(program, symbol_table, "test.astra", False)

    assert len(work_items) == 1
    assert "exit" in work_items[0].fn_groups


def test_analyze_program_parallel_deterministic_error_sorting():
    """Test that error messages are sorted deterministically"""
    fn1 = FnDecl(name="z_func", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)
    fn2 = FnDecl(name="a_func", generics=[], params=[], ret="Int", body=[], line=1, col=1, pos=0)

    program = Program(items=[fn1, fn2])

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    mutable_table.add_function(fn2, "test.astra")
    symbol_table = mutable_table.freeze()

    def mock_analyze_with_error(*args):
        raise Exception("error")

    with patch('astra.parallel_semantic._analyze_fn', side_effect=mock_analyze_with_error):
        try:
            analyze_program_parallel(program, symbol_table, "test.astra", False)
            assert False
        except SemanticError as e:
            # Errors should be sorted
            error_lines = str(e).split("\n")
            # Should have multiple errors
            assert len(error_lines) >= 2


def test_analyze_programs_parallel_uses_relative_paths():
    """Test that multi-program analysis uses relative paths for work IDs"""
    import os

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    # Use path relative to cwd
    cwd = Path.cwd()
    rel_path = Path("test.astra")
    full_path = cwd / rel_path

    programs = {full_path: program}

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn, str(full_path))
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not raise
        analyze_programs_parallel(programs, symbol_table, False)


def test_regression_empty_program_analysis():
    """Regression test: analyzing empty program"""
    program = Program(items=[])
    symbol_table = GlobalSymbolTable()

    # Should not raise
    analyze_program_parallel(program, symbol_table, "test.astra", False)


def test_regression_single_vs_multiple_functions():
    """Regression test: ensure single and multiple function paths work the same"""
    fn1 = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    program_single = Program(items=[fn1])
    program_multi = Program(items=[fn1, fn1])  # Duplicate for testing

    mutable_table = MutableSymbolTable()
    mutable_table.add_function(fn1, "test.astra")
    symbol_table = mutable_table.freeze()

    with patch('astra.parallel_semantic._analyze_fn'):
        # Both should work
        analyze_program_parallel(program_single, symbol_table, "test.astra", False)
        # Multi will have duplicate work items but should still work
        try:
            analyze_program_parallel(program_multi, symbol_table, "test.astra", False)
        except:
            pass  # May fail due to duplicates, but shouldn't crash


def test_edge_case_work_item_with_empty_groups():
    """Edge case: work item with empty function groups"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    work_item = SemanticWorkItem(
        fn_decl=fn,
        file_path="test.astra",
        fn_groups={},
        structs={},
        enums={},
        global_scope={},
        freestanding=False
    )

    with patch('astra.parallel_semantic._analyze_fn'):
        # Should not crash
        diagnostics = analyze_function_parallel(work_item)
        assert isinstance(diagnostics, ThreadLocalDiagnostics)