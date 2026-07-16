"""Bounded, read-only adapters for the PTM discovery pilot.

The source documents remain authoritative.  This module only produces immutable,
deterministic references to them; it is deliberately not a registry or queue.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Iterable


ADAPTER_VERSION = "ptm-prod-g1"


class AdapterState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflict"


class Freshness(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceReference:
    path: str
    sha256: str | None
    byte_length: int | None


@dataclass(frozen=True)
class AdapterRecord:
    adapter_name: str
    adapter_version: str
    source: SourceReference
    source_family: str
    discovered_at: str
    state: AdapterState
    freshness: Freshness
    extracted_id: str | None
    extracted_title: str | None
    extracted_status: str | None
    authority_refs: tuple[str, ...]
    dependency_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    related_source_paths: tuple[str, ...]
    parse_confidence: str
    adapter_warnings: tuple[str, ...]
    field_provenance: tuple[tuple[str, str], ...]

    def normalized(self) -> dict[str, object]:
        """Return a JSON-ready representation with stable key and value ordering."""
        value = asdict(self)
        value["state"] = self.state.value
        value["freshness"] = self.freshness.value
        return value


class PtmReadOnlyAdapterRuntime:
    """Open only allowlisted repository files, with finite resource limits."""

    _ALLOWED = {
        "parking_lot_source_adapter": ("collaboration/parking_lot/",),
        "work_package_source_adapter": ("collaboration/work_packages/",),
        "dispatch_source_adapter": ("collaboration/",),
        "validation_source_adapter": ("collaboration/",),
        "acceptance_source_adapter": ("collaboration/",),
    }
    _FAMILIES = {
        "parking_lot_source_adapter": "parking_lot",
        "work_package_source_adapter": "work_package",
        "dispatch_source_adapter": "dispatch_evidence",
        "validation_source_adapter": "validation_evidence",
        "acceptance_source_adapter": "acceptance_evidence",
    }

    def __init__(
        self,
        repository_root: str | Path,
        *,
        max_file_bytes: int = 1_000_000,
        max_records: int = 100,
        stale_after_seconds: int = 30 * 24 * 60 * 60,
        observed_at: datetime | None = None,
    ) -> None:
        self.root = Path(repository_root).resolve(strict=True)
        self.max_file_bytes = max_file_bytes
        self.max_records = max_records
        self.stale_after_seconds = stale_after_seconds
        self.observed_at = observed_at

    def adapt(self, adapter_name: str, source_paths: Iterable[str]) -> tuple[AdapterRecord, ...]:
        if adapter_name not in self._ALLOWED:
            raise ValueError(f"unknown adapter: {adapter_name}")
        paths = sorted(set(source_paths))
        if len(paths) > self.max_records:
            raise ValueError("bounded read limit exceeded")
        records = [self._adapt_one(adapter_name, path) for path in paths]
        return tuple(sorted(records, key=lambda record: record.source.path))

    def _adapt_one(self, adapter_name: str, raw_path: str) -> AdapterRecord:
        relative = self._validate_path(adapter_name, raw_path)
        source = SourceReference(relative, None, None)
        try:
            content, metadata = self._read_only(relative)
        except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError) as exc:
            return self._unavailable(adapter_name, source, f"{type(exc).__name__}: {exc}")

        source = SourceReference(relative, hashlib.sha256(content).hexdigest(), len(content))
        text = self._redact_private_fields(content.decode("utf-8"))
        title_match = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
        id_match = re.search(r"\b(?:WP|PL|PROD-PTM|[A-Z]+-PTM)-[A-Z0-9-]+\b", text)
        status_match = re.search(r"^Status:\s*(.+?)\s*$", text, re.MULTILINE | re.IGNORECASE)
        bucket = self._status_bucket(relative)
        explicit_status = status_match.group(1).strip() if status_match else None
        warnings: list[str] = []
        state = AdapterState.AVAILABLE
        if not title_match:
            warnings.append("missing title heading")
        if explicit_status and bucket and explicit_status.casefold() != bucket.casefold():
            state = AdapterState.CONFLICT
            warnings.append(f"body status '{explicit_status}' conflicts with path bucket '{bucket}'")
        status_value = explicit_status or bucket
        refs = self._path_refs(text)
        dependencies = self._label_refs(text, "depend")
        authorities = self._label_refs(text, "owner|review|authorit")
        evidence = tuple(sorted(ref for ref in refs if any(word in ref.casefold() for word in ("receipt", "report", "evidence", "validation", "acceptance", "dispatch"))))
        observed = self.observed_at or datetime.fromtimestamp(metadata.st_mtime, timezone.utc)
        age = observed.timestamp() - metadata.st_mtime
        freshness = Freshness.STALE if age > self.stale_after_seconds else Freshness.CURRENT
        if freshness is Freshness.STALE:
            warnings.append("source is stale at the observation time")
        confidence = "high" if title_match and id_match and not warnings else "medium"
        if not title_match and not id_match:
            confidence = "low"
            warnings.append("record has no detectable identifier")
        provenance = tuple((field, relative) for field in (
            "extracted_id", "extracted_title", "extracted_status", "authority_refs",
            "dependency_refs", "evidence_refs", "related_source_paths",
        ))
        discovered_at = datetime.fromtimestamp(metadata.st_mtime, timezone.utc).isoformat()
        return AdapterRecord(
            adapter_name, ADAPTER_VERSION, source, self._FAMILIES[adapter_name], discovered_at,
            state, freshness, id_match.group(0) if id_match else None,
            title_match.group(1).strip() if title_match else None, status_value,
            authorities, dependencies, evidence, refs, confidence,
            tuple(sorted(set(warnings))), provenance,
        )

    def _validate_path(self, adapter_name: str, raw_path: str) -> str:
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts or "\\" in raw_path:
            raise ValueError("source path escapes repository root")
        relative = path.as_posix()
        if not any(relative.startswith(prefix) for prefix in self._ALLOWED[adapter_name]):
            raise ValueError("source path is not allowlisted for adapter")
        resolved = (self.root / relative).resolve(strict=False)
        if not resolved.is_relative_to(self.root):
            raise ValueError("source path escapes repository root through a symlink")
        name = path.name.casefold()
        if adapter_name in {"dispatch_source_adapter", "validation_source_adapter", "acceptance_source_adapter"}:
            term = adapter_name.split("_", 1)[0]
            if term not in name:
                raise ValueError(f"source filename is not {term}-named")
        return relative

    def _read_only(self, relative: str) -> tuple[bytes, os.stat_result]:
        path = self.root / relative
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("source is not a regular file")
            if metadata.st_size > self.max_file_bytes:
                raise ValueError("source exceeds bounded file size")
            content = os.read(descriptor, self.max_file_bytes + 1)
            if len(content) > self.max_file_bytes:
                raise ValueError("source exceeds bounded file size")
            content.decode("utf-8")
            return content, metadata
        finally:
            os.close(descriptor)

    def _unavailable(self, adapter_name: str, source: SourceReference, reason: str) -> AdapterRecord:
        warning = f"source unavailable: {reason}"
        return AdapterRecord(adapter_name, ADAPTER_VERSION, source, self._FAMILIES[adapter_name],
            "unknown", AdapterState.UNAVAILABLE, Freshness.UNKNOWN, None, None, None,
            (), (), (), (), "low", (warning,), ())

    @staticmethod
    def _status_bucket(path: str) -> str | None:
        parts = PurePosixPath(path).parts
        return parts[2] if len(parts) > 3 and parts[:2] == ("collaboration", "work_packages") else None

    @staticmethod
    def _path_refs(text: str) -> tuple[str, ...]:
        refs = re.findall(r"`((?:collaboration|docs)/[^`\n]+)`", text)
        return tuple(sorted(set(refs)))

    @staticmethod
    def _label_refs(text: str, label: str) -> tuple[str, ...]:
        values = re.findall(rf"^(?:{label})[^:]*:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
        return tuple(sorted(set(value.strip() for value in values)))

    @staticmethod
    def _redact_private_fields(text: str) -> str:
        """Exclude explicitly private source fields from all extracted values.

        The source bytes (and therefore their integrity hash) remain untouched.
        This is deliberately a narrow field-level rule rather than an attempt to
        classify or rewrite the authoritative document.
        """
        private_label = re.compile(
            r"^\s*(?:private(?:[-_ ]field)?|secret|password|token|api[-_ ]?key)\s*:",
            re.IGNORECASE,
        )
        return "\n".join(line for line in text.splitlines() if not private_label.match(line))
