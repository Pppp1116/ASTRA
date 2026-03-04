"""
Comprehensive tests for astra.parallel_ir module.

Tests parallel IR generation and optimization including:
- IROptimizationWorkItem
- ThreadLocalIROptimizer
- Parallel program optimization
- Parallel IR generation
- ParallelIROptimizer interface
"""

import pytest
from unittest.mock import MagicMock, patch

from astra.parallel_ir import (
    IROptimizationWorkItem,
    ThreadLocalIROptimizer,
    prepare_ir_optimization_work_items,
    optimize_program_parallel,
    generate_ir_parallel,
    _optimize_function_worker,
    _generate_ir_worker,
    ParallelIROptimizer,
)
from astra.ast import Program, FnDecl, LetStmt, Literal, Name


def test_ir_optimization_work_item_creation():
    """Test IROptimizationWorkItem creation"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    context = {"opt_level": 2}

    work_item = IROptimizationWorkItem(fn_decl=fn, context=context)

    assert work_item.fn_decl is fn
    assert work_item.context == context


def test_thread_local_ir_optimizer_creation():
    """Test ThreadLocalIROptimizer creation"""
    optimizer = ThreadLocalIROptimizer()

    assert len(optimizer.local_context) == 0
    assert len(optimizer.optimized_functions) == 0


def test_thread_local_ir_optimizer_optimize_function():
    """Test optimizing a single function"""
    optimizer = ThreadLocalIROptimizer()

    fn = FnDecl(
        name="test",
        generics=[],
        params=[],
        ret="Int",
        body=[
            LetStmt(name="x", expr=Literal(value=1), mut=False),
            LetStmt(name="y", expr=Literal(value=2), mut=False),
        ]
    )
    work_item = IROptimizationWorkItem(fn_decl=fn, context={})

    result = optimizer.optimize_function(work_item)

    assert isinstance(result, FnDecl)
    assert result.name == "test"


def test_thread_local_ir_optimizer_stores_context():
    """Test that optimizer stores context"""
    optimizer = ThreadLocalIROptimizer()

    context = {"opt_level": 2, "inline_threshold": 100}
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    work_item = IROptimizationWorkItem(fn_decl=fn, context=context)

    optimizer.optimize_function(work_item)

    assert optimizer.local_context == context


def test_thread_local_ir_optimizer_exception_handling():
    """Test that optimizer handles exceptions gracefully"""
    optimizer = ThreadLocalIROptimizer()

    # Create a function that might cause issues during optimization
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    work_item = IROptimizationWorkItem(fn_decl=fn, context={})

    # Mock optimize_program to raise an exception
    with patch('astra.parallel_ir.optimize_program', side_effect=Exception("Test error")):
        result = optimizer.optimize_function(work_item)

        # Should return original function on error
        assert result is fn


def test_prepare_ir_optimization_work_items():
    """Test preparing work items for optimization"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Void", body=[])

    program = Program(items=[fn1, fn2])
    context = {"opt_level": 2}

    work_items = prepare_ir_optimization_work_items(program, context)

    assert len(work_items) == 2
    assert work_items[0].fn_decl is fn1
    assert work_items[1].fn_decl is fn2
    assert all(item.context == context for item in work_items)


def test_prepare_ir_optimization_work_items_no_functions():
    """Test preparing work items with no functions"""
    program = Program(items=[])
    work_items = prepare_ir_optimization_work_items(program, {})

    assert len(work_items) == 0


def test_optimize_program_parallel_single_function():
    """Test parallel optimization with single function"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    result = optimize_program_parallel(program)

    assert isinstance(result, Program)
    assert len(result.items) == 1
    assert isinstance(result.items[0], FnDecl)


def test_optimize_program_parallel_multiple_functions():
    """Test parallel optimization with multiple functions"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])
    fn3 = FnDecl(name="func3", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2, fn3])

    result = optimize_program_parallel(program)

    assert isinstance(result, Program)
    assert len(result.items) == 3


def test_optimize_program_parallel_no_functions():
    """Test parallel optimization with no functions"""
    program = Program(items=[])

    result = optimize_program_parallel(program)

    assert result is program


def test_optimize_program_parallel_with_context():
    """Test parallel optimization with optimization context"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])
    context = {"opt_level": 3, "inline": True}

    result = optimize_program_parallel(program, context)

    assert isinstance(result, Program)


def test_optimize_program_parallel_preserves_non_function_items():
    """Test that non-function items are preserved"""
    from astra.ast import StructDecl

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    struct = StructDecl(name="Point", generics=[], fields=[("x", "Int"), ("y", "Int")], methods=[], packed=False)

    program = Program(items=[fn, struct])

    result = optimize_program_parallel(program)

    assert len(result.items) == 2
    # Struct should be preserved
    assert any(isinstance(item, StructDecl) for item in result.items)


def test_optimize_function_worker():
    """Test _optimize_function_worker function"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    work_item = IROptimizationWorkItem(fn_decl=fn, context={})

    result = _optimize_function_worker(work_item)

    assert isinstance(result, FnDecl)


def test_generate_ir_parallel_single_function():
    """Test parallel IR generation with single function"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    def mock_ir_generator(fn, context):
        return f"IR for {fn.name}"

    result = generate_ir_parallel(program, mock_ir_generator)

    assert "test" in result
    assert result["test"] == "IR for test"


def test_generate_ir_parallel_multiple_functions():
    """Test parallel IR generation with multiple functions"""
    fn1 = FnDecl(name="func1", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="func2", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2])

    def mock_ir_generator(fn, context):
        return f"IR for {fn.name}"

    result = generate_ir_parallel(program, mock_ir_generator)

    assert len(result) == 2
    assert "func1" in result
    assert "func2" in result


def test_generate_ir_parallel_no_functions():
    """Test parallel IR generation with no functions"""
    program = Program(items=[])

    def mock_ir_generator(fn, context):
        return "IR"

    result = generate_ir_parallel(program, mock_ir_generator)

    assert result == {}


def test_generate_ir_parallel_with_context():
    """Test parallel IR generation with generation context"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    context = {"target": "x86_64", "debug": True}

    def mock_ir_generator(fn, ctx):
        assert ctx == context
        return "IR"

    result = generate_ir_parallel(program, mock_ir_generator, context)

    assert "test" in result


def test_generate_ir_parallel_handles_errors():
    """Test that IR generation handles errors gracefully"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    def failing_ir_generator(fn, context):
        raise ValueError("Test error")

    result = generate_ir_parallel(program, failing_ir_generator)

    assert "test" in result
    assert "ERROR" in result["test"]


def test_generate_ir_worker():
    """Test _generate_ir_worker function"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    def mock_ir_generator(fn, context):
        return "IR"

    result = _generate_ir_worker(fn, mock_ir_generator, {})

    assert result == "IR"


def test_generate_ir_worker_error_handling():
    """Test _generate_ir_worker error handling"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])

    def failing_ir_generator(fn, context):
        raise ValueError("Test error")

    result = _generate_ir_worker(fn, failing_ir_generator, {})

    assert "ERROR" in result


def test_parallel_ir_optimizer_creation():
    """Test ParallelIROptimizer creation"""
    optimizer = ParallelIROptimizer()

    assert len(optimizer.optimization_context) == 0
    assert len(optimizer.generation_context) == 0


def test_parallel_ir_optimizer_set_optimization_context():
    """Test setting optimization context"""
    optimizer = ParallelIROptimizer()
    context = {"opt_level": 2}

    optimizer.set_optimization_context(context)

    assert optimizer.optimization_context == context


def test_parallel_ir_optimizer_set_generation_context():
    """Test setting generation context"""
    optimizer = ParallelIROptimizer()
    context = {"target": "arm64"}

    optimizer.set_generation_context(context)

    assert optimizer.generation_context == context


def test_parallel_ir_optimizer_optimize_program():
    """Test ParallelIROptimizer.optimize_program"""
    optimizer = ParallelIROptimizer()
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    result = optimizer.optimize_program(program)

    assert isinstance(result, Program)


def test_parallel_ir_optimizer_generate_ir():
    """Test ParallelIROptimizer.generate_ir"""
    optimizer = ParallelIROptimizer()
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    def mock_ir_generator(fn, context):
        return "IR"

    result = optimizer.generate_ir(program, mock_ir_generator)

    assert "test" in result


def test_parallel_ir_optimizer_uses_context():
    """Test that ParallelIROptimizer uses set contexts"""
    optimizer = ParallelIROptimizer()
    optimizer.set_optimization_context({"opt_level": 2})
    optimizer.set_generation_context({"target": "x86_64"})

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    # Test optimization uses context
    result = optimizer.optimize_program(program)
    assert isinstance(result, Program)

    # Test IR generation uses context
    def mock_ir_generator(fn, context):
        assert "target" in context
        return "IR"

    result = optimizer.generate_ir(program, mock_ir_generator)
    assert "test" in result


def test_optimize_program_parallel_fallback_on_error():
    """Test that optimization falls back to original on error"""
    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    program = Program(items=[fn])

    # Mock the worker to raise an exception
    with patch('astra.parallel_ir._optimize_function_worker', side_effect=Exception("Test error")):
        result = optimize_program_parallel(program)

        # Should still return a program
        assert isinstance(result, Program)


def test_generate_ir_parallel_uses_function_names_as_keys():
    """Test that IR results use function names as keys"""
    fn1 = FnDecl(name="add", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="subtract", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2])

    def mock_ir_generator(fn, context):
        return f"IR_{fn.name}"

    result = generate_ir_parallel(program, mock_ir_generator)

    # Keys should be function names
    assert "add" in result
    assert "subtract" in result
    assert result["add"] == "IR_add"
    assert result["subtract"] == "IR_subtract"


def test_optimize_program_parallel_preserves_function_order():
    """Test that optimization preserves function order"""
    fn1 = FnDecl(name="first", generics=[], params=[], ret="Int", body=[])
    fn2 = FnDecl(name="second", generics=[], params=[], ret="Int", body=[])
    fn3 = FnDecl(name="third", generics=[], params=[], ret="Int", body=[])

    program = Program(items=[fn1, fn2, fn3])

    result = optimize_program_parallel(program)

    # Order should be preserved
    assert result.items[0].name == "first"
    assert result.items[1].name == "second"
    assert result.items[2].name == "third"


def test_thread_local_ir_optimizer_copy_function():
    """Test _copy_function method"""
    optimizer = ThreadLocalIROptimizer()

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    copied = optimizer._copy_function(fn)

    # Should be a deep copy
    assert copied is not fn
    assert copied.name == fn.name


def test_regression_ir_generation_empty_program():
    """Regression test: IR generation with empty program"""
    program = Program(items=[])

    def mock_ir_generator(fn, context):
        return "IR"

    result = generate_ir_parallel(program, mock_ir_generator)

    assert result == {}


def test_regression_optimization_preserves_metadata():
    """Regression test: optimization preserves function metadata"""
    fn = FnDecl(
        name="test",
        generics=["T"],
        params=[("x", "T")],
        ret="T",
        body=[],
        pub=True,
        async_fn=True,
        doc="Test function"
    )

    program = Program(items=[fn])

    result = optimize_program_parallel(program)

    optimized_fn = result.items[0]
    assert optimized_fn.name == "test"
    assert optimized_fn.pub == True
    assert optimized_fn.async_fn == True
    assert optimized_fn.doc == "Test function"


def test_edge_case_mixed_items_program():
    """Edge case: program with mixed item types"""
    from astra.ast import StructDecl, EnumDecl

    fn = FnDecl(name="test", generics=[], params=[], ret="Int", body=[])
    struct = StructDecl(name="Point", generics=[], fields=[], methods=[], packed=False)
    enum = EnumDecl(name="Color", generics=[], variants=[], doc="")

    program = Program(items=[struct, fn, enum])

    result = optimize_program_parallel(program)

    # All items should be preserved
    assert len(result.items) == 3
    assert isinstance(result.items[0], StructDecl)
    assert isinstance(result.items[1], FnDecl)
    assert isinstance(result.items[2], EnumDecl)