#!/usr/bin/env python3
"""Environment guard for the Run centre.

The lab's job scripts (launched from /console#agents) import third-party packages
that requirements.txt under-declares (it lists only ephem/numpy/openpyxl, but the
scripts also need scipy/matplotlib/pandas/ripser). The console job e2e mocks the
/api/jobs POSTs, so a missing runtime dependency surfaces only when a job actually
runs a subprocess — which is how meta_panel (matplotlib) and r5_coupling (scipy)
failed in the browser after passing every mocked test.

This fast import check is the coverage the mocked UI test cannot give: it fails
loudly, before anyone clicks Run, if any package a whitelisted job needs is
absent. No job is executed and nothing under results/ is touched.

Run:  python3 webapp/test_lab_deps.py
"""
import importlib
import unittest

# import-name -> a Run-centre job script that needs it (for a clear message).
REQUIRED = {
    "numpy": "src/* (ubiquitous)",
    "scipy": "measure_r5_coupling.py (R5 re-shadow), measure_equivalence.py (families)",
    "matplotlib": "meta_uniformity.py (Rebuild honesty meter — writes fig9)",
    "pandas": "src/* data handling",
    "ripser": "src/* persistent-homology instruments",
    "ephem": "eq_* ephemeris series (equation program)",
    "openpyxl": "PCSO .xlsx ingestion",
}


class TestLabRuntimeDeps(unittest.TestCase):
    def test_required_imports_present(self):
        missing = []
        for mod, who in REQUIRED.items():
            try:
                importlib.import_module(mod)
            except Exception as e:                       # ImportError et al.
                missing.append(f"{mod}  — needed by {who}  ({type(e).__name__})")
        self.assertEqual(missing, [], "\nMissing lab runtime dependencies — Run "
                         "centre jobs will fail with ModuleNotFoundError:\n  "
                         + "\n  ".join(missing) + "\nInstall them into the "
                         "interpreter the server runs on (sys.executable).")


if __name__ == "__main__":
    unittest.main(verbosity=2)
