"""
Tests for the Clinical Black Box.

Verifies append-only behaviour, JSONL/CSV export, and shift summary
generation (manifesto §6).
"""
import json
import tempfile
import time
from pathlib import Path

import pytest

from agnes.black_box import ClinicalBlackBox, EntryType
from agnes.evidence import (
    ClinicalEvent,
    EventSeverity,
    Evidence,
    NodeID,
    SignalType,
)
from agnes.veto_engine import VetoRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(audible=False) -> ClinicalEvent:
    return ClinicalEvent(
        event_id="evt-001",
        description="Test tachycardia",
        severity=EventSeverity.WARNING,
        contributing_evidence=[],
        audible=audible,
    )


def _make_veto() -> VetoRecord:
    return VetoRecord(
        veto_id="veto-001",
        reason="Mechanical Agitation Artifact",
        conflicting=[],
        candidate_desc="Desaturation",
    )


def _make_evidence() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=98.0,
    )


# ---------------------------------------------------------------------------
# In-memory black box tests
# ---------------------------------------------------------------------------

class TestClinicalBlackBoxInMemory:
    def test_record_event_stores_entry(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        entries = list(bb.iter_entries())
        assert len(entries) == 1
        assert entries[0].entry_type == EntryType.EVENT

    def test_record_veto_stores_entry(self):
        bb = ClinicalBlackBox()
        bb.record_veto(_make_veto())
        entries = list(bb.iter_entries(EntryType.VETO))
        assert len(entries) == 1
        assert "Mechanical Agitation" in entries[0].payload["reason"]

    def test_record_hypothesis_stores_entry(self):
        bb = ClinicalBlackBox()
        bb.record_hypothesis(
            "Test Hypothesis", "Description", 0.85, [_make_evidence()]
        )
        entries = list(bb.iter_entries(EntryType.HYPOTHESIS))
        assert len(entries) == 1
        assert entries[0].payload["hypothesis"] == "Test Hypothesis"

    def test_record_system_stores_entry(self):
        bb = ClinicalBlackBox()
        bb.record_system("System boot")
        entries = list(bb.iter_entries(EntryType.SYSTEM))
        assert len(entries) == 1
        assert entries[0].payload["message"] == "System boot"

    def test_entries_are_append_only(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        first = list(bb.iter_entries())
        bb.record_veto(_make_veto())
        second = list(bb.iter_entries())
        # Original entry is unchanged
        assert first[0].entry_id == second[0].entry_id

    def test_entry_ids_are_sequential(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        bb.record_veto(_make_veto())
        ids = [e.entry_id for e in bb.iter_entries()]
        assert ids == ["1", "2"]

    def test_filter_by_entry_type(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        bb.record_veto(_make_veto())
        events = list(bb.iter_entries(EntryType.EVENT))
        vetos = list(bb.iter_entries(EntryType.VETO))
        assert len(events) == 1
        assert len(vetos) == 1


class TestShiftSummary:
    def test_shift_summary_counts_events_and_vetos(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        bb.record_veto(_make_veto())
        summary = bb.shift_summary()
        assert summary["promoted_events"] == 1
        assert summary["vetoed_alarms"] == 1

    def test_shift_summary_counts_audible_alarms(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event(audible=False))
        bb.record_event(_make_event(audible=True))
        summary = bb.shift_summary()
        assert summary["audible_alarms"] == 1
        assert summary["promoted_events"] == 2

    def test_shift_summary_time_window(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())  # recorded now
        future_start = time.time() + 3600  # 1 hour from now
        summary = bb.shift_summary(start=future_start)
        assert summary["promoted_events"] == 0
        assert summary["vetoed_alarms"] == 0

    def test_shift_summary_includes_veto_reasons(self):
        bb = ClinicalBlackBox()
        bb.record_veto(_make_veto())
        summary = bb.shift_summary()
        assert "Mechanical Agitation Artifact" in summary["veto_reasons"]

    def test_shift_summary_includes_hypothesis_names(self):
        bb = ClinicalBlackBox()
        bb.record_hypothesis("Apnea of Prematurity", "desc", 0.95, [])
        summary = bb.shift_summary()
        assert "Apnea of Prematurity" in summary["hypothesis_names"]


class TestExportFormats:
    def test_export_jsonl_is_valid_json_lines(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        bb.record_veto(_make_veto())
        jsonl = bb.export_jsonl()
        lines = [l for l in jsonl.splitlines() if l.strip()]
        assert len(lines) == 2
        for line in lines:
            obj = json.loads(line)  # must not raise
            assert "entry_id" in obj
            assert "entry_type" in obj
            assert "timestamp" in obj
            assert "payload" in obj

    def test_export_csv_has_header_and_rows(self):
        bb = ClinicalBlackBox()
        bb.record_event(_make_event())
        csv_str = bb.export_csv()
        lines = csv_str.splitlines()
        assert lines[0] == "entry_id,entry_type,timestamp,payload_json"
        assert len(lines) == 2  # header + 1 data row

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            ClinicalBlackBox(fmt="xml")


class TestFileOutput:
    def test_records_written_to_jsonl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_log.jsonl"
            with ClinicalBlackBox(output_path=path, fmt="jsonl") as bb:
                bb.record_event(_make_event())
                bb.record_veto(_make_veto())
            lines = [l for l in path.read_text().splitlines() if l.strip()]
            assert len(lines) == 2
            for line in lines:
                json.loads(line)  # must be valid JSON

    def test_records_written_to_csv_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_log.csv"
            with ClinicalBlackBox(output_path=path, fmt="csv") as bb:
                bb.record_event(_make_event())
            content = path.read_text()
            assert "entry_id" in content
            assert "event" in content
