#!/usr/bin/env python3
"""Compare deterministic Edriç f32 receipts with the original Futhark entries.

This deliberately executes each fixture once.  It records semantics, not time.
"""

from __future__ import annotations

import argparse
import re
import struct
import subprocess
from pathlib import Path


F32_TOKEN = re.compile(
    r"[-+]?(?:nan|inf|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)

A = "[1.0f32, -2.0f32, 16777216.0f32, 0.1f32, -0.0f32, 3.5f32]"
B = "[5.0f32, 4.0f32, 1.0f32, -0.2f32, 2.0f32, -7.25f32]"
C = "[0.5f32, -3.0f32, 2.0f32, 0.3f32, -4.0f32, 8.0f32]"


def run(command: list[str], *, input_text: str | None = None) -> str:
    completed = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def f32_bits(text: str) -> list[int]:
    values = []
    for token in F32_TOKEN.findall(text.replace("f32", "")):
        packed = struct.pack("<f", float(token))
        values.append(struct.unpack("<I", packed)[0])
    return values


def edric_receipts(executable: Path) -> tuple[dict[str, str], set[str]]:
    values: dict[str, str] = {}
    boundaries: set[str] = set()
    for line in run([str(executable)]).splitlines():
        if " " not in line:
            raise RuntimeError(f"malformed Edriç receipt: {line!r}")
        label, payload = line.split(" ", 1)
        if label in {
            "equal_shape",
            "unequal_shape",
            "wrong_value_count",
        }:
            boundaries.add(line)
        else:
            values[label] = payload
    return values, boundaries


def futhark_receipts(babelstream: Path, intra: Path) -> dict[str, str]:
    cases = {
        "f32_copy": (babelstream, "f32_copy", [A]),
        "f32_mul": (babelstream, "f32_mul", [C]),
        "f32_add": (babelstream, "f32_add", [A, B]),
        "f32_triad": (babelstream, "f32_triad", [B, C]),
        "f32_nstream": (babelstream, "f32_nstream", [A, B, C]),
        "f32_dot": (babelstream, "f32_dot", [A, B]),
        "scan_reduce": (intra, "scan_reduce", [f"[{A}, {B}]"]),
    }
    receipts: dict[str, str] = {}
    for label, (executable, entry, inputs) in cases.items():
        receipts[label] = run(
            [str(executable), "-e", entry],
            input_text="\n".join(inputs) + "\n",
        )
    return receipts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edric", required=True, type=Path)
    parser.add_argument("--futhark-babelstream", required=True, type=Path)
    parser.add_argument("--futhark-intra", required=True, type=Path)
    args = parser.parse_args()

    edric, boundaries = edric_receipts(args.edric.resolve())
    futhark = futhark_receipts(
        args.futhark_babelstream.resolve(), args.futhark_intra.resolve()
    )

    if set(edric) != set(futhark):
        raise SystemExit(
            "receipt labels differ: "
            f"Edriç={sorted(edric)}, Futhark={sorted(futhark)}"
        )

    for label in sorted(futhark):
        edric_bits = f32_bits(edric[label])
        futhark_bits = f32_bits(futhark[label])
        if edric_bits != futhark_bits:
            raise SystemExit(
                f"{label}: f32 bits differ\n"
                f"  Edriç:   {edric[label]} -> {edric_bits}\n"
                f"  Futhark: {futhark[label]} -> {futhark_bits}"
            )
        print(f"{label}: MATCH ({len(edric_bits)} f32 value(s))")

    required_boundaries = {
        "equal_shape accepted",
        "unequal_shape refused",
        "wrong_value_count refused",
    }
    if boundaries != required_boundaries:
        raise SystemExit(
            "checked boundary receipts differ: "
            f"expected={sorted(required_boundaries)}, actual={sorted(boundaries)}"
        )

    print("shape/storage boundary: MATCH")
    print("semantic comparison: PASS (no timing performed)")


if __name__ == "__main__":
    main()
