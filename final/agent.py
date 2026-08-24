from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Literal, TypedDict


PUBLIC_SOURCES: List[Dict[str, str]] = [
    {
        "title": "Amazon Bedrock User Guide",
        "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html",
        "license": "AWS Documentation",
        "excerpt": "Amazon Bedrock is a fully managed service for using foundation models through an API.",
        "keywords": "aws bedrock model foundation api llm",
    },
    {
        "title": "LangGraph Documentation",
        "url": "https://langchain-ai.github.io/langgraph/",
        "license": "LangChain documentation",
        "excerpt": "LangGraph is a framework for building stateful, multi-actor applications with LLMs.",
        "keywords": "langgraph state graph workflow agent",
    },
    {
        "title": "Python datetime Documentation",
        "url": "https://docs.python.org/3/library/datetime.html",
        "license": "Python Software Foundation License",
        "excerpt": "The datetime module supplies classes for manipulating dates and times.",
        "keywords": "python datetime date today",
    },
]


class AgentState(TypedDict, total=False):
    message: str
    history: List[Dict[str, str]]
    query: str
    citations: List[Dict[str, str]]
    tool_log: List[Dict[str, Any]]
    answer_summary: str
    reply: str
    confidence: Literal["low", "medium", "high"]
    next_actions: List[str]
    error: str
    used_bedrock: bool


def _search_public_sources(query: str) -> Dict[str, Any]:
    """固定の公開データから、質問に近い出典を返します。"""
    normalized_query = query.lower()
    words = {w.lower() for w in query.replace("　", " ").split() if w.strip()}
    scored: List[tuple[int, Dict[str, str]]] = []
    japanese_hints = {
        "Python datetime Documentation": ["日付", "日時", "今日", "現在日", "現在時刻"],
        "Amazon Bedrock User Guide": ["bedrock", "aws", "基盤モデル"],
        "LangGraph Documentation": ["langgraph", "状態遷移", "グラフ"],
    }

    for source in PUBLIC_SOURCES:
        haystack = " ".join(source.values()).lower()
        score = sum(1 for word in words if word in haystack)
        score += sum(1 for hint in japanese_hints[source["title"]] if hint in normalized_query)
        if score:
            scored.append((score, source))

    if not scored and query.strip():
        scored = [(1, source) for source in PUBLIC_SOURCES[:2]]

    citations = [
        {
            "title": source["title"],
            "url": source["url"],
            "excerpt": source["excerpt"],
            "license": source["license"],
        }
        for _, source in sorted(scored, key=lambda item: item[0], reverse=True)[:3]
    ]
    return {"query": query, "citations": citations}


def _get_today(_: Dict[str, Any] | None = None) -> Dict[str, str]:
    """回答時点の日付を返します。"""
    return {"today": date.today().isoformat()}


ALLOWED_TOOLS = {
    "search_public_sources": _search_public_sources,
    "get_today": _get_today,
}


def _run_tool(name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    if name not in ALLOWED_TOOLS:
        raise ValueError(f"tool is not allowed: {name}")
    if not isinstance(tool_input, dict):
        raise ValueError("tool input must be a dict")
    if name == "search_public_sources":
        query = str(tool_input.get("query", "")).strip()
        if not query:
            raise ValueError("query is required")
        return ALLOWED_TOOLS[name](query)
    return ALLOWED_TOOLS[name](tool_input)


def _normalize_tool_input(name: str, tool_input: Dict[str, Any], state: AgentState) -> Dict[str, Any]:
    if name == "search_public_sources" and not str(tool_input.get("query", "")).strip():
        return {**tool_input, "query": state["message"]}
    return tool_input


def _collect_evidence(state: AgentState) -> AgentState:
    query = state["message"].strip()
    tool_result = _run_tool("search_public_sources", {"query": query})
    today_result = _run_tool("get_today", {})
    return {
        **state,
        "query": query,
        "citations": tool_result["citations"],
        "tool_log": [
            {"tool": "search_public_sources", "input": {"query": query}, "output": tool_result},
            {"tool": "get_today", "input": {}, "output": today_result},
        ],
    }


def _bedrock_answer(state: AgentState) -> str:
    import boto3
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    region = os.getenv("AWS_REGION", "ap-northeast-1")
    model_id = os.getenv("BEDROCK_MODEL_ID")
    if not model_id:
        raise RuntimeError("BEDROCK_MODEL_ID is not set")

    client = boto3.client("bedrock-runtime", region_name=region)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text": (
                        "次の質問に、根拠を明示して日本語で簡潔に回答してください。\n"
                        f"質問: {state['message']}\n"
                        f"根拠候補: {json.dumps(state.get('citations', []), ensure_ascii=False)}"
                    )
                }
            ],
        }
    ]
    tool_config = {
        "tools": [
            {
                "toolSpec": {
                    "name": "search_public_sources",
                    "description": "固定の公開データから質問に関係する出典を検索する",
                    "inputSchema": {
                        "json": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                        }
                    },
                }
            },
            {
                "toolSpec": {
                    "name": "get_today",
                    "description": "今日の日付を返す",
                    "inputSchema": {"json": {"type": "object", "properties": {}}},
                }
            },
        ]
    }
    system = [
        {
            "text": (
                "あなたは公開データだけを根拠に回答する調査エージェントです。"
                "根拠が不足する場合は不足していると明記してください。"
            )
        }
    ]

    response = client.converse(
        modelId=model_id,
        messages=messages,
        system=system,
        toolConfig=tool_config,
        inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
    )
    content = response["output"]["message"]["content"]
    tool_uses = [block["toolUse"] for block in content if "toolUse" in block]

    if tool_uses:
        messages.append(response["output"]["message"])
        tool_results = []
        for tool_use in tool_uses:
            tool_input = _normalize_tool_input(
                tool_use["name"], tool_use.get("input", {}), state
            )
            result = _run_tool(tool_use["name"], tool_input)
            tool_results.append(
                {
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content": [{"json": result}],
                    }
                }
            )
        messages.append({"role": "user", "content": tool_results})
        response = client.converse(
            modelId=model_id,
            messages=messages,
            system=system,
            toolConfig=tool_config,
            inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
        )
        content = response["output"]["message"]["content"]

    return "\n".join(block["text"] for block in content if "text" in block).strip()


def _fallback_summary(state: AgentState) -> str:
    if not state.get("citations"):
        return "公開データの候補が見つからなかったため、検索条件を変えて再確認してください。"
    titles = "、".join(citation["title"] for citation in state["citations"])
    return f"質問に関連する公開データとして {titles} を確認しました。詳細は根拠を参照してください。"


def _build_reply(state: AgentState) -> str:
    citations = state.get("citations", [])
    citation_lines = [
        f"- {item['title']}: {item['excerpt']} ({item['url']})" for item in citations
    ] or ["- 該当する公開データが見つかりませんでした。"]
    structured = {
        "answer_summary": state["answer_summary"],
        "citations": citations,
        "confidence": state["confidence"],
        "next_actions": state["next_actions"],
    }
    return (
        "【回答】\n"
        f"{state['answer_summary']}\n\n"
        "【根拠】\n"
        + "\n".join(citation_lines)
        + "\n\n【構造化出力】\n"
        + json.dumps(structured, ensure_ascii=False, indent=2)
    )


def _answer(state: AgentState) -> AgentState:
    try:
        summary = _bedrock_answer(state)
        used_bedrock = True
        error = ""
    except Exception as exc:
        summary = _fallback_summary(state)
        used_bedrock = False
        error = str(exc)

    next_actions = [
        "必要に応じて質問の対象範囲を狭める",
        "一次情報のURLやライセンスを追加で確認する",
    ]
    if error:
        next_actions.append("AWS_REGION / BEDROCK_MODEL_ID / AWS認証設定を確認する")

    new_state: AgentState = {
        **state,
        "answer_summary": summary,
        "confidence": "medium" if used_bedrock else "low",
        "next_actions": next_actions,
        "error": error,
        "used_bedrock": used_bedrock,
    }
    return {**new_state, "reply": _build_reply(new_state)}


def _build_graph():
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(AgentState)
    graph.add_node("collect_evidence", _collect_evidence)
    graph.add_node("answer", _answer)
    graph.add_edge(START, "collect_evidence")
    graph.add_edge("collect_evidence", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


def _run_flow(message: str, history: List[Dict[str, str]]) -> AgentState:
    initial_state: AgentState = {"message": message, "history": history}
    try:
        return _build_graph().invoke(initial_state)
    except ModuleNotFoundError as exc:
        if exc.name != "langgraph":
            raise
        state = _collect_evidence(initial_state)
        state["error"] = "langgraph is not installed; ran the fallback sequential flow"
        return _answer(state)


def run_agent(message: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
    """チャットUI（`final/chat_ui.py`）から呼び出されるエージェントの入口です。

    受講者が実装する場所は基本的にこの関数（またはこの関数が呼ぶ下位関数）です。

    実装の方針（例）：
    - LangGraphでstateを持つフローを構築
    - ツール（RAG検索、計算、日付取得など）をTool callingで呼び出す
    - 失敗時フォールバック（検索ヒットなし、JSON破損など）を入れる

    引数：
    - message: ユーザーの最新発話
    - history: これまでの会話履歴（role/contentの配列）

    戻り値（辞書）：
    - reply: str（ユーザーに見せる本文）
    - meta: dict（任意。デバッグ用情報や構造化出力を入れてよい）

    注意：
    - APIキーや認証情報をコードに直書きしない
    - 例外は握りつぶさず、UI側で原因が分かるよう meta に入れるか適切にエラー化する
    """
    history = history or []
    if not message or not message.strip():
        return {
            "reply": "質問が空です。調査したい内容を入力してください。",
            "meta": {
                "error": "message is empty",
                "structured": {
                    "answer_summary": "",
                    "citations": [],
                    "confidence": "low",
                    "next_actions": ["調査したい質問を入力する"],
                },
            },
        }

    result = _run_flow(message, history)
    return {
        "reply": result["reply"],
        "meta": {
            "history_len": len(history),
            "used_bedrock": result.get("used_bedrock", False),
            "error": result.get("error", ""),
            "tool_log": result.get("tool_log", []),
            "structured": {
                "answer_summary": result.get("answer_summary", ""),
                "citations": result.get("citations", []),
                "confidence": result.get("confidence", "low"),
                "next_actions": result.get("next_actions", []),
            },
        },
    }
