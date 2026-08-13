from __future__ import annotations

import argparse
import logging
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day06のCLI引数を定義します（入力・モード・ケース番号）。"""
    p = argparse.ArgumentParser(prog="day06")
    p.add_argument("--text", required=True)
    p.add_argument("--mode", choices=["normal", "attack"], default="normal")
    p.add_argument("--case", type=int, default=1)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("[ERROR] 不正な入力が検出されました: 空文字です")
    if args.mode == "attack" and not (1 <= args.case <= 3):
        raise ValueError("--case must be between 1 and 3 when --mode attack")


def run_guarded(*, text: str, mode: str, case: int) -> str:
    """入力とツール実行をガードしながら処理し、回答（文字列）を返します。

    `mode` の意味：
    - `normal`：通常入力を処理
    - `attack`：用意した「悪い入力例」を使って、ガードが効いているか確認

    実装ガイド：
    - attackケースは最低3つ用意（README参照）
    - 「禁止する行為」を明確にし、検知したら例外（または拒否文）にする
    - ツールを実装する場合は許可リストで制限する（許可されないツールは実行しない）

    返り値：
    - 標準出力に出る本文（文章）を返す
    """
    user_text = text.strip()
    if len(user_text) > 1000:
        raise ValueError("[ERROR] 不正な入力が検出されました: 入力が長すぎます")

    attack_requests = {
        1: {"tool": "reveal_secret", "args": {"name": "system_prompt"}},
        2: {"tool": "run_system_command", "args": {"command": "ls -la"}},
        3: {"tool": "delete_file", "args": {"path": "/tmp/important.txt"}},
    }
    allowed_tools = {"answer": {"text"}}

    def validate_tool_request(tool: str, args: dict[str, str]) -> None:
        if tool not in allowed_tools:
            raise ValueError("[ERROR] 不正な入力が検出されました:禁止されたパターンに一致")
        if set(args) != allowed_tools[tool]:
            raise ValueError("[ERROR] 不正な入力が検出されました:禁止されたパターンに一致")
        if not all(isinstance(value, str) and value.strip() for value in args.values()):
            raise ValueError("[ERROR] 不正な入力が検出されました:禁止されたパターンに一致")

    if mode == "attack":
        request = attack_requests[case]
        validate_tool_request(request["tool"], request["args"])

    if "天気" in user_text:
        validate_tool_request("answer", {"text": user_text})
        return "今日の天気は晴れです。"

    validate_tool_request("answer", {"text": user_text})
    return f"通常入力として処理しました: {user_text}"


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_guarded()` を実装します。ここは引数解析/検証/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        return 2

    logging.info("mode=%s case=%s", args.mode, args.case)

    try:
        out = run_guarded(text=args.text, mode=args.mode, case=args.case)
        print(out)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        return 1
    except Exception as e:
        logging.error("%s", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
