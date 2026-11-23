"""Public tokenizer fleet experiment. Tokenizer assets only; no model weights or remote code.

`freeze` fetches SHA-1 model revisions once for the entire matrix.
`run` emits one CSV row per model × test string, including explicit errors.
"""
import argparse
import csv
import datetime as dt
import importlib.metadata
import json
import os
import platform
from pathlib import Path

MODELS = [
    "bert-base-uncased",
    "bert-base-cased",
    "distilbert-base-uncased",
    "gpt2",
    "roberta-base",
    "facebook/bart-base",
    "google/flan-t5-small",
    "google/mt5-small",
    "facebook/opt-125m",
    "bigscience/bloom-560m",
    "EleutherAI/gpt-neo-125m",
    "EleutherAI/pythia-70m",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-Coder-0.5B-Instruct",
    "deepseek-ai/deepseek-coder-1.3b-base",
    "bigcode/starcoder2-3b",
    "bigcode/tiny_starcoder_py",
    "Salesforce/codegen-350M-mono",
    "Salesforce/codet5-small",
    "microsoft/CodeGPT-small-py",
]
TEXTS = ["x != y ?", "Wait , isn't it ?", "a . b"]
FIELDS = [
    "matrix_version", "transformers_version", "python_version", "tokenizers_version",
    "model", "revision", "status", "error", "error_detail",
    "config_present", "config_value", "config_tokenizer_class", "config_fetch_error",
    "tokenizer_class", "is_fast", "backend_model_type", "effective_cleanup",
    "raw", "token_ids", "decoded_default", "decoded_false", "decoded_true",
    "default_equals_raw", "false_equals_true", "default_equals_false", "default_equals_true",
]


def err(exc):
    return type(exc).__name__, str(exc).replace("\n", " ")[:600]


def freeze(out):
    from huggingface_hub import HfApi
    api = HfApi()
    manifest = {"created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "models": []}
    for m in MODELS:
        row = {"model": m}
        try:
            info = api.model_info(m)
            row["revision"] = info.sha
            row["status"] = "ok"
        except Exception as exc:
            row["status"] = "revision_error"
            row["error"], row["detail"] = err(exc)
        manifest["models"].append(row)
        print(json.dumps(row), flush=True)
    Path(out).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def version(package):
    try:
        return importlib.metadata.version(package)
    except Exception:
        return "unavailable"


def run(manifest, output, version_label):
    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    roots = data["models"]
    # Import errors are reported for all 20 × 3 cases, preserving the matrix shape.
    try:
        from huggingface_hub import hf_hub_download
        from transformers import AutoTokenizer
        import transformers
        tver = transformers.__version__
        import_failure = None
    except Exception as exc:
        tver = "unavailable"
        import_failure = exc
    base = {"matrix_version": version_label, "transformers_version": tver,
            "python_version": platform.python_version(),
            "tokenizers_version": version("tokenizers")}
    n_errors = 0
    with open(output, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for entry in roots:
            model = entry["model"]
            row = {**base, "model": model, "revision": entry.get("revision", "")}
            if import_failure is not None:
                row["status"] = "import_error"
                row["error"], row["error_detail"] = err(import_failure)
            elif entry.get("status") != "ok":
                row["status"] = "revision_error"
                row["error"] = entry.get("error", "")
                row["error_detail"] = entry.get("detail", "")
            else:
                revision = entry["revision"]
                try:
                    try:
                        fp = hf_hub_download(model, "tokenizer_config.json", revision=revision)
                        config = json.loads(Path(fp).read_text(encoding="utf-8"))
                        row["config_present"] = "clean_up_tokenization_spaces" in config
                        row["config_value"] = config.get("clean_up_tokenization_spaces", "")
                        row["config_tokenizer_class"] = config.get("tokenizer_class", "")
                    except Exception as exc:
                        row["config_present"] = "unknown"
                        name, detail = err(exc)
                        row["config_fetch_error"] = name + ": " + detail
                    tok = AutoTokenizer.from_pretrained(
                        model, revision=revision, use_fast=True, trust_remote_code=False
                    )
                    row["tokenizer_class"] = type(tok).__name__
                    row["is_fast"] = getattr(tok, "is_fast", "")
                    row["effective_cleanup"] = getattr(tok, "clean_up_tokenization_spaces", "")
                    try:
                        row["backend_model_type"] = type(tok.backend_tokenizer.model).__name__
                    except Exception:
                        row["backend_model_type"] = "unavailable"
                    row["status"] = "ok"
                except Exception as exc:
                    row["status"] = "model_error"
                    row["error"], row["error_detail"] = err(exc)
            for raw in TEXTS:
                case = {**row, "raw": raw}
                if row["status"] == "ok":
                    try:
                        ids = tok.encode(raw, add_special_tokens=False)
                        default = tok.decode(ids, skip_special_tokens=True)
                        disabled = tok.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)
                        enabled = tok.decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
                        case.update({
                            "token_ids": json.dumps(ids, separators=(",", ":")),
                            "decoded_default": default,
                            "decoded_false": disabled,
                            "decoded_true": enabled,
                            "default_equals_raw": default == raw,
                            "false_equals_true": disabled == enabled,
                            "default_equals_false": default == disabled,
                            "default_equals_true": default == enabled,
                        })
                    except Exception as exc:
                        case["status"] = "case_error"
                        case["error"], case["error_detail"] = err(exc)
                if case["status"] != "ok":
                    n_errors += 1
                writer.writerow({k: case.get(k, "") for k in FIELDS})
            print(f"{version_label} {model}: {row['status']}", flush=True)
    print(f"wrote {output} ({len(roots) * len(TEXTS)} rows; {n_errors} error rows)")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["freeze", "run"])
    p.add_argument("--manifest", default="tokenizer-fleet-manifest.json")
    p.add_argument("--out", default="")
    p.add_argument("--version", default=os.environ.get("MATRIX_VERSION", "unknown"))
    a = p.parse_args()
    if a.command == "freeze":
        freeze(a.manifest)
    else:
        run(a.manifest, a.out or f"fleet-{a.version}.csv", a.version)
