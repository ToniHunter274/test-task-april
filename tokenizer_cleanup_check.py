"""Compatibility matrix for Hugging Face tokenizer cleanup.

Run separately under each pinned Transformers version. Uses tokenizer files,
never downloads model weights; does not execute remote tokenizer code.
Always emits results.jsonl, including model-specific errors.
"""
import importlib.metadata
import json
import os
import platform
import sys
import traceback
from pathlib import Path

OUTPUT = Path(os.environ.get("RESULT_FILE", "results.jsonl"))
VERSION_LABEL = os.environ.get("MATRIX_VERSION", "unlabeled")
MODELS = [
    "bert-base-uncased",
    "bert-base-cased",
    "distilbert-base-uncased",
    "gpt2",
    "roberta-base",
    "facebook/bart-base",
    "google/flan-t5-small",
    "Qwen/Qwen2.5-0.5B-Instruct",
]
TEXTS = ["x != y ?", "Wait , isn't it ?", "a . b"]


def emit(record):
    with OUTPUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(record, ensure_ascii=False, sort_keys=True), flush=True)


OUTPUT.write_text("", encoding="utf-8")
base = {"matrix_version": VERSION_LABEL, "python": platform.python_version()}
try:
    import transformers
    from transformers import AutoTokenizer
    from huggingface_hub import HfApi, hf_hub_download
except Exception as exc:
    emit({**base, "status": "import_error", "error": type(exc).__name__,
          "detail": str(exc)[:800]})
    sys.exit(0)  # installation failure is captured as data, not mistaken for a model result

base["transformers"] = transformers.__version__
try:
    from importlib.metadata import version as dist_version
    base["tokenizers"] = dist_version("tokenizers")
    base["huggingface_hub"] = dist_version("huggingface-hub")
except Exception:
    pass

api = HfApi()
for model in MODELS:
    row = {**base, "model": model}
    try:
        info = api.model_info(model)
        revision = info.sha
        row["revision"] = revision
        # A missing tokenizer_config.json is important evidence, not a failure.
        try:
            fp = hf_hub_download(model, "tokenizer_config.json", revision=revision)
            config = json.loads(Path(fp).read_text(encoding="utf-8"))
            row["config_field_present"] = "clean_up_tokenization_spaces" in config
            row["config_field_value"] = config.get("clean_up_tokenization_spaces")
            row["config_tokenizer_class"] = config.get("tokenizer_class")
        except Exception as config_exc:
            row["config_field_present"] = None
            row["config_fetch_error"] = type(config_exc).__name__ + ": " + str(config_exc)[:250]

        tokenizer = AutoTokenizer.from_pretrained(model, revision=revision,
                                                   use_fast=True, trust_remote_code=False)
        row["tokenizer_class"] = type(tokenizer).__name__
        row["is_fast"] = bool(tokenizer.is_fast)
        row["effective_cleanup"] = getattr(tokenizer, "clean_up_tokenization_spaces", None)
        row["cases"] = []
        for raw in TEXTS:
            try:
                ids = tokenizer.encode(raw, add_special_tokens=False)
                decoded = tokenizer.decode(ids, skip_special_tokens=True)
                explicit_false = tokenizer.decode(ids, skip_special_tokens=True,
                                                   clean_up_tokenization_spaces=False)
                explicit_true = tokenizer.decode(ids, skip_special_tokens=True,
                                                  clean_up_tokenization_spaces=True)
                row["cases"].append({
                    "raw": raw,
                    "token_ids": ids,
                    "default": decoded,
                    "cleanup_false": explicit_false,
                    "cleanup_true": explicit_true,
                    "default_equals_raw": decoded == raw,
                    "effect_from_cleanup": explicit_false != explicit_true,
                    "default_equals_false": decoded == explicit_false,
                    "default_equals_true": decoded == explicit_true,
                })
            except Exception as case_exc:
                row["cases"].append({"raw": raw, "status": "case_error",
                                     "error": type(case_exc).__name__, "detail": str(case_exc)[:500]})
        row["status"] = "ok"
    except Exception as exc:
        row["status"] = "model_error"
        row["error"] = type(exc).__name__
        row["detail"] = str(exc)[:900]
    emit(row)
