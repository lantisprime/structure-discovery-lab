# Structure Discovery Evaluation Set v1

This pack contains synthetic datasets that look noisy at the row level but contain a
controlled mixture of true nulls, planted within-dataset structure, and planted
cross-dataset relationships.

Use the `blind/` folder for your lab run. Do not open `answer_key/` until after the lab
has produced its own results.

## Intended use

This is a benchmark for a structure-discovery lab. A good lab should:

1. correctly reject structure in negative controls;
2. detect planted marginal, dynamical, topological, graph, low-rank, and relational
   structure;
3. avoid treating every optimizer output as evidence;
4. use matched nulls;
5. report which effects are detectable and which are below power.

## Folders

| folder | contents |
|---|---|
| `blind/` | datasets and neutral data cards, no ground truth |
| `answer_key/` | ground truth, expected detections, hidden labels |
| `src/` | deterministic generation notes/code support |

## Recommended workflow

1. Hand only `structure_eval_set_v1_blind.zip` to the lab.
2. Run the lab's normal onboarding, registration, and experiment cycle.
3. Export the lab report.
4. Compare with `answer_key/GROUND_TRUTH.md`.
5. Score as: true positives, true negatives, false positives, false negatives,
   null-model mismatches, and overclaims.
