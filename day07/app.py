from __future__ import annotations

import argparse
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day07のCLI引数を定義します（入力と分類モード）。"""
    p = argparse.ArgumentParser(prog="day07")
    p.add_argument("--text", required=True)
    p.add_argument("--mode", choices=["llm", "rule"], default="rule")
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.text:
        raise ValueError("--text is required")


def run_graph(*, text: str, mode: str) -> str:
    """LangGraphで「分類→分岐→処理」を実行し、最終出力（文字列）を返します。

    mode:
    - `rule`：ルール（キーワード等）でintentを決めて分岐
    - `llm`：LLMでintentを分類して分岐

    受け入れ基準（README）：
    - 分岐が最低2パターンある
    - どの分岐に入ったかがログで分かる
    - 分類不能時のフォールバックがある
    """
    from typing import TypedDict

    from langgraph.graph import END, StateGraph

    class GraphState(TypedDict):
        input: str
        intent: str
        reason: str
        output: str
        errors: list[str]

    def classify(state):
        user_text = state["input"]

        if "要約" in user_text or "まとめ" in user_text:
            intent = "summarize"
            reason = "要約キーワードを検出"
        elif "手順" in user_text or "実装" in user_text:
            intent = "plan"
            reason = "手順化キーワードを検出"
        elif "教えて" in user_text or "調べて" in user_text or "とは" in user_text:
            intent = "rag"
            reason = "調査・説明キーワードを検出"
        else:
            intent = "fallback"
            reason = "分類キーワードなし"

        logging.info("intent=%s reason=%s mode=%s", intent, reason, mode)
        return {**state, "intent": intent, "reason": reason}

    def route(state):
        logging.info("branch=%s", state["intent"])
        return state["intent"]

    def rag(state):
        return {**state, "output": "RAG分岐: 関連情報を探して回答します。"}

    def summarize(state):
        return {**state, "output": "要約分岐: 入力内容を短く整理します。"}

    def plan(state):
        return {**state, "output": "タスク分解分岐: 実行手順に分けます。"}

    def fallback(state):
        return {**state, "output": "デフォルト分岐: 意図を分類できませんでした。"}

    graph = StateGraph(GraphState)
    graph.add_node("classify", classify)
    graph.add_node("rag", rag)
    graph.add_node("summarize", summarize)
    graph.add_node("plan", plan)
    graph.add_node("fallback", fallback)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        route,
        {
            "rag": "rag",
            "summarize": "summarize",
            "plan": "plan",
            "fallback": "fallback",
        },
    )
    graph.add_edge("rag", END)
    graph.add_edge("summarize", END)
    graph.add_edge("plan", END)
    graph.add_edge("fallback", END)

    app = graph.compile()
    result = app.invoke({"input": text, "intent": "", "reason": "", "output": "", "errors": []})
    return result["output"]

def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は `run_graph()` を実装します。ここは引数解析/検証/終了コードを担当します。
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    logging.info("mode=%s", args.mode)

    try:
        out = run_graph(text=args.text, mode=args.mode)
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
