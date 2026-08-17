from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List


def build_parser() -> argparse.ArgumentParser:
    """Day09のCLI引数を定義します（suite入力と出力先）。"""
    p = argparse.ArgumentParser(prog="day09")
    p.add_argument("--suite", required=True)
    p.add_argument("--out", default=os.path.join("day09", "result.json"))
    p.add_argument("--timeout-sec", type=int, default=30)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.suite:
        raise ValueError("--suite is required")
    if args.timeout_sec <= 0:
        raise ValueError("--timeout-sec must be a positive integer")


def load_suite(path: str) -> List[Dict[str, Any]]:
    """テスト入力セットを読み込んでケース配列を返します。

    形式は自由ですが、まずはJSONを推奨します。

    例（suite.json）：
    - `[{"id":"case1","input":"..."}, {"id":"case2","input":"..."}]`

    実装ガイド：
    - `path` を開いて読み、ケース配列（list[dict]）にして返す
    - ケースは最低 `id` と `input` を含む想定
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"--suite file not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    except json.JSONDecodeError as e:
        print(f"--suite must be valid JSON: {e}", file=sys.stderr)
        raise SystemExit(2)

    if not isinstance(data, list):
        print("--suite must be a JSON array", file=sys.stderr)
        raise SystemExit(2)

    cases: List[Dict[str, Any]] = []
    for index, case in enumerate(data, start=1):
        if not isinstance(case, dict):
            print(f"case {index} must be an object", file=sys.stderr)
            raise SystemExit(2)
        if not case.get("id"):
            print(f"case {index} must have id", file=sys.stderr)
            raise SystemExit(2)
        if "input" not in case:
            print(f"case {case['id']} must have input", file=sys.stderr)
            raise SystemExit(2)
        cases.append(case)

    return cases


def run_case(case: Dict[str, Any], timeout_sec: int) -> Dict[str, Any]:
    """1ケースを実行して結果dictを返します。

    実装ガイド：
    - ここでは「どのDayの成果物を評価するか」を決めて呼び出してください
      例：Day08のフローを呼ぶ、または最終課題を呼ぶ、など
    - 戻り値は最低限このキーを含めると扱いやすいです
      - `id`: ケースID
      - `passed`: bool
      - `reason`: str（失敗理由）
      - `output`: 任意（実際の出力）

    注意：
    - `timeout_sec` を使って、長時間実行にならないようにしてください
    """
    start = time.perf_counter()
    case_id = str(case.get("id", "unknown"))
    input_text = str(case.get("input", ""))

    if not input_text.strip():
        return {
            "id": case_id,
            "passed": False,
            "reason": "input is empty",
            "output": "",
        }

    if time.perf_counter() - start > timeout_sec:
        return {
            "id": case_id,
            "passed": False,
            "reason": "timeout",
            "output": "",
        }

    return {
        "id": case_id,
        "passed": True,
        "reason": "stub evaluation completed",
        "output": input_text,
    }


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    suite読み込み→各ケース実行→結果JSON出力までを制御します。
    受講者は `load_suite()` と `run_case()` を実装します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    try:
        suite = load_suite(args.suite)
        results: List[Dict[str, Any]] = []
        ok = 0
        ng = 0

        for case in suite:
            start = time.perf_counter()
            try:
                r = run_case(case, timeout_sec=args.timeout_sec)
                r.setdefault("duration_ms", int((time.perf_counter() - start) * 1000))
                passed = bool(r.get("passed", False))
                ok += 1 if passed else 0
                ng += 0 if passed else 1
                results.append(r)
            except NotImplementedError as e:
                logging.error(str(e))
                print(str(e), file=sys.stderr)
                return 1

        out_obj = {
            "summary": {"passed": ok, "failed": ng, "total": ok + ng},
            "results": results,
        }
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=2)

        print(f"passed={ok} failed={ng} total={ok + ng}")
        return 0
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
