# Eval A-2 report — `src/meta_uniformity.py` re-run (execute-only)

**Command run:** `.venv/bin/python src/meta_uniformity.py` from the worktree root. Exit code 0.

## 1. sha256 of `results/meta_uniformity.json`

| | sha256 |
|---|---|
| before run | `021c37ddcfc3d6eb7b2435580b6ef9dcbdad882f144f4e27b8082a1984b41f31` |
| after run | `3d696051230a8837038545df7b435c57e61af6684634629d1debed7906231d45` |

**Identical: NO.** The file changed on re-run.

## 2. Script stdout, verbatim

```
Matplotlib is building the font cache; this may take a moment.
{
 "panel_version": 2,
 "panel_sha": "8c7891b558ab8a28",
 "n_tests": 132,
 "p_meta_discrete": 0.03248375812093953,
 "frac_le_05": 0.10606060606060606,
 "frac_le_01": 0.015151515151515152
}
```

(The first line is a Matplotlib message emitted on stderr/stdout by the library, not by the script's own print; it is included because I captured `2>&1`.)

## Noted, not acted on

- `git status --porcelain` after the run shows two tracked files modified: `results/meta_uniformity.json` and `results/figures/fig9_meta_uniformity.png`. I did not diff, revert, or inspect either file's contents.
- No files were edited by me. No interpretation of the hash mismatch is offered per the execute-only brief.

## Summary lines (per role rule 8)

- Statistics run: one execution of `src/meta_uniformity.py` (meta-uniformity panel, n_tests=132).
- p-values: as printed above (`p_meta_discrete` = 0.03248375812093953); not interpreted.
- Fires + attribution: none assessed (execute-only task).
- Multiplicity arithmetic: not applicable to this task.
- Reproducibility verification: before/after sha256 of `results/meta_uniformity.json` differ (see table). Verification of this run is to be dispatched by the orchestrator to the independent verifier; I have not marked anything as verified.
