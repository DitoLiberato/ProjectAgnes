"""
AGNES Clinical Black Box
========================
Implements the append-only audit log described in manifesto §6.

Design principles
-----------------
* **Append-only** – records are never mutated or deleted after creation.
* **Complete decision chain** – every promoted ClinicalEvent, vetoed alarm
  (VetoRecord), and Hypothesis is persisted so the full reasoning can be
  reconstructed.
* **Dual format** – records can be written in JSON Lines (JSONL) or CSV so
  that the log can be processed by both humans and downstream analytics.
* **Shift summary** – the black box can generate a human-readable shift
  summary for handover documentation.

The Clinical Black Box is the foundation for automated documentation
(manifesto §6): shift summaries, nursing notes, and adverse event
investigations are all derived from this permanent record.
"""

from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import IO, Iterator, Optional, Union

from agnes.evidence import ClinicalEvent, Evidence
from agnes.veto_engine import VetoRecord


# ---------------------------------------------------------------------------
# Log entry types
# ---------------------------------------------------------------------------

class EntryType(str, Enum):
    EVENT = "event"
    VETO = "veto"
    HYPOTHESIS = "hypothesis"
    SYSTEM = "system"


@dataclass
class BlackBoxEntry:
    """
    A single immutable record in the Clinical Black Box.

    Attributes
    ----------
    entry_id    : Unique identifier (UUID or sequence).
    entry_type  : Category of the log entry.
    timestamp   : Unix epoch when the entry was created.
    payload     : Arbitrary JSON-serialisable dict with the full decision data.
    """

    entry_id: str
    entry_type: EntryType
    timestamp: float
    payload: dict

    def to_jsonl(self) -> str:
        """Serialise to a single JSON Line (no trailing newline)."""
        return json.dumps(
            {
                "entry_id": self.entry_id,
                "entry_type": self.entry_type.value,
                "timestamp": self.timestamp,
                "payload": self.payload,
            },
            ensure_ascii=False,
            default=str,
        )

    def to_csv_row(self) -> dict:
        """Flatten to a dict suitable for csv.DictWriter."""
        return {
            "entry_id": self.entry_id,
            "entry_type": self.entry_type.value,
            "timestamp": self.timestamp,
            "payload_json": json.dumps(self.payload, ensure_ascii=False, default=str),
        }


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _evidence_to_dict(e: Evidence) -> dict:
    return {
        "source": e.source.value,
        "signal_type": e.signal_type.name,
        "value": e.value,
        "quality": e.quality,
        "confidence": e.confidence,
        "timestamp": e.timestamp,
        "duration_s": e.duration_s,
        "sensor_id": e.sensor_id,
        "metadata": e.metadata,
    }


def _event_to_payload(event: ClinicalEvent) -> dict:
    return {
        "event_id": event.event_id,
        "description": event.description,
        "severity": event.severity.value,
        "audible": event.audible,
        "hypothesis": event.hypothesis,
        "timestamp": event.timestamp,
        "contributing_evidence": [
            _evidence_to_dict(e) for e in event.contributing_evidence
        ],
    }


def _veto_to_payload(record: VetoRecord) -> dict:
    return {
        "veto_id": record.veto_id,
        "reason": record.reason,
        "candidate_desc": record.candidate_desc,
        "timestamp": record.timestamp,
        "conflicting_evidence": [
            _evidence_to_dict(e) for e in record.conflicting
        ],
    }


# ---------------------------------------------------------------------------
# ClinicalBlackBox
# ---------------------------------------------------------------------------

class ClinicalBlackBox:
    """
    Append-only clinical audit log (manifesto §6).

    Entries can be streamed to a file (JSONL or CSV) and queried in memory
    for shift summaries.

    Parameters
    ----------
    output_path : Optional path to the log file.  If None, records are kept
                  only in memory.
    fmt         : ``"jsonl"`` or ``"csv"`` (default ``"jsonl"``).
    """

    CSV_FIELDNAMES = ["entry_id", "entry_type", "timestamp", "payload_json"]

    def __init__(
        self,
        output_path: Optional[Union[str, Path]] = None,
        fmt: str = "jsonl",
    ) -> None:
        if fmt not in ("jsonl", "csv"):
            raise ValueError(f"Unsupported format: {fmt!r}. Use 'jsonl' or 'csv'.")
        self._fmt = fmt
        self._entries: list[BlackBoxEntry] = []
        self._entry_counter = 0

        self._file: Optional[IO] = None
        self._csv_writer: Optional[csv.DictWriter] = None
        if output_path is not None:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file = open(path, "a", encoding="utf-8", newline="")
            if fmt == "csv":
                self._csv_writer = csv.DictWriter(
                    self._file, fieldnames=self.CSV_FIELDNAMES
                )
                # Write header only if file is empty
                if path.stat().st_size == 0:
                    self._csv_writer.writeheader()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_event(self, event: ClinicalEvent) -> BlackBoxEntry:
        """Append a promoted ClinicalEvent to the log."""
        entry = self._make_entry(EntryType.EVENT, _event_to_payload(event))
        self._append(entry)
        return entry

    def record_veto(self, record: VetoRecord) -> BlackBoxEntry:
        """Append a vetoed alarm to the log."""
        entry = self._make_entry(EntryType.VETO, _veto_to_payload(record))
        self._append(entry)
        return entry

    def record_hypothesis(
        self,
        hypothesis_name: str,
        description: str,
        confidence: float,
        evidence: list[Evidence],
    ) -> BlackBoxEntry:
        """Append a Hypothesis inference to the log."""
        payload = {
            "hypothesis": hypothesis_name,
            "description": description,
            "confidence": confidence,
            "evidence_count": len(evidence),
            "evidence_sources": [e.source.value for e in evidence],
        }
        entry = self._make_entry(EntryType.HYPOTHESIS, payload)
        self._append(entry)
        return entry

    def record_system(self, message: str, data: Optional[dict] = None) -> BlackBoxEntry:
        """Append a system-level message (boot, shutdown, sensor error, etc.)."""
        payload = {"message": message, **(data or {})}
        entry = self._make_entry(EntryType.SYSTEM, payload)
        self._append(entry)
        return entry

    def shift_summary(
        self,
        start: Optional[float] = None,
        end: Optional[float] = None,
    ) -> dict:
        """
        Generate a shift summary for handover documentation (manifesto §6).

        Parameters
        ----------
        start : Unix epoch start of the reporting window (None = beginning).
        end   : Unix epoch end of the reporting window (None = now).

        Returns
        -------
        dict with counts and narrative excerpts.
        """
        end = end or time.time()
        window = [
            e for e in self._entries
            if (start is None or e.timestamp >= start)
            and e.timestamp <= end
        ]
        events = [e for e in window if e.entry_type == EntryType.EVENT]
        vetos = [e for e in window if e.entry_type == EntryType.VETO]
        hypotheses = [e for e in window if e.entry_type == EntryType.HYPOTHESIS]

        audible_count = sum(
            1 for e in events if e.payload.get("audible", False)
        )
        critical_count = sum(
            1 for e in events if e.payload.get("severity") == "critical"
        )

        return {
            "window_start": start,
            "window_end": end,
            "total_entries": len(window),
            "promoted_events": len(events),
            "vetoed_alarms": len(vetos),
            "hypotheses_generated": len(hypotheses),
            "audible_alarms": audible_count,
            "critical_events": critical_count,
            "veto_reasons": [
                e.payload.get("reason", "") for e in vetos
            ],
            "hypothesis_names": [
                e.payload.get("hypothesis", "") for e in hypotheses
            ],
        }

    def iter_entries(
        self,
        entry_type: Optional[EntryType] = None,
    ) -> Iterator[BlackBoxEntry]:
        """Iterate over stored entries, optionally filtered by type."""
        for entry in self._entries:
            if entry_type is None or entry.entry_type == entry_type:
                yield entry

    def export_jsonl(self) -> str:
        """Return all entries as a JSONL string."""
        return "\n".join(e.to_jsonl() for e in self._entries)

    def export_csv(self) -> str:
        """Return all entries as a CSV string."""
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self.CSV_FIELDNAMES)
        writer.writeheader()
        for entry in self._entries:
            writer.writerow(entry.to_csv_row())
        return buf.getvalue()

    def close(self) -> None:
        """Flush and close the underlying file if one is open."""
        if self._file is not None:
            self._file.flush()
            self._file.close()
            self._file = None

    def __enter__(self) -> "ClinicalBlackBox":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_entry(self, entry_type: EntryType, payload: dict) -> BlackBoxEntry:
        self._entry_counter += 1
        return BlackBoxEntry(
            entry_id=str(self._entry_counter),
            entry_type=entry_type,
            timestamp=time.time(),
            payload=payload,
        )

    def _append(self, entry: BlackBoxEntry) -> None:
        """Store in memory and optionally flush to file."""
        self._entries.append(entry)
        if self._file is not None:
            if self._fmt == "jsonl":
                self._file.write(entry.to_jsonl() + "\n")
            else:
                assert self._csv_writer is not None
                self._csv_writer.writerow(entry.to_csv_row())
            self._file.flush()
