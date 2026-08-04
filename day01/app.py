from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import List


def build_parser() -> argparse.ArgumentParser:
    """Day01のCLI引数を定義します。

    原則として受講者はこの関数を編集せず、要件変更がある場合のみ調整します。
    """
    # argparse.ArgumentParser は「このCLIで使えるオプションのルール表」です。
    # ここで定義した内容が `python -m day01.app --help` にも表示されます。
    p = argparse.ArgumentParser(prog="day01")

    # --name は必須入力です。未指定の場合、argparse が自動でエラーにします。
    p.add_argument("--name", required=True)

    # --repeat は表示回数です。文字列ではなく int として受け取ります。
    # 指定がなければ default=1 により 1 回になります。
    p.add_argument("--repeat", type=int, default=1)

    # --format は text か json のどちらかだけ許可します。
    # choices にない値を指定すると、argparse が自動でエラーにします。
    p.add_argument("--format", choices=["text", "json"], default="text")
    return p


def _validate_args(args: argparse.Namespace) -> None:
    """引数の簡易バリデーションを行います（入力不備は exit code=2 で終了）。"""
    # argparse でも --name required=True を見ていますが、空文字などへの保険です。
    if not args.name:
        raise ValueError("--name is required")

    # README の要件どおり、repeat は 1〜10 だけ許可します。
    if not (1 <= args.repeat <= 10):
        raise ValueError("--repeat must be between 1 and 10")


def run(name: str, repeat: int, fmt: str) -> str:
    """課題ロジック本体です（Day01は完成形の見本として実装済み）。"""
    # まず、指定された回数分の "Hello, 名前" をリストで作ります。
    # 例: name="Taro", repeat=2 -> ["Hello, Taro", "Hello, Taro"]
    outputs: List[str] = [f"Hello, {name}" for _ in range(repeat)]

    # JSON形式を指定された場合は、辞書をJSON文字列に変換して返します。
    if fmt == "json":
        return json.dumps({"name": name, "repeat": repeat, "outputs": outputs}, ensure_ascii=False)

    # text形式の場合は、リストの要素を改行でつないで返します。
    return "\n".join(outputs)


def main(argv: List[str] | None = None) -> int:
    """CLIのエントリポイントです。

    引数解析→検証→実行→終了コードの責務を持ちます。受講者は原則編集不要です。
    """
    # ここからがCLI全体の流れです。
    # main() は「入力を読む -> チェックする -> 実行する -> 終了コードを返す」司令塔です。

    # INFO / ERROR などのログを表示するための初期設定です。
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    # 1. コマンドライン引数のルール表を作ります。
    parser = build_parser()

    # 2. 実際に入力されたコマンドライン引数を読み取ります。
    # 例: --name Taro --repeat 2 なら args.name="Taro", args.repeat=2 になります。
    args = parser.parse_args(argv)

    try:
        # 3. 入力値がREADMEの要件に合っているか確認します。
        _validate_args(args)
    except Exception as e:
        # 入力不備の場合は、エラー内容をログと標準エラーに出して終了コード2を返します。
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 2

    # 4. 実行開始時の情報をINFOログに出します。
    logging.info("name=%s repeat=%s format=%s", args.name, args.repeat, args.format)

    try:
        # 5. 実際の処理を実行し、表示する文字列を作ります。
        out = run(args.name, args.repeat, args.format)

        # 6. 作った結果を標準出力に表示します。
        print(out)

        # 正常終了なので終了コード0を返します。
        return 0
    except Exception as e:
        # 想定外のエラーが起きた場合は、ログと標準エラーに出して終了コード1を返します。
        logging.error("%s", e)
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    # `python -m day01.app` で実行されたときのスタート地点です。
    # main() の戻り値をプロセスの終了コードとして使います。
    raise SystemExit(main())
