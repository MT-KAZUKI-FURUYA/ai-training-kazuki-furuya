from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import List, Optional

from dotenv import load_dotenv


def build_parser() -> argparse.ArgumentParser:
    """Day02のCLI引数を定義します（READMEの機能要件に対応）。"""
    p = argparse.ArgumentParser(prog="day02")
    p.add_argument("--prompt", required=True)
    p.add_argument("--region", default=None)
    p.add_argument("--model-id", default=None)
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-tokens", type=int, default=512)
    p.add_argument("--timeout-sec", type=int, default=30)
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2）。"""
    if not args.prompt or not args.prompt.strip():
        raise ValueError("--prompt is required")
    if not (0.0 <= args.temperature <= 1.0):
        raise ValueError("--temperature must be between 0.0 and 1.0")
    if args.max_tokens <= 0:
        raise ValueError("--max-tokens must be a positive integer")
    if args.timeout_sec <= 0:
        raise ValueError("--timeout-sec must be a positive integer")


def invoke_bedrock(
    *,
    prompt: str,
    region: str,
    model_id: str,
    temperature: float,
    max_tokens: int,
    timeout_sec: int,
) -> str:
    """Bedrockを呼び出して回答本文（文字列）を返します。

    この関数を実装すると、`python -m day02.app ...` が動くようになります。

    実装ガイド：
    - boto3のBedrock Runtimeクライアントを作る（リージョンは `region` を使う）
    - `model_id` で指定されたモデルを呼び出す
    - `temperature` / `max_tokens` をリクエストに反映する
    - `timeout_sec` はHTTPクライアント設定やタイムアウト制御に反映する
    - 返すのは「回答本文のみ」（前後に装飾文を混ぜない）

    エラー時：
    - 認証/権限/ネットワーク/タイムアウトなどは例外として投げてOK
     （main側で終了コード=1にしてstderrへ出ます）
    """
    try:
        import boto3
        from botocore.config import Config
        from botocore.exceptions import (
            BotoCoreError,
            ClientError,
            ConnectTimeoutError,
            ConnectionClosedError,
            EndpointConnectionError,
            NoCredentialsError,
            PartialCredentialsError,
            ReadTimeoutError,
        )
    except ImportError as e:
        raise RuntimeError("boto3 is required: install dependencies with `pip install -r requirements.txt`") from e

    client = boto3.client(
        "bedrock-runtime",
        region_name=region,
        config=Config(
            connect_timeout=timeout_sec,
            read_timeout=timeout_sec,
            retries={"max_attempts": 2, "mode": "standard"},
        ),
    )

    try:
        response = client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}],
                }
            ],
            inferenceConfig={
                "temperature": temperature,
                "maxTokens": max_tokens,
            },
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        raise RuntimeError(
            "AWS authentication failed: credentials were not found or are incomplete. "
            "Check AWS_PROFILE, AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, or ~/.aws/credentials."
        ) from e
    except (ConnectTimeoutError, ReadTimeoutError) as e:
        raise RuntimeError(
            f"Bedrock request timed out after {timeout_sec} seconds. "
            "Check network connectivity, region, model availability, or increase --timeout-sec."
        ) from e
    except (EndpointConnectionError, ConnectionClosedError) as e:
        raise RuntimeError(
            f"Bedrock network connection failed for region={region}. "
            "Check network connectivity, proxy/VPN settings, and AWS_REGION."
        ) from e
    except ClientError as e:
        error = e.response.get("Error", {})
        code = error.get("Code", "Unknown")
        message = str(error.get("Message", str(e))).rstrip(".")
        if code in {
            "AccessDeniedException",
            "AccessDenied",
            "UnauthorizedOperation",
            "UnrecognizedClientException",
            "ExpiredTokenException",
            "InvalidSignatureException",
        }:
            raise RuntimeError(
                f"AWS authorization/authentication failed ({code}): {message}. "
                "Check IAM permissions for bedrock:InvokeModel, AWS_PROFILE, and token validity."
            ) from e
        raise RuntimeError(f"Bedrock invocation failed ({code}): {message}") from e
    except BotoCoreError as e:
        raise RuntimeError(f"Bedrock SDK error ({type(e).__name__}): {e}") from e

    content = response.get("output", {}).get("message", {}).get("content", [])
    texts = [block["text"] for block in content if isinstance(block, dict) and "text" in block]
    if not texts:
        raise RuntimeError("Bedrock response did not contain assistant text")
    return "".join(texts).strip()


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    受講者は原則 `invoke_bedrock()` のみ実装し、それ以外は触らない想定です。
    """
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        _validate_args(args)
    except Exception as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    region: Optional[str] = args.region or os.getenv("AWS_REGION")
    model_id: Optional[str] = args.model_id or os.getenv("BEDROCK_MODEL_ID")

    if not region:
        msg = "region is required: set --region or AWS_REGION"
        logging.error(msg)
        print(msg, file=sys.stderr)
        return 2

    if not model_id:
        msg = "model-id is required: set --model-id or BEDROCK_MODEL_ID"
        logging.error(msg)
        print(msg, file=sys.stderr)
        return 2

    logging.info(
        "region=%s model-id=%s temperature=%s max-tokens=%s timeout-sec=%s",
        region,
        model_id,
        args.temperature,
        args.max_tokens,
        args.timeout_sec,
    )

    try:
        reply = invoke_bedrock(
            prompt=args.prompt,
            region=region,
            model_id=model_id,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout_sec=args.timeout_sec,
        )
        print(reply)
        return 0
    except NotImplementedError as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        logging.error("%s: %s", type(e).__name__, e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
