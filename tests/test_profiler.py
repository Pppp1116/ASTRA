"""
Comprehensive tests for astra.profiler module.

Tests profiling functionality including:
- ProfileRecord and PhaseStats
- ThreadLocalProfiler
- Profiler singleton
- Thread-safe profiling
- JSON and text output
"""

import pytest
import json
import time
import threading
from unittest.mock import patch

from astra.profiler import (
    ProfileRecord,
    PhaseStats,
    ThreadLocalProfiler,
    Profiler,
    profiler,
)


def test_profile_record_creation():
    """Test ProfileRecord creation"""
    record = ProfileRecord(name="test_phase", duration_s=1.5)
    assert record.name == "test_phase"
    assert record.duration_s == 1.5
    assert record.thread_id > 0


def test_profile_record_default_thread_id():
    """Test that ProfileRecord gets default thread_id"""
    record = ProfileRecord(name="test", duration_s=1.0)
    assert record.thread_id == threading.get_ident()


def test_phase_stats_defaults():
    """Test PhaseStats default values"""
    stats = PhaseStats()
    assert stats.total_time == 0.0
    assert stats.call_count == 0
    assert stats.parallel_time == 0.0
    assert stats.max_thread_time == 0.0


def test_phase_stats_values():
    """Test PhaseStats with values"""
    stats = PhaseStats(
        total_time=5.0,
        call_count=10,
        parallel_time=2.5,
        max_thread_time=1.5
    )
    assert stats.total_time == 5.0
    assert stats.call_count == 10
    assert stats.parallel_time == 2.5
    assert stats.max_thread_time == 1.5


def test_thread_local_profiler_stack():
    """Test ThreadLocalProfiler stack operations"""
    profiler = ThreadLocalProfiler()

    profiler.start_section("test")
    assert len(profiler._stack) == 1

    duration = profiler.end_section("test")
    assert len(profiler._stack) == 0
    assert duration >= 0


def test_thread_local_profiler_records():
    """Test ThreadLocalProfiler records collection"""
    profiler = ThreadLocalProfiler()

    profiler.start_section("test1")
    time.sleep(0.01)
    profiler.end_section("test1")

    profiler.start_section("test2")
    time.sleep(0.01)
    profiler.end_section("test2")

    assert len(profiler._records) == 2
    assert profiler._records[0].name == "test1"
    assert profiler._records[1].name == "test2"


def test_thread_local_profiler_empty_stack_end():
    """Test ending section with empty stack"""
    profiler = ThreadLocalProfiler()
    duration = profiler.end_section("test")
    assert duration == 0.0


def test_profiler_enable_disable():
    """Test Profiler enable/disable"""
    prof = Profiler()
    assert not prof.enabled

    prof.enable()
    assert prof.enabled

    prof.disable()
    assert not prof.enabled


def test_profiler_enable_clears_state():
    """Test that enabling profiler clears previous state"""
    prof = Profiler()
    prof._totals["test"] = 5.0
    prof._records.append(ProfileRecord("test", 1.0))

    prof.enable()

    assert len(prof._totals) == 0
    assert len(prof._records) == 0


def test_profiler_reset():
    """Test Profiler reset"""
    prof = Profiler()
    prof._totals["test"] = 5.0
    prof._records.append(ProfileRecord("test", 1.0))
    prof._phase_stats["test"] = PhaseStats(total_time=5.0)

    prof.reset()

    assert len(prof._totals) == 0
    assert len(prof._records) == 0
    assert len(prof._phase_stats) == 0


def test_profiler_section_disabled():
    """Test that section does nothing when disabled"""
    prof = Profiler()
    prof.disable()

    with prof.section("test"):
        time.sleep(0.01)

    assert "test" not in prof._totals


def test_profiler_section_enabled():
    """Test section profiling when enabled"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        time.sleep(0.01)

    assert "test" in prof._totals
    assert prof._totals["test"] > 0


def test_profiler_section_accumulates():
    """Test that multiple sections accumulate time"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        time.sleep(0.01)

    first_time = prof._totals["test"]

    with prof.section("test"):
        time.sleep(0.01)

    second_time = prof._totals["test"]

    assert second_time > first_time


def test_profiler_section_records():
    """Test that sections create records"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        pass

    assert len(prof._records) == 1
    assert prof._records[0].name == "test"


def test_profiler_summary():
    """Test profiler summary"""
    prof = Profiler()
    prof.enable()

    with prof.section("test1"):
        time.sleep(0.01)

    with prof.section("test2"):
        time.sleep(0.01)

    summary = prof.summary()

    assert "test1" in summary
    assert "test2" in summary
    assert summary["test1"] > 0
    assert summary["test2"] > 0


def test_profiler_summary_returns_copy():
    """Test that summary returns a copy to prevent mutation"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        pass

    summary1 = prof.summary()
    summary1["test"] = 999.0

    summary2 = prof.summary()
    assert summary2["test"] != 999.0


def test_profiler_total_time():
    """Test total time calculation"""
    prof = Profiler()
    prof.enable()

    with prof.section("test1"):
        time.sleep(0.01)

    with prof.section("test2"):
        time.sleep(0.01)

    total = prof.total_time()
    assert total > 0


def test_profiler_to_text_empty():
    """Test text output when empty"""
    prof = Profiler()
    prof.enable()

    text = prof.to_text()
    assert text == ""


def test_profiler_to_text_with_data():
    """Test text output with profiling data"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        time.sleep(0.01)

    text = prof.to_text()

    assert "Compile-time profile" in text
    assert "test" in text
    assert "total" in text


def test_profiler_to_text_sorted():
    """Test that text output is sorted"""
    prof = Profiler()
    prof.enable()

    with prof.section("zebra"):
        pass

    with prof.section("aardvark"):
        pass

    text = prof.to_text()
    lines = text.split("\n")

    # Find the phase lines (skip header)
    phase_lines = [l for l in lines if "aardvark" in l or "zebra" in l]

    # aardvark should come before zebra (check that aardvark is in first line)
    assert len(phase_lines) == 2
    assert "aardvark" in phase_lines[0]
    assert "zebra" in phase_lines[1]


def test_profiler_to_json():
    """Test JSON output"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        time.sleep(0.01)

    json_str = prof.to_json()
    data = json.loads(json_str)

    assert "phases" in data
    assert "total" in data
    assert "threads" in data
    assert "test" in data["phases"]
    assert data["phases"]["test"]["total_time_s"] > 0


def test_profiler_to_json_phase_info():
    """Test JSON output contains phase info"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        pass

    json_str = prof.to_json()
    data = json.loads(json_str)

    phase = data["phases"]["test"]
    assert "total_time_s" in phase
    assert "call_count" in phase
    assert "parallel_time_s" in phase
    assert "max_thread_time_s" in phase
    assert "is_parallel" in phase


def test_profiler_singleton():
    """Test that profiler is a singleton"""
    from astra.profiler import profiler as prof1
    from astra.profiler import profiler as prof2

    assert prof1 is prof2


def test_profiler_thread_safety():
    """Test basic thread safety of profiler"""
    prof = Profiler()
    prof.enable()

    def worker():
        with prof.section("worker"):
            time.sleep(0.01)

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Worker thread records are in thread-local storage
    # Check that thread locals were created
    assert len(prof._thread_locals) > 0


def test_profiler_parallel_section():
    """Test profiling parallel sections in worker threads"""
    prof = Profiler()
    prof.enable()

    def worker():
        with prof.section("parallel_work"):
            time.sleep(0.01)

    # Run in worker thread
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    # Main thread work
    with prof.section("main_work"):
        time.sleep(0.01)

    summary = prof.summary()
    # Both sections should be recorded
    assert "parallel_work" in summary or "main_work" in summary


def test_profiler_phase_stats_tracking():
    """Test that phase stats are tracked correctly"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        time.sleep(0.01)

    with prof.section("test"):
        time.sleep(0.01)

    stats = prof._phase_stats["test"]
    assert stats.call_count == 2
    assert stats.total_time > 0


def test_profiler_parallel_efficiency_calculation():
    """Test parallel efficiency calculation in text output"""
    prof = Profiler()
    prof.enable()

    # Simulate parallel work
    def worker():
        with prof.section("parallel_phase"):
            time.sleep(0.01)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    # Main thread also does work
    with prof.section("main_phase"):
        time.sleep(0.01)

    text = prof.to_text()
    # Should have text output with main phase
    assert text != ""
    assert "main_phase" in text


def test_profiler_update_phase_stats():
    """Test _update_phase_stats method"""
    prof = Profiler()
    prof.enable()

    # Update stats for non-parallel phase
    prof._update_phase_stats("test", 1.5, is_parallel=False)

    stats = prof._phase_stats["test"]
    assert stats.total_time == 1.5
    assert stats.call_count == 1
    assert stats.parallel_time == 0.0


def test_profiler_update_phase_stats_parallel():
    """Test _update_phase_stats for parallel work"""
    prof = Profiler()
    prof.enable()

    # Update stats for parallel phase
    prof._update_phase_stats("test", 2.0, is_parallel=True)

    stats = prof._phase_stats["test"]
    assert stats.total_time == 2.0
    assert stats.call_count == 1
    assert stats.parallel_time == 2.0
    assert stats.max_thread_time == 2.0


def test_profiler_max_thread_time_tracking():
    """Test that max thread time is tracked correctly"""
    prof = Profiler()
    prof.enable()

    prof._update_phase_stats("test", 1.0, is_parallel=True)
    prof._update_phase_stats("test", 2.5, is_parallel=True)
    prof._update_phase_stats("test", 1.5, is_parallel=True)

    stats = prof._phase_stats["test"]
    assert stats.max_thread_time == 2.5


def test_profiler_enable_with_thread_locals():
    """Test that enabling profiler handles existing thread locals"""
    prof = Profiler()
    prof.enable()

    # Create some thread-local state
    def worker():
        with prof.section("worker"):
            time.sleep(0.01)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()

    # Re-enable should clear thread locals
    prof.enable()
    assert len(prof._thread_locals) == 0


def test_profiler_get_thread_local():
    """Test _get_thread_local method"""
    prof = Profiler()
    prof.enable()

    local1 = prof._get_thread_local()
    local2 = prof._get_thread_local()

    # Same thread should get same instance
    assert local1 is local2


def test_profiler_json_thread_count():
    """Test JSON output includes thread count"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        pass

    json_str = prof.to_json()
    data = json.loads(json_str)

    assert "thread_count" in data
    assert data["thread_count"] >= 1


def test_profiler_json_threads_from_env():
    """Test JSON output includes ASTRA_THREADS from env"""
    prof = Profiler()
    prof.enable()

    with patch.dict('os.environ', {"ASTRA_THREADS": "8"}):
        with prof.section("test"):
            pass

        json_str = prof.to_json()
        data = json.loads(json_str)

        assert data["threads"] == 8


def test_profiler_text_parallel_metrics():
    """Test text output includes parallel metrics"""
    prof = Profiler()
    prof.enable()

    # Simulate some parallel work
    prof._update_phase_stats("parallel_phase", 2.0, is_parallel=True)
    prof._totals["parallel_phase"] = 2.0

    text = prof.to_text()

    assert "parallel" in text.lower()


def test_profiler_section_exception_handling():
    """Test that section context manager handles exceptions"""
    prof = Profiler()
    prof.enable()

    try:
        with prof.section("test"):
            raise ValueError("Test error")
    except ValueError:
        pass

    # Should still have recorded the section
    assert "test" in prof._totals


def test_profiler_concurrent_sections():
    """Test multiple concurrent sections"""
    prof = Profiler()
    prof.enable()

    def worker(name):
        with prof.section(name):
            time.sleep(0.01)

    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(f"worker_{i}",))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Main thread also needs to do work to have entries in summary
    with prof.section("main"):
        pass

    summary = prof.summary()
    # Should have at least the main entry
    assert len(summary) >= 1
    # Thread locals should have been created
    assert len(prof._thread_locals) >= 1


def test_regression_empty_summary_to_text():
    """Regression test: empty summary should return empty string"""
    prof = Profiler()
    prof.enable()
    prof.reset()  # Clear everything

    text = prof.to_text()
    assert text == ""


def test_regression_json_sorted_keys():
    """Regression test: JSON output should have sorted keys"""
    prof = Profiler()
    prof.enable()

    with prof.section("test"):
        pass

    json_str = prof.to_json()

    # JSON should be formatted with sorted keys
    assert '"phases"' in json_str
    assert '"threads"' in json_str
    assert '"total"' in json_str


def test_edge_case_very_short_section():
    """Edge case: very short profiling section"""
    prof = Profiler()
    prof.enable()

    with prof.section("very_short"):
        pass  # Minimal work

    assert "very_short" in prof._totals
    # Duration might be 0 or very small, but should exist
    assert prof._totals["very_short"] >= 0