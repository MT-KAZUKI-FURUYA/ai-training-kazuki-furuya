from __future__ import annotations

import argparse
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day08のCLI引数を定義します（入力と上限設定）。"""
    p = argparse.ArgumentParser(prog="day08")
    p.add_argument("--text", required=True)
    p.add_argument("--max-steps", type=int, default=10)
    p.add_argument("--max-retry", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")
    if not (1 <= args.max_steps <= 50):
        raise ValueError("--max-steps must be between 1 and 50")
    if not (0 <= args.max_retry <= 5):
        raise ValueError("--max-retry must be between 0 and 5")


def run_graph(*, text: str, max_steps: int, max_retry: int) -> str:
    """失敗時復帰（リトライ/フォールバック）付きのフローを実行します。

    実装ガイド：
    - 失敗パターンを1つ以上作り、復帰パスへ入ることを確認する
      - 例：JSONが壊れる→再生成
      - 例：検索ヒットなし→聞き返し
    - `max_steps` / `max_retry` を上限として必ず反映し、無限ループを防ぐ
    - 上限到達時は明示的に失敗（例外）してよい（mainがexit code=1にする）
    """
    import json

    steps = 0
    retry_count = 0

    def use_step(step_name: str) -> None:
        nonlocal steps
        steps += 1
        logging.info("step=%s (%s/%s)", step_name, steps, max_steps)
        if steps > max_steps:
            raise RuntimeError("最大ステップ数に到達したため終了しました")

    while True:
        use_step("generate")
        if "不完全なJSON" in text and retry_count == 0:
            raw_response = '{"answer": "JSONの形式が壊れています"'
        else:
            raw_response = json.dumps({"answer": f"{text} への回答です。"}, ensure_ascii=False)

        use_step("parse")
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            if retry_count >= max_retry:
                raise RuntimeError("JSONのパースに失敗し、最大リトライ回数に到達しました")
            retry_count += 1
            logging.info("JSON parse failed. retry=%s/%s", retry_count, max_retry)
            continue

        use_step("search")
        if "存在しない情報" in text:
            logging.info("search result is empty. use fallback response")
            return "検索結果が見つかりませんでした。条件を変えてもう一度質問してください。"

        return parsed["answer"]


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/上限の適用/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("max-steps=%s max-retry=%s", args.max_steps, args.max_retry)

    try:
        out = run_graph(text=args.text, max_steps=args.max_steps, max_retry=args.max_retry)
        print(out)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
