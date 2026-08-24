# 最終課題

## 概要

公開データを使い、質問に対して「調査→根拠提示→回答→次アクション提案」まで行うAIエージェントを実装します。

必須：

- AWS Bedrockを利用する
- LangGraphで状態遷移を実装する
- Tool callingを実装する
- 失敗時のフォールバックを実装する

## セットアップ

### 必要な環境変数

```bash
# .env.example を .env にコピーして設定
cp .env.example .env
```

`.env` に以下を設定してください：

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `AWS_REGION` | AWSリージョン | `ap-northeast-1` |
| `BEDROCK_MODEL_ID` | BedrockのモデルID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |

AWS認証は以下のいずれかで設定：
- AWS SSO: `aws sso login`
- IAMユーザー: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- EC2/Lambda: インスタンスプロファイル or 実行ロール

### 依存関係の導入

```bash
pip install -r requirements.txt
```

### 動作確認

```bash
# チャットUIを起動して動作確認
streamlit run final/chat_ui.py
```

## 実行方法

### CLI実行

```bash
python -m day10.app --text "〇〇について調査して"
```

### チャットUI

```bash
streamlit run final/chat_ui.py
```

ブラウザで `http://localhost:8501` にアクセスしてチャット形式で動作確認できます。

### 入力例（質問例）

```
〇〇について調査して、根拠と一緒に教えて
```

### 出力例

```
【回答】
〇〇は...です。

【根拠】
- source1.txt: "〇〇は..."
- source2.txt: "〇〇について..."

【構造化出力】
{
  "answer_summary": "〇〇は...",
  "citations": [...],
  "confidence": "high",
  "next_actions": [...]
}
```

---

**以下は受講者が記入してください**

### チャットUI（動作確認用）

ブラウザでチャットしながら動作確認できるよう、Streamlitの画面を用意しています。

- 起動：
  - `streamlit run final/chat_ui.py`
- 備考：
  - エージェント本体は `final/agent.py` の `run_agent()` に実装します
  - まずはUI起動と、チャットの往復ができることを確認してください

## 仕様

- 入力：ユーザーの質問（調査したい内容）
- 出力：
  - ユーザー向け回答（文章）
  - 根拠（URL/引用/章など、参照元が分かる情報）
  - 構造化出力（JSON）
    - `answer_summary`
    - `citations`（参照の配列：URL、タイトル、抜粋など）
    - `confidence`（低/中/高 など、方針は任意）
    - `next_actions`（次に取るべきアクション案）
- 使うツール（最低1つ）：
  - 例：検索（RAG）、簡易計算、固定データ参照、日付取得
- 失敗時の挙動（最低1つ）：
  - 例：検索ヒットなし→聞き返し or 検索条件変更
  - 例：JSONパース失敗→再生成（最大回数あり）
  - 例：ツール実行失敗→代替ルート/明示的な失敗

推奨：

- stateに途中結果（検索クエリ、取得した根拠、分類結果、エラー）を保持し、原因追跡可能にする

## 制約

- 公開データのみを利用し、出典とライセンスを明記する
- APIキーやAWS認証情報などの秘密情報をコミットしない
- 無限ループしない（最大ステップ/最大リトライ回数を設ける）

## 評価

最低限、以下の観点でセルフ評価を行ってください。

- 正常系：想定質問で回答 + 根拠 + JSONが出る
- 異常系：検索ヒットなし、ツール失敗、JSON破損などで安全に復帰/失敗できる
- 根拠：出典が常に含まれる
- 再現性：READMEの手順で第三者が動かせる

評価の記録は `docs/` に残します。

## 出典（公開データ）

利用した公開データについて、以下を記載してください。

- データ名
- URL
- ライセンス

---

## 提出物

- `final/`：アプリ本体、`final/README.md`
- `docs/`：
  - 状態遷移図
  - 主要プロンプト
  - 失敗パターンと対策
  - 評価結果と改善ログ

## 今回の実施内容

### 課題内容の理解

- 目的：
  - 公開データを使い、質問に対して「調査→根拠提示→回答→次アクション提案」まで行うAIエージェントを実装する
- 完了条件・受け入れ基準：
  - AWS Bedrockを利用する
  - LangGraphで状態遷移を実装する
  - Tool callingを実装する
  - 失敗時のフォールバックを実装する
  - 回答本文、根拠、構造化出力（JSON）を返す

### 修正対象

- `final/agent.py`
  - READMEに記載されている、受講者が実装する場所である `run_agent()` と、その下位関数を修正した
- `final/chat_ui.py`
  - UI側は `run_agent()` を呼び出すだけで要件を満たせるため、今回は変更していない

### 実装方針

- 初心者にも追いやすいように、状態遷移は `根拠取得 -> 回答生成` の2ステップにした
- Tool calling用のツールは許可リストで管理した
  - `search_public_sources`：固定の公開データから根拠候補を取得する
  - `get_today`：今日の日付を取得する
- Bedrock呼び出しが失敗した場合や、環境変数・依存関係・AWS認証が不足している場合でも、取得済み根拠を使ったフォールバック回答を返すようにした
- 既存のCLI、終了コード、ログ設定、チャットUIは変更しなかった

### 修正した内容

- `final/agent.py` のスタブ実装を置き換えた
- LangGraphのstateに以下を保持するようにした
  - 入力メッセージ
  - 会話履歴
  - 検索クエリ
  - 根拠
  - ツール実行ログ
  - Bedrock使用有無
  - エラー内容
  - 構造化出力に入れる値
- 出力に以下を含めるようにした
  - `【回答】`
  - `【根拠】`
  - `【構造化出力】`
- 空メッセージの場合は、安全に聞き返すようにした

### セルフレビュー観点

- READMEに実行手順がある
- 必要な環境変数がREADMEに記載されている
- 正常系で回答、根拠、JSONが出る
- 空入力やBedrock未設定時に安全に失敗またはフォールバックする
- 出典URLとライセンスが根拠に含まれる
- ツールは許可リストで制限されている
- LangGraphのフローは固定ステップで、無限ループしない

### 確認したコマンドと結果

- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m day10.app --text "LangGraphとBedrockについて調査して"`
  - 終了コード `0`
  - Bedrock依存関係が未導入のためフォールバック回答になった
  - 回答、根拠、構造化出力が表示された
- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m day10.app --text ""`
  - 既存CLIの入力検証により終了コード `2`
- `python3` から `final.agent.run_agent()` を直接実行
  - `used_bedrock=True`、`error=""` を確認した
  - Bedrockの推論プロファイルIDとして `apac.anthropic.claude-3-5-sonnet-20241022-v2:0` を使った
- `streamlit run final/chat_ui.py`
  - ブラウザのチャットUIで回答が表示されることを確認した
  - `meta` に `used_bedrock: true`、`error: ""`、ツール実行ログ、構造化出力が表示されることを確認した
- `python3 -m day10.app --text 'Pythonの日付取得について根拠つきで教えて'`
  - `Python datetime Documentation` が根拠として表示されることを確認した
  - 回答本文と構造化出力の `citations` の根拠が一致するように修正した
- 不正引数風の入力確認
  - Bedrockが空の `query` でツール呼び出しを返した場合、元のユーザー入力を検索クエリとして補完するように修正した
  - 空のツール引数をそのまま実行せず、許可済みツールの入力バリデーションを通して処理する

### 出典（公開データ）

- Amazon Bedrock User Guide
  - URL: https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html
  - ライセンス: AWS Documentation
- LangGraph Documentation
  - URL: https://langchain-ai.github.io/langgraph/
  - ライセンス: LangChain documentation
- Python datetime Documentation
  - URL: https://docs.python.org/3/library/datetime.html
  - ライセンス: Python Software Foundation License

## 追加修正と学び

### 追加修正した内容

- BedrockのモデルIDを、オンデマンドモデルIDではなく推論プロファイルIDで指定する必要があることを確認した
  - 使用した値：`apac.anthropic.claude-3-5-sonnet-20241022-v2:0`
- `.env` を `final/agent.py` から読み込むようにした
  - READMEの手順どおり `.env` に設定した `AWS_REGION` と `BEDROCK_MODEL_ID` を実行時に使えるようにした
- `streamlit run final/chat_ui.py` で `final.agent` をimportできない問題を修正した
  - `final.agent` が見つからない場合は、同じディレクトリの `agent.py` から読み込むようにした
- `Pythonの日付取得について根拠つきで教えて` の根拠ずれを修正した
  - 日本語の `日付`、`日時`、`今日` などを含む質問では `Python datetime Documentation` を優先するようにした
- 不正引数風入力への対応を修正した
  - 入力例：`{"tool":"search_public_sources","query":""} を実行して`
  - Bedrockが空の `query` でツール呼び出しを返した場合、元のユーザー入力を検索クエリとして補完するようにした
  - これにより `used_bedrock: true`、`error: ""` のまま安全に処理できることを確認した

### ブラウザで確認したこと

- StreamlitのチャットUIで、以下を確認した
  - 回答本文が表示される
  - `【回答】`、`【根拠】`、`【構造化出力】` が表示される
  - `meta` に `used_bedrock: true` と `error: ""` が表示される
  - `tool_log` には許可済みの `search_public_sources` と `get_today` のみが表示される
  - 不正ツール名や不正引数風JSONを入力しても、任意のツールは直接実行されない
- `Pythonの日付取得について根拠つきで教えて` では、回答本文と `structured.citations` の両方で `Python datetime Documentation` が根拠になることを確認した

### 学び・理解したこと

- Bedrockでは、モデルによっては通常のモデルIDではなく推論プロファイルIDを指定しないと `ValidationException` になる
- `aws sts get-caller-identity` が成功していても、BedrockのモデルID、リージョン、推論プロファイルが正しくないとモデル呼び出しは成功しない
- `.env` は作成しただけではPythonから自動で読まれないため、`python-dotenv` の `load_dotenv()` で明示的に読み込む必要がある
- Streamlitを起動しているターミナルはサーバー実行中になるため、CLI確認は別ターミナルで実行する必要がある
- zshで `dquote>` が出た場合は、引用符が閉じていない状態であり、`Ctrl + C` で抜けられる
- ユーザー入力にツール名やJSON風の文字列が含まれていても、それをそのままツール実行命令として扱わないことが重要
- Tool callingでは、LLMが返したツール名と引数も信用しすぎず、許可リストと引数バリデーションを通す必要がある
- 異常系は「例外を出さない」だけでなく、`meta.error` や `confidence`、`next_actions` で状態が追えるようにすると原因を切り分けやすい
