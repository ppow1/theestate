from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

CANONS = {
    "WP-4111": {
        "directory": "WP-4111_SERIES_Height_Proportion_and_Scale_Reference_System",
        "parts": 7,
        "output": "WP-4111_SERIES_Height_Proportion_and_Scale_Reference_System.md",
    },
    "WP-4112": {
        "directory": "WP-4112_SERIES_Measurement_Variant_Review_Workflow",
        "parts": 8,
        "output": "WP-4112_SERIES_Measurement_Variant_Review_Workflow.md",
    },
}


def assemble(root: Path, identifier: str) -> tuple[Path, str, int]:
    spec = CANONS[identifier]
    canon_dir = root / spec["directory"]
    parts_dir = canon_dir / "parts"
    expected = [parts_dir / f"{identifier}.part-{index:03d}.md" for index in range(spec["parts"])]

    missing = [str(path) for path in expected if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required canon parts:\n" + "\n".join(missing))

    unexpected = sorted(parts_dir.glob(f"{identifier}.part-*.md"))
    if unexpected != expected:
        raise RuntimeError(
            "Part set differs from the verified handoff. Expected:\n"
            + "\n".join(str(path) for path in expected)
            + "\nObserved:\n"
            + "\n".join(str(path) for path in unexpected)
        )

    payload = b"".join(path.read_bytes() for path in expected)
    output = canon_dir / spec["output"]
    output.write_bytes(payload)
    return output, hashlib.sha256(payload).hexdigest(), len(payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Assemble the verified WP-4111 and WP-4112 recovery parts without rewriting or normalization."
    )
    parser.add_argument(
        "identifiers",
        nargs="*",
        choices=sorted(CANONS),
        default=sorted(CANONS),
        help="Canon identifiers to assemble. Defaults to both verified canons.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Recovered work-package root containing the canon directories.",
    )
    args = parser.parse_args()

    for identifier in args.identifiers:
        output, digest, size = assemble(args.root.resolve(), identifier)
        print(f"{identifier}: {output} bytes={size} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
