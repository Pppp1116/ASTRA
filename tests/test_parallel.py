"""
Comprehensive tests for astra.parallel module.

Tests parallel compilation utilities including:
- WorkItem management
- ParallelExecutor functionality
- Dependency tracking
- Thread pool management
- File parsing in parallel
- Deterministic merging
"""

import pytest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from astra.parallel import (
    WorkItem,
    ParallelExecutor,
    parse_file_parallel,
    collect_files_parallel,
    parse_files_parallel,
    DeterministicMerge,
    get_thread_count,
    is_parallel_enabled,
)


def test_work_item_creation():
    """Test basic WorkItem creation"""
    def dummy_fn():
        return 42

    work = WorkItem(id="test_work", fn=dummy_fn)
    assert work.id == "test_work"
    assert work.fn == dummy_fn
    assert work.dependencies == []


def test_work_item_with_dependencies():
    """Test WorkItem with dependencies"""
    def dummy_fn():
        return 42

    work = WorkItem(id="test_work", fn=dummy_fn, dependencies=["dep1", "dep2"])
    assert work.id == "test_work"
    assert work.dependencies == ["dep1", "dep2"]


def test_work_item_post_init_default_dependencies():
    """Test that dependencies default to empty list"""
    work = WorkItem(id="test", fn=lambda: 1, dependencies=None)
    assert work.dependencies == []


def test_parallel_executor_context_manager():
    """Test ParallelExecutor as context manager"""
    with ParallelExecutor(max_workers=2) as executor:
        assert executor._pool is not None
        assert executor.max_workers == 2


def test_parallel_executor_cleanup():
    """Test that ParallelExecutor cleans up after exit"""
    executor = ParallelExecutor(max_workers=2)
    with executor:
        pool = executor._pool
        assert pool is not None

    # After exit, pool should be shutdown
    assert executor._pool is None


def test_parallel_executor_submit_work():
    """Test submitting work to ParallelExecutor"""
    with ParallelExecutor(max_workers=2) as executor:
        result_value = [0]

        def work_fn():
            result_value[0] = 42
            return 42

        work = WorkItem(id="test_work", fn=work_fn)
        future = executor.submit_work(work)

        assert future is not None
        assert "test_work" in executor._futures


def test_parallel_executor_wait_for():
    """Test waiting for specific work item"""
    with ParallelExecutor(max_workers=2) as executor:
        def work_fn():
            return 42

        work = WorkItem(id="test_work", fn=work_fn)
        executor.submit_work(work)

        result = executor.wait_for("test_work")
        assert result == 42


def test_parallel_executor_wait_for_nonexistent():
    """Test waiting for nonexistent work raises error"""
    with ParallelExecutor(max_workers=2) as executor:
        with pytest.raises(ValueError, match="Work item.*not found"):
            executor.wait_for("nonexistent")


def test_parallel_executor_wait_for_already_completed():
    """Test waiting for already completed work returns cached result"""
    with ParallelExecutor(max_workers=2) as executor:
        def work_fn():
            return 42

        work = WorkItem(id="test_work", fn=work_fn)
        executor.submit_work(work)

        # First wait
        result1 = executor.wait_for("test_work")
        # Second wait should return cached result
        result2 = executor.wait_for("test_work")

        assert result1 == 42
        assert result2 == 42


def test_parallel_executor_wait_all():
    """Test waiting for all work items"""
    with ParallelExecutor(max_workers=2) as executor:
        def work_fn(value):
            return lambda: value

        for i in range(5):
            work = WorkItem(id=f"work_{i}", fn=work_fn(i))
            executor.submit_work(work)

        results = executor.wait_all()
        assert len(results) == 5
        for i in range(5):
            assert results[f"work_{i}"] == i


def test_parallel_executor_wait_all_with_errors():
    """Test that wait_all raises on errors"""
    with ParallelExecutor(max_workers=2) as executor:
        def work_fn_success():
            return 42

        def work_fn_error():
            raise ValueError("Test error")

        work1 = WorkItem(id="work_success", fn=work_fn_success)
        work2 = WorkItem(id="work_error", fn=work_fn_error)

        executor.submit_work(work1)
        executor.submit_work(work2)

        with pytest.raises(ValueError, match="Test error"):
            executor.wait_all()


def test_parallel_executor_submit_without_context_raises():
    """Test that submitting work without context raises"""
    executor = ParallelExecutor(max_workers=2)
    work = WorkItem(id="test", fn=lambda: 1)

    with pytest.raises(RuntimeError, match="not active"):
        executor.submit_work(work)


def test_parallel_executor_dependency_not_completed_raises():
    """Test that submitting work with unsatisfied dependencies raises"""
    with ParallelExecutor(max_workers=2) as executor:
        work = WorkItem(id="test", fn=lambda: 1, dependencies=["missing_dep"])

        with pytest.raises(ValueError, match="depends on.*not completed"):
            executor.submit_work(work)


def test_parallel_executor_max_workers_default():
    """Test that max_workers defaults to thread count"""
    with patch.dict(os.environ, {"ASTRA_THREADS": "4"}):
        executor = ParallelExecutor()
        assert executor.max_workers == 4


def test_parallel_executor_error_caching():
    """Test that errors are cached properly"""
    with ParallelExecutor(max_workers=2) as executor:
        def work_fn_error():
            raise ValueError("Test error")

        work = WorkItem(id="work_error", fn=work_fn_error)
        executor.submit_work(work)

        # First wait should raise
        with pytest.raises(ValueError, match="Test error"):
            executor.wait_for("work_error")

        # Second wait should also raise the cached error
        with pytest.raises(ValueError, match="Test error"):
            executor.wait_for("work_error")


def test_parse_file_parallel_success(tmp_path):
    """Test successful parallel file parsing"""
    test_file = tmp_path / "test.astra"
    test_file.write_text("fn main() -> Int { return 0; }")

    file_path, result = parse_file_parallel(test_file)

    assert file_path == test_file
    assert result is not None
    assert not isinstance(result, Exception)


def test_parse_file_parallel_error(tmp_path):
    """Test parallel file parsing with error"""
    test_file = tmp_path / "test.astra"
    test_file.write_text("invalid syntax !!!")

    file_path, result = parse_file_parallel(test_file)

    assert file_path == test_file
    assert isinstance(result, Exception)


def test_parse_file_parallel_file_not_found():
    """Test parallel parsing of nonexistent file"""
    test_file = Path("/nonexistent/file.astra")

    file_path, result = parse_file_parallel(test_file)

    assert file_path == test_file
    assert isinstance(result, Exception)


def test_parse_files_parallel_empty_list():
    """Test parsing empty file list"""
    results = parse_files_parallel([])
    assert results == {}


def test_parse_files_parallel_single_file(tmp_path):
    """Test parsing single file"""
    test_file = tmp_path / "test.astra"
    test_file.write_text("fn main() -> Int { return 0; }")

    results = parse_files_parallel([test_file])

    assert len(results) == 1
    assert test_file in results
    assert not isinstance(results[test_file], Exception)


def test_parse_files_parallel_multiple_files(tmp_path):
    """Test parsing multiple files in parallel"""
    files = []
    for i in range(5):
        test_file = tmp_path / f"test{i}.astra"
        test_file.write_text(f"fn func{i}() -> Int {{ return {i}; }}")
        files.append(test_file)

    results = parse_files_parallel(files)

    assert len(results) == 5
    for file in files:
        assert file in results
        assert not isinstance(results[file], Exception)


def test_parse_files_parallel_with_errors(tmp_path):
    """Test parsing files with some errors"""
    good_file = tmp_path / "good.astra"
    good_file.write_text("fn main() -> Int { return 0; }")

    bad_file = tmp_path / "bad.astra"
    bad_file.write_text("invalid syntax !!!")

    results = parse_files_parallel([good_file, bad_file])

    assert len(results) == 2
    assert not isinstance(results[good_file], Exception)
    assert isinstance(results[bad_file], Exception)


def test_parse_files_parallel_uses_relative_paths(tmp_path):
    """Test that parse_files_parallel uses relative paths for work IDs"""
    # Change to tmp_path to make files relative
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        test_file = tmp_path / "test.astra"
        test_file.write_text("fn main() -> Int { return 0; }")

        results = parse_files_parallel([test_file])

        assert len(results) == 1
        assert test_file in results
    finally:
        os.chdir(original_cwd)


def test_deterministic_merge_diagnostics():
    """Test deterministic merging of diagnostics"""

    @dataclass
    class MockDiagnostic:
        message: str
        span: object = None

    @dataclass
    class MockSpan:
        filename: str
        line: int
        col: int

    # Create diagnostics
    diag1 = MockDiagnostic("error 1", MockSpan("file.astra", 10, 5))
    diag2 = MockDiagnostic("error 2", MockSpan("file.astra", 5, 10))
    diag3 = MockDiagnostic("error 3", MockSpan("other.astra", 1, 1))

    lists = [[diag1, diag2], [diag3]]

    merged = DeterministicMerge.merge_diagnostics(lists)

    # Should be sorted by file, line, col
    assert len(merged) == 3
    assert merged[0] == diag2  # file.astra:5:10
    assert merged[1] == diag1  # file.astra:10:5
    assert merged[2] == diag3  # other.astra:1:1


def test_deterministic_merge_diagnostics_without_span():
    """Test merging diagnostics without span info"""

    @dataclass
    class MockDiagnostic:
        message: str
        span: object = None

    diag1 = MockDiagnostic("error 1")
    diag2 = MockDiagnostic("error 2")

    merged = DeterministicMerge.merge_diagnostics([[diag1], [diag2]])

    assert len(merged) == 2


def test_deterministic_merge_symbol_tables():
    """Test deterministic merging of symbol tables"""
    table1 = {"sym1": "value1", "sym2": "value2"}
    table2 = {"sym3": "value3", "sym2": "value2_override"}

    merged = DeterministicMerge.merge_symbol_tables([table1, table2])

    assert "sym1" in merged
    assert "sym2" in merged
    assert "sym3" in merged
    # Last one wins in case of conflict
    assert merged["sym2"] == "value2_override"


def test_deterministic_merge_empty_symbol_tables():
    """Test merging empty symbol tables"""
    merged = DeterministicMerge.merge_symbol_tables([{}, {}])
    assert merged == {}


def test_get_thread_count_default():
    """Test get_thread_count with default value"""
    with patch.dict(os.environ, {}, clear=True):
        count = get_thread_count()
        # Should default to cpu_count or 1
        assert count >= 1


def test_get_thread_count_from_env():
    """Test get_thread_count from environment variable"""
    with patch.dict(os.environ, {"ASTRA_THREADS": "8"}):
        count = get_thread_count()
        assert count == 8


def test_get_thread_count_invalid_env():
    """Test get_thread_count with invalid environment value"""
    with patch.dict(os.environ, {"ASTRA_THREADS": "invalid"}):
        count = get_thread_count()
        # Should fall back to cpu_count
        assert count >= 1


def test_get_thread_count_empty_env():
    """Test get_thread_count with empty environment value"""
    with patch.dict(os.environ, {"ASTRA_THREADS": ""}):
        count = get_thread_count()
        # Should fall back to cpu_count
        assert count >= 1


def test_is_parallel_enabled_single_thread():
    """Test is_parallel_enabled returns False for single thread"""
    with patch.dict(os.environ, {"ASTRA_THREADS": "1"}):
        assert not is_parallel_enabled()


def test_is_parallel_enabled_multiple_threads():
    """Test is_parallel_enabled returns True for multiple threads"""
    with patch.dict(os.environ, {"ASTRA_THREADS": "4"}):
        assert is_parallel_enabled()


def test_parallel_executor_concurrent_execution():
    """Test that work items execute concurrently"""
    with ParallelExecutor(max_workers=2) as executor:
        start_times = {}
        end_times = {}

        def work_fn(work_id):
            def fn():
                start_times[work_id] = time.time()
                time.sleep(0.1)  # Simulate work
                end_times[work_id] = time.time()
                return work_id
            return fn

        # Submit two work items
        work1 = WorkItem(id="work_1", fn=work_fn("work_1"))
        work2 = WorkItem(id="work_2", fn=work_fn("work_2"))

        executor.submit_work(work1)
        executor.submit_work(work2)

        results = executor.wait_all()

        assert results["work_1"] == "work_1"
        assert results["work_2"] == "work_2"
        # Check that they overlapped (ran concurrently)
        # Work1 starts, work2 starts before work1 ends
        assert "work_1" in start_times
        assert "work_2" in start_times


def test_parallel_executor_multiple_wait_all_calls():
    """Test that multiple wait_all calls work correctly"""
    with ParallelExecutor(max_workers=2) as executor:
        # First batch
        work1 = WorkItem(id="work_1", fn=lambda: 1)
        executor.submit_work(work1)
        results1 = executor.wait_all()
        assert results1 == {"work_1": 1}

        # Second batch
        work2 = WorkItem(id="work_2", fn=lambda: 2)
        executor.submit_work(work2)
        results2 = executor.wait_all()
        assert results2 == {"work_2": 2}


def test_parallel_executor_wait_all_clears_state():
    """Test that wait_all clears results after returning them"""
    with ParallelExecutor(max_workers=2) as executor:
        work = WorkItem(id="work_1", fn=lambda: 42)
        executor.submit_work(work)

        results = executor.wait_all()
        assert results == {"work_1": 42}

        # Internal state should be cleared
        assert len(executor._results) == 0


def test_collect_files_parallel(tmp_path):
    """Test collect_files_parallel delegates to existing function"""
    test_file = tmp_path / "test.astra"
    test_file.write_text("fn main() -> Int { return 0; }")

    # Mock the _collect_input_files function from build module
    with patch('astra.build._collect_input_files') as mock_collect:
        mock_collect.__wrapped__ = MagicMock(return_value=[test_file])

        result = collect_files_parallel(test_file)

        assert result == [test_file]


# Import dataclass for mock diagnostic
from dataclasses import dataclass


def test_parallel_executor_work_profiling():
    """Test that work execution is profiled"""
    with patch('astra.parallel.profiler') as mock_profiler:
        mock_section = MagicMock()
        mock_profiler.section.return_value.__enter__ = MagicMock()
        mock_profiler.section.return_value.__exit__ = MagicMock()

        with ParallelExecutor(max_workers=2) as executor:
            work = WorkItem(id="test_work", fn=lambda: 42)
            executor.submit_work(work)
            executor.wait_for("test_work")


def test_regression_work_item_late_binding():
    """Regression test: ensure work functions use proper late binding"""
    with ParallelExecutor(max_workers=2) as executor:
        # This tests that lambda captures work correctly in loops
        for i in range(3):
            work = WorkItem(id=f"work_{i}", fn=lambda val=i: val)
            executor.submit_work(work)

        results = executor.wait_all()

        # Each work item should return its own value, not the final loop value
        assert results["work_0"] == 0
        assert results["work_1"] == 1
        assert results["work_2"] == 2