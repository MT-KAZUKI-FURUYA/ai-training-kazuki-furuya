# Day 02

## 受講者が実装する場所

- `day02/app.py` の `invoke_bedrock()`

## 目的

- AWS BedrockでLLMを呼び出せるようにする
- 失敗時に原因切り分け（認証/権限/設定/ネットワーク）できるようにする
- モデル/リージョン/主要パラメータを設定として扱う習慣をつける

## ゴール（完了条件）

- `python -m day02.app --prompt "..."` が動く
- 失敗時に原因切り分けができる（ログ/メッセージがある）

## 機能要件

CLIは次の仕様を満たしてください。

コマンド

- `python -m day02.app` で起動できること（モジュール名は固定）

必須オプション

- `--prompt`：ユーザー入力（文字列、必須）

任意オプション

- `--region`：AWSリージョン（未指定の場合は環境変数 `AWS_REGION` を利用）
- `--model-id`：BedrockのモデルID（未指定の場合は環境変数 `BEDROCK_MODEL_ID` を利用）
- `--temperature`：温度（0.0〜1.0、デフォルト `0.2`）
- `--max-tokens`：最大トークン（整数、デフォルト `512`）
- `--timeout-sec`：タイムアウト秒（整数、デフォルト `30`）

出力

- 正常時：標準出力にモデルの回答本文のみを出力する
- 失敗時：標準エラー出力にエラーメッセージを出力する

終了コード

- 正常終了：`0`
- 入力不備（`--prompt` なし、型不正、範囲外など）：`2`
- Bedrock呼び出し失敗（認証/権限/ネットワーク/タイムアウト等）：`1`

ログ

- 実行開始時に、`region` / `model-id` / `temperature` / `max-tokens` / `timeout-sec` をINFOで出す
- 例外発生時に、例外種別と要点（原因切り分けに必要な情報）をERRORで出す

### エラー条件（最低限この3つを扱う）

- 入力不備（`--prompt` が空 or 未指定）
- AWS認証/権限系の失敗
- タイムアウト

## 実装タスク

- `day02/app.py` の `invoke_bedrock()` を実装し、機能要件を満たす
- `region` / `model-id` を引数または環境変数で扱えるようにする

## 実行方法

### 必要な環境変数

```bash
# 1. .env.example を .env にコピーして設定
cp .env.example .env

# 2. AWS認証（IAMユーザーのアクセスキーを使用）
#    ~/.aws/credentials に以下を設定（詳細は training-requirements.md 参照）
#    [training]
#    aws_access_key_id = AKIA...
#    aws_secret_access_key = ...
export AWS_PROFILE=training

# 3. リージョン・モデルID（.env で設定済みなら不要）
export AWS_REGION=ap-northeast-1
export BEDROCK_MODEL_ID=jp.anthropic.claude-haiku-4-5-20251001-v1:0
```

Windows（PowerShell）の場合：

```powershell
# 1. .env.example を .env にコピーして設定
copy .env.example .env

# 2. AWS認証
$env:AWS_PROFILE = "training"

# 3. リージョン・モデルID（.env で設定済みなら不要）
$env:AWS_REGION = "ap-northeast-1"
$env:BEDROCK_MODEL_ID = "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
```

### 実行コマンド例

```bash
# 基本的な実行
python -m day02.app --prompt "日本の首都はどこですか？"

# リージョンとモデルを明示的に指定
python -m day02.app --prompt "Hello" --region ap-northeast-1 --model-id jp.anthropic.claude-haiku-4-5-20251001-v1:0

# パラメータを調整
python -m day02.app --prompt "短い俳句を作ってください" --temperature 0.8 --max-tokens 100
```

### 期待する出力例

```
日本の首都は東京です。
```

---

**以下は受講者が記入してください**

## 提出物

- `day02/app.py`
- `day02/README.md`

## セルフレビュー

- 正常系：`python -m day02.app --prompt "日本の首都はどこですか？"` で回答が返ることを確認済み（exit code=0）
- 異常系：空の `--prompt`、範囲外の `--temperature`、不正な `--max-tokens` / `--timeout-sec` が exit code=2 で失敗することを確認済み
- 異常系：不正な `--model-id` 指定時に `ValidationException` と原因がstderrへ出ることを確認済み（exit code=1）
- 境界：改行を含むやや長い入力で要約が返り、クラッシュしないことを確認済み
- 再実行：同じ入力を2回実行し、どちらも `5` が返ることを確認済み（temperature=0.0、exit code=0）

## Bedrock確認

- モデル：`jp.anthropic.claude-haiku-4-5-20251001-v1:0`
- リージョン：`ap-northeast-1`
- 主要パラメータ：`temperature=0.2`、`max_tokens=512`、`timeout_sec=30`

## リサーチメモ（任意）

調べたURLや、理解した要点をメモしてください。

- Bedrockのモデル呼び出し方法（boto3等）
    - Python から AWS Bedrock を呼び出すには `boto3` を使う。
    - モデルを実行するサービスは `bedrock-runtime`。
    - 今回は `client.converse()` を使って、会話形式でモデルへ `prompt` を送った。
    - `modelId` には通常のモデルID、または環境によっては inference profile ID を指定する。
    - `messages` にユーザーの質問を入れ、`inferenceConfig` に `temperature` や `maxTokens` を指定する。
- 利用する認証方式（研修の指示に従う）
    - 今回は SSO 確認ではなく、 `aws configure --profile training` で Access Key ID / Secret Access Key を設定した。
    - Python アプリは `.env` を読むが、AWS CLI は `.env` を自動では読まない。
    - そのため CLI 確認時は `AWS_PROFILE=training` を明示した。
    - `aws bedrock list-foundation-models` が成功すれば、Bedrock API へアクセスできる認証・権限があると判断できる。
- タイムアウト/リトライの考え方
    - `botocore.config.Config` を使うと、AWS API 呼び出し時の通信設定を指定できる。
    - `connect_timeout` は接続開始までに待つ秒数。
    - `read_timeout` は接続後、レスポンスを読み取るまでに待つ秒数。
    - タイムアウトを設定しないと、ネットワーク不調時に処理が長く止まる可能性がある。
    - `retries` で失敗時の再試行回数や方式を設定できる。
- Bedrockの一部モデルは基盤モデルIDを直接呼び出せず、inference profile ID（例：`jp.anthropic.claude-haiku-4-5-20251001-v1:0`）を指定する必要がある

### 用語解説

#### Amazon Bedrock
Amazon Bedrock は、AWS 上で生成AIモデルを使うためのサービスです。
Anthropic Claude などのモデルを、AWS の認証と権限を使って呼び出せます。

#### Bedrock Runtime
Bedrock Runtime は、実際にモデルへリクエストを送るための API。
モデル一覧を見るだけなら `bedrock`、モデルへ質問を送るなら `bedrock-runtime` を使う。

今回の Python 実装では次のように使っています。
```python
client = boto3.client("bedrock-runtime", region_name=region)
```

#### boto3
`boto3` は、Python から AWS を操作するための公式ライブラリ。
今回のアプリでは、Python から Bedrock にリクエストを送るために使う。

#### AWS CLI
AWS CLI は、ターミナルから AWS を操作するためのコマンドツールです。
以下のコマンドは、Bedrock のモデル一覧を取得します。

```bash
aws bedrock list-foundation-models --region ap-northeast-1
```

#### 環境変数
環境変数は、プログラムの外側から設定を渡す仕組みです。
今回使う主な環境変数は次の3つ。
| 環境変数 | 意味 |
|---|---|
| `AWS_REGION` | AWS のリージョン |
| `BEDROCK_MODEL_ID` | 呼び出す Bedrock モデル ID |
| `AWS_PROFILE` | 使う AWS 認証プロファイル名 |

#### .env
`.env` は、環境変数を書いておくファイルです。
毎回 `export` コマンドを打たなくても、
Python アプリ側が `load_dotenv()` で読み込めます。
※ただし、AWS CLI は `.env` を自動では読みません。

### Access Key ID
Access Key ID は、AWS CLI や Python から AWS を使うための認証情報。

ログインID、AWSアカウントID、IAMユーザー名とは別物です。

形式はだいたい次のような文字列。
```text
AKIAxxxxxxxxxxxxxxxx
```
一時的な認証情報の場合は、次のような形式もあります。
```text
ASIAxxxxxxxxxxxxxxxx
```

#### Secret Access Key
Secret Access Key は、Access Key ID とペアで使う秘密情報です。

#### リージョン

リージョンは、AWS のデータセンターの場所です。
今回使うリージョンは東京です。

```text
ap-northeast-1
```
#### inference profile ID

inference profile ID は、Bedrock で一部のモデルを呼び出すときに必要になる特別なモデル指定。

今回、使用モデル

```text
jp.anthropic.claude-haiku-4-5-20251001-v1:0
```