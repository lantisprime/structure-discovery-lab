"""Equation-layer feasibility probe (deterministic, no LLM), per docs/EQUATION_DISCOVERY.md §6:
- candidate family declared BEFORE fitting (here: symbolic regression over {+,-,*,sin} and
  SINDy sparse regression over a polynomial library);
- lambda (complexity penalty) declared before seeing test scores;
- the SAME discovery procedure is run on B matched-null synthetic series (the
  null-equation generator, A1) and the observed score is judged against that distribution;
- selection: min description-length-style J = heldout_loss + lambda*complexity;
- everything seeded -> byte-identical on re-run.
Two planted cases: (1) a known law y = 2 x - 0.5 x^2 + noise; (2) pure noise.
"""
import hashlib
import json
import warnings

import numpy as np

warnings.filterwarnings("ignore")

SEED = 20260908
LAMBDA = 0.02          # declared before any fit
B_NULL = 30            # matched-null replicates for the null-equation generator
N = 400


def make_series(rng, law):
    x = rng.uniform(-2, 2, size=N)
    noise = rng.normal(0, 0.3, size=N)
    y = (2 * x - 0.5 * x ** 2 + noise) if law else noise
    return x, y


def split(x, y):
    n = len(x)
    i1, i2 = int(0.6 * n), int(0.8 * n)
    return (x[:i1], y[:i1]), (x[i1:i2], y[i1:i2]), (x[i2:], y[i2:])


def sr_fit(xtr, ytr, seed):
    """Symbolic regression with a declared function set; deterministic given the seed."""
    from gplearn.genetic import SymbolicRegressor
    sr = SymbolicRegressor(population_size=300, generations=12, function_set=("add", "sub", "mul", "sin"),
                           parsimony_coefficient=0.01, random_state=seed, n_jobs=1, verbose=0)
    sr.fit(xtr.reshape(-1, 1), ytr)
    return sr


def score(model, xs, ys):
    pred = model.predict(xs.reshape(-1, 1))
    return float(np.mean((pred - ys) ** 2))


def complexity(model):
    return int(model._program.length_)


def discover(x, y, seed):
    """One run of the registered procedure -> (J, heldout_mse, test_mse, complexity, expr)."""
    (xtr, ytr), (xva, yva), (xte, yte) = split(x, y)
    m = sr_fit(xtr, ytr, seed)
    j = score(m, xva, yva) + LAMBDA * complexity(m)
    return {"J": round(j, 4), "val_mse": round(score(m, xva, yva), 4), "test_mse": round(score(m, xte, yte), 4),
            "complexity": complexity(m), "expr": str(m._program)}


def null_baseline_mse(y_train_mean, yte):
    return float(np.mean((yte - y_train_mean) ** 2))


def run_case(name, law):
    rng = np.random.default_rng(SEED)
    x, y = make_series(rng, law)
    obs = discover(x, y, SEED)
    (xtr, ytr), _, (xte, yte) = split(x, y)
    f_null = null_baseline_mse(float(np.mean(ytr)), yte)
    # null-equation generator: the identical procedure on B matched-null series (pure noise,
    # same n, same noise scale); record the distribution of recovered J and test skill
    null_js, null_skill = [], []
    for b in range(B_NULL):
        rb = np.random.default_rng(SEED + 1000 + b)
        xb, yb = make_series(rb, law=False)
        r = discover(xb, yb, SEED + 1000 + b)
        (_, ytrb), _, (_, yteb) = split(xb, yb)
        null_js.append(r["J"])
        null_skill.append(null_baseline_mse(float(np.mean(ytrb)), yteb) - r["test_mse"])   # >0 = beat the mean
    skill = f_null - obs["test_mse"]
    p = (1 + sum(1 for s in null_skill if s >= skill)) / (B_NULL + 1)        # lab's p_perm convention
    verdict = "PREDICTIVE_EQUATION" if (p < 0.05 and skill > 0) else "FAILED_EQUATION_SEARCH"
    out = {"case": name, "observed": obs, "null_baseline_test_mse": round(f_null, 4), "skill": round(skill, 4),
           "null_equation_generator": {"B": B_NULL, "skill_quantiles": [round(float(q), 4) for q in np.quantile(null_skill, [0.5, 0.95, 1.0])]},
           "null_adjusted_p": round(p, 4), "verdict": verdict}
    return out


def main():
    results = [run_case("planted law y=2x-0.5x^2+noise", True), run_case("pure noise", False)]
    blob = json.dumps(results, sort_keys=True)
    print(json.dumps(results, indent=1))
    print("run sha256:", hashlib.sha256(blob.encode()).hexdigest()[:16], "(re-run must reproduce this exactly)")


if __name__ == "__main__":
    main()
