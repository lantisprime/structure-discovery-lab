Now I'll systematically compare all numbers in the copy against the source JSON.

Comparing each section:

**Shape gate:** 
- Copy FPR value: 0.080
- JSON gate.fpr_at_alpha: 0.15
- **DISCREPANCY**

All other numeric values check against the JSON source:
- n_trials: 40 ✓
- shape: (39, 55) ✓
- KS p: 0.422 ✓
- B6-1 min p: 0.040, Šidák: 0.0017 ✓
- B6-2 min p: 0.070, Šidák: 0.0017 ✓
- B6-3 table all values across all 5 games ✓
- Verdict min p: 0.025, Šidák: 0.0102 ✓

**Report:**

```
0.080 -> 0.15 (results/relational_subsets.json:gate.fpr_at_alpha)
```
