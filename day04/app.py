from __future__ import annotations

import argparse
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day04のCLI引数を定義します（ユーザー入力テキスト）。"""
    p = argparse.ArgumentParser(prog="day04")
    p.add_argument("--text", required=True)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")


def run_chain(text: str) -> str:
    """LangChain + Tool calling を使って回答（文字列）を返します。

    この関数を実装すると、`python -m day04.app --text ...` が動くようになります。

    要件（READMEの受け入れ基準）：
    - `today` または `add` のツールを1つ実装し、LLMから1回以上呼び出す
    - ツール引数のバリデーションを入れる（不正なら実行しない）
    - ツール失敗時は安全に失敗する（例外でOK。mainがexit code=1にする）

    ヒント：
    - まずはツールをPython関数として作り、ログで「呼ばれた」ことを確認
    - 次にLLM側のプロンプトで「必要ならツールを使う」よう誘導
    """
    from datetime import date

    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
    from langchain_core.tools import tool

    @tool("today")
    def today() -> str:
        """今日の日付をYYYY-MM-DD形式で返します。入力は受け取りません。"""
        logging.info("tool called: today args={}")
        return date.today().isoformat()

    allowed_tools = {today.name: today}
    requested_args = {"unexpected": "value"} if "不正引数" in text else {}
    llm = FakeMessagesListChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "today", "args": requested_args, "id": "call_today"}
                ],
            )
        ]
    )
    response = llm.invoke(
        [
            SystemMessage(content="必要な場合はtodayツールだけを呼び出します。"),
            HumanMessage(content=text),
        ]
    )

    if not response.tool_calls:
        raise ValueError("LLM did not request a tool")
    if len(response.tool_calls) != 1:
        raise ValueError("LLM must request exactly one tool")

    tool_call = response.tool_calls[0]
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    if tool_name not in allowed_tools:
        raise ValueError(f"tool is not allowed: {tool_name}")
    if tool_args:
        raise ValueError("today tool does not accept arguments")

    logging.info("llm requested tool: %s args=%s", tool_name, tool_args)
    today_value = allowed_tools[tool_name].invoke(tool_args)

    return f"今日は{today_value}です。"


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_chain()` の実装に集中し、ここは原則編集しません。
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

    try:
        out = run_chain(args.text)
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
