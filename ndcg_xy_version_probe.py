"""Check release-specific empty-query semantics on *actual* LightGBM and XGBoost runtimes.

This is a focused implementation-behavior probe, NOT a reproduction of candidates
X and Y's specific dashboard values (those inputs are not present here).

Run with the pinned versions in the GitHub workflow. For development on a
non-pinned local XGBoost install, pass --development.
"""
import argparse
import csv
import math
import pathlib

import numpy as np
import lightgbm as lgb
import xgboost as xgb


parser = argparse.ArgumentParser()
parser.add_argument("--development", action="store_true")
a = parser.parse_args()
print(f"NumPy={np.__version__} LightGBM={lgb.__version__} XGBoost={xgb.__version__}", flush=True)
assert lgb.__version__ == "4.6.0", "This probe requires LightGBM 4.6.0"
if not a.development:
    assert xgb.__version__ == "3.1.1", "Pinned audit requires XGBoost 3.1.1"

# Two groups: one perfect relevance [1,0], one empty [0,0].
# Constant features force no tree split. Explicit init score/base margin
# fixes descending ranking independently of training decisions.
LABELS = np.asarray([1, 0, 0, 0], dtype=np.float64)
GROUPS = [2, 2]
FEATURES = np.zeros((4, 1), dtype=np.float64)
SCORES = np.asarray([2, 1, 2, 1], dtype=np.float64)
WEIGHTS = [None, (1, 1), (1, 3), (1, 10)]
results = []


def lgb_check(w):
    weights = None if w is None else np.repeat(w, GROUPS)
    dataset = lgb.Dataset(FEATURES, label=LABELS, group=GROUPS,
                          weight=weights, init_score=SCORES, free_raw_data=False)
    history = {}
    lgb.train({"objective": "lambdarank", "metric": "ndcg", "ndcg_eval_at": [3],
               "min_data_in_leaf": 1000, "num_leaves": 2, "num_threads": 1,
               "verbosity": -1, "seed": 23}, dataset, num_boost_round=1,
              valid_sets=[dataset], valid_names=["test"],
              callbacks=[lgb.record_evaluation(history)])
    return float(history["test"]["ndcg@3"][-1])


def xgb_check(w, metric):
    # XGBoost ranking sample weights apply per *group*, not per row.
    data = xgb.DMatrix(FEATURES, label=LABELS, weight=w, base_margin=SCORES)
    data.set_group(GROUPS)
    history = {}
    xgb.train({"objective": "rank:ndcg", "eval_metric": metric,
               "tree_method": "hist", "min_child_weight": 100000,
               "max_depth": 1, "nthread": 1, "verbosity": 0},
              data, num_boost_round=1, evals=[(data, "test")],
              evals_result=history, verbose_eval=False)
    return float(history["test"][metric][-1])


for weights in WEIGHTS:
    first = 1 if weights is None else weights[0]
    denominator = 2 if weights is None else sum(weights)
    expected_lgb = (first + 1) / denominator
    expected_xgb_minus = first / denominator
    for library, version, metric, got, wanted in (
        ("LightGBM", lgb.__version__, "ndcg@3", lgb_check(weights), expected_lgb),
        ("XGBoost", xgb.__version__, "ndcg@3", xgb_check(weights, "ndcg@3"), expected_lgb),
        ("XGBoost", xgb.__version__, "ndcg@3-", xgb_check(weights, "ndcg@3-"), expected_xgb_minus),
    ):
        print(f"{library:8} {version:5} {metric:7} weights={str(weights):8} "
              f"observed={got:.12f} expected={wanted:.12f}")
        assert math.isclose(got, wanted, abs_tol=1e-8), (library, metric, weights, got, wanted)
        results.append({"library": library, "version": version, "metric": metric,
                        "group_weights": str(weights), "observed": f"{got:.12f}",
                        "expected": f"{wanted:.12f}", "match": "PASS"})

with pathlib.Path("ndcg-xy-release-probe.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0]))
    writer.writeheader()
    writer.writerows(results)
print("ALL 12 RELEASE-BEHAVIOR ASSERTIONS PASSED")
