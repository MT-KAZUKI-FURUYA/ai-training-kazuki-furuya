# Day 01

## 受講者が実装する場所

- `day01/app.py`（基本はこのファイルを編集）

## 目的

- 開発環境のセットアップができる状態にする
- GitHubのPR提出フローに慣れる
- Pythonで小さなCLIを作り、例外/ログ/READMEの書き方を身につける

## ゴール（完了条件）

- READMEどおりに第三者が実行できる
- 入力不備で終了コード `2` になり、標準エラーに分かりやすいメッセージが出る

## 機能要件

### 機能要件

コマンド

- `python -m day01.app` で起動できること（モジュール名は固定）

必須オプション

- `--name`：表示したい名前（文字列、必須）

任意オプション

- `--repeat`：繰り返し回数（整数、デフォルト `1`、1〜10）
- `--format`：出力形式（`text` / `json`、デフォルト `text`）

出力

- `--format text` の場合：標準出力に、指定回数分のテキストを出す
- `--format json` の場合：標準出力にJSONを出す
  - 例：`{"name":"Taro","repeat":2,"outputs":["Hello, Taro","Hello, Taro"]}`

終了コード

- 正常終了：`0`
- 入力不備（未指定、範囲外など）：`2`

ログ

- 実行開始時に、`name` / `repeat` / `format` をINFOで出す
- 例外発生時はERRORで出す

### 受け入れ基準

- `--name` 未指定で終了コード `2`、標準エラーに分かりやすいメッセージが出る
- `--repeat 2` で2行（または2要素）出る
- `--format json` でJSONとしてパース可能な文字列が出る

## 実装タスク

- `day01/app.py` を編集し、機能要件を満たす
- 例外時は標準エラーへメッセージを出し、終了コードを要件どおりにする

## 実行方法

### セットアップ

```bash
# 仮想環境の作成と有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 実行コマンド例

```bash
# 基本的な実行
python -m day01.app --name "Taro"

# 繰り返し回数を指定
python -m day01.app --name "Taro" --repeat 3

# JSON形式で出力
python -m day01.app --name "Taro" --repeat 2 --format json
```

### 期待する出力例

```
# --name "Taro" の場合
Hello, Taro

# --name "Taro" --repeat 2 --format json の場合
{"name": "Taro", "repeat": 2, "outputs": ["Hello, Taro", "Hello, Taro"]}
```

---

**以下は受講者が記入してください**

- 追加で確認した入力例：
  - `python3 -m day01.app --name Taro`
  - `python3 -m day01.app --name Taro --repeat 2`
  - `python3 -m day01.app --name Taro --repeat 8 --format json`
  - `python3 -m day01.app --name Taro --repeat 11`
  - `python3 -m day01.app --name Furuya`
  - `python3 -m day01.app --name FuFu --format json`

- 発生したエラーと対処：
  - `python` コマンドが見つからない場合は `python3` を使用した
  -  `--name` 未指定で実行した場合、必須引数エラーになることを確認した
  - `--repeat 0と11` は範囲外のためエラーになることを確認した

## 提出物

- `day01/app.py`
- `day01/README.md`

## セルフレビュー

- 正常系：`--name Taro` で期待どおりに表示される
- 異常系：`--name` 未指定でエラーになり、メッセージが分かりやすい
- 境界：`--name` に長い文字列や記号を入れても壊れない
- 再実行：同じ入力で複数回実行しても安定して同じ結果になる

## リサーチメモ（任意）

調べたURLや、理解した要点をメモしてください。

- Python仮想環境（venv等）
  - `venv` は、プロジェクトごとにPythonの実行環境を分けるための仕組み。
  - 仮想環境の有効化は `source .venv/bin/activate` で行う。

- 依存管理（requirements/pyprojectの考え方）
  - `pip install -r requirements.txt` で、必要なライブラリをまとめてインストールできる。

- CLIの引数処理（例：argparse等）
  - `argparse` は、コマンドライン引数を扱うためのPython標準ライブラリ。
  - `argparse` を使うと、プログラム内で `args.name` や `args.repeat` のように値を扱える。
  - 不正な入力があった場合、`argparse` が自動でエラーを出してくれる。
  - `choices=["text", "json"]` のように指定すると、許可する値を制限できる。
- コードの読み解き方
  - 今回の `day01/app.py` では、最初に `main()` が呼ばれる。
  - `main()` を上から読み、そこから呼ばれている `build_parser()`、`_validate_args()`、`run()` を順番に確認すると流れを追いやすい。
  - 処理の流れ：
```
python3 -m day01.app
  ↓
main()
  ↓
build_parser()
  ↓
parser.parse_args()
  ↓
_validate_args()
  ↓
run()
  ↓
print()
```
- ログ（INFO/ERRORの使い分け）
  - `INFO` は正常な処理の開始や設定値の確認に使う。
  - `ERROR` は入力不備や例外など、問題が発生したときに使う。
  - `print()` はユーザーに結果を見せるため、`logging` は実行状況や原因を追うために使う。

- GitHub：ブランチ作成→PR→修正push
  - 実務では `main` ブランチに直接pushせず、作業用ブランチを作って作業する。
  - 変更後はコミットしてGitHubにpushし、Pull Requestを作成する。
  - PR作成後に修正が必要な場合は、同じブランチに追加でpushするとPRに反映される。
