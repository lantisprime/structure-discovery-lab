# Data card — eq_eval_set_v1 blind units

12 univariate daily time series, `unit_01.csv` … `unit_12.csv`, columns
`date,value`, n=400 each, dates 2025-01-01 onward (calendar is synthetic —
no real-world covariates apply). Values are dimensionless; scales differ by
unit and carry no information. Provenance, mixture proportions, and per-unit
generating processes are sealed (SEAL_NOTICE.md). Treat each unit
independently; nothing links units to each other.
