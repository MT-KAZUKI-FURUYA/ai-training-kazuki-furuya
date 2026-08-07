from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    """Day03のCLI引数を定義します（要件文とリトライ回数）。"""
    p = argparse.ArgumentParser(prog="day03")
    p.add_argument("--requirements", required=True)
    p.add_argument("--max-retry", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.requirements or not args.requirements.strip():
        raise ValueError("--requirements is required")
    if not (0 <= args.max_retry <= 3):
        raise ValueError("--max-retry must be between 0 and 3")


def generate_json(requirements: str) -> str:
    """要件文字列から、JSON文字列（本文のみ）を生成して返します。

    この関数を実装すると、`python -m day03.app --requirements ...` が動くようになります。

    実装ガイド：
    - LLMに「JSONだけを返す」ように強く指示する
    - `title` / `tasks` / `risks` を必ず含める
    - `tasks` は配列で、各要素に `id` / `description` / `acceptance_criteria` を含める
    - 返す文字列は JSON として `json.loads()` できる必要がある

    注意：
    - 余計な前置き/後置きの文章を混ぜない
    - 壊れやすいので、プロンプトは短く・形式を固定する
    """
    region = os.getenv("AWS_REGION")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not region:
        raise RuntimeError("AWS_REGION is required")
    if not model_id:
        raise RuntimeError("BEDROCK_MODEL_ID is required")

    try:
        import boto3
        from botocore.config import Config
    except ImportError as e:
        raise RuntimeError("boto3 is required: install dependencies with `pip install -r requirements.txt`") from e

    prompt = f"""次の形式のJSONだけを出力してください。先頭は必ず {{、末尾は必ず }} にしてください。
説明文、Markdown、コードフェンスは禁止です。

{{
  "title": "要約タイトル",
  "tasks": [
    {{"id": 1, "description": "作業内容", "acceptance_criteria": "完了条件"}}
  ],
  "risks": ["想定リスク"]
}}
条件: tasksは2〜3件、idは1からの連番、acceptance_criteriaは文字列。
要件: {requirements.strip()}
"""

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(retries={"max_attempts": 2, "mode": "standard"}),
    )
    response = client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "temperature": 0.0,
            "maxTokens": 1024,
        },
    )

    content = response.get("output", {}).get("message", {}).get("content", [])
    texts = [block["text"] for block in content if isinstance(block, dict) and "text" in block]
    if not texts:
        raise RuntimeError("Bedrock response did not contain assistant text")

    text = "".join(texts).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]

    obj = validate_json(text)
    return json.dumps(obj, ensure_ascii=False, indent=2)


def validate_json(text: str) -> Dict[str, Any]:
    """生成結果のJSONを検証します（必須キーと型）。"""
    obj = json.loads(text)
    for key in ("title", "tasks", "risks"):
        if key not in obj:
            raise ValueError(f"missing key: {key}")
    if not isinstance(obj.get("tasks"), list):
        raise ValueError("tasks must be a list")
    return obj


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    JSON生成→検証→（失敗時は再生成）までを制御します。受講者は `generate_json()` を実装します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    last_err: Exception | None = None
    for _ in range(args.max_retry + 1):
        try:
            text = generate_json(args.requirements)
            validate_json(text)
            print(text)
            return 0
        except NotImplementedError as e:
            logging.error(str(e))
            print(str(e), file=sys.stderr)
            return 1
        except Exception as e:
            last_err = e

    msg = str(last_err) if last_err else "validation failed"
    logging.error(msg)
    print(msg, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
