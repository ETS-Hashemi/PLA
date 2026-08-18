"""Execute every python block in docs/SEMANTICS.md.

The semantics document promises that each formula sits next to a runnable
block; this test enforces that promise, so the doc cannot drift from the
engine.
"""

import pathlib
import re

import pytest

DOC = pathlib.Path(__file__).resolve().parents[1] / "docs" / "SEMANTICS.md"
BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)

BLOCKS = BLOCK_RE.findall(DOC.read_text(encoding="utf-8"))

# One executable block per formula group: F1/F2, F3, F4, F5a-d, fixpoint,
# non-distribution caveat.
MINIMUM_EXPECTED_BLOCKS = 6


def test_semantics_doc_has_a_block_per_formula_group():
    assert len(BLOCKS) >= MINIMUM_EXPECTED_BLOCKS


@pytest.mark.parametrize("index", range(len(BLOCKS)))
def test_semantics_doc_block_executes(index):
    exec(compile(BLOCKS[index], f"SEMANTICS.md block {index + 1}", "exec"), {})
