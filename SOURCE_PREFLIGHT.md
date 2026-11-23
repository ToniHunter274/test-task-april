# Source preflight (private research only; not Radar Studio wording)

Exact public versions and mechanisms:

- Databricks Runtime 18 LTS ML: xgboost 3.1.1. https://docs.databricks.com/aws/en/release-notes/runtime/18ml
- Databricks Runtime 19 ML: lightgbm 4.6.0. https://docs.databricks.com/aws/en/release-notes/runtime/19ml
- LightGBM v4.6.0 NDCG class, query-weight branch and nonweighted perfect score for empty query: https://github.com/lightgbm-org/LightGBM/blob/v4.6.0/src/metric/rank_metric.hpp#L92-L142
- XGBoost v3.1.1 NDCG source, minus branch and weighted aggregation: https://github.com/dmlc/xgboost/blob/v3.1.1/src/metric/rank_metric.cc#L386-L425
- XGBoost v3.1.1 exact documentation about `ndcg@n-`: https://github.com/dmlc/xgboost/blob/v3.1.1/doc/parameter.rst#L475-L480
- OpenAI HumanEval official pass@k estimator: https://github.com/openai/human-eval/blob/master/human_eval/evaluation.py#L13-L29
- Codex paper: https://arxiv.org/abs/2107.03374

Notes:
1. Public web/source reads succeeded on Databricks and GitHub, but this is NOT an actual Radar Studio source-check result. Run Studio's Source URLs check before writing any rubric criterion.
2. This bundle verifies the class-level rule, NOT an NDCG dashboard value of 0.5731 or either candidate X/Y's inferred metric. Their complete input labels, rankings, group weights and dashboard aggregate are necessary for exact scenario reproduction.
3. The user-reported decision bands entail a generation threshold strictly above 0.6000 and at or below 0.6278, assuming a common threshold and k<=12; check the actual user-authored task threshold.
4. No Studio prompt, rubric criteria, evidence excerpts or review notes were generated here.
