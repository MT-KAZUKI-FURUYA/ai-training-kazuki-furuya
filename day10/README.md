# Day 10

## 受講者が実装する場所

- `day10/app.py`（統合の入口）
- `final/agent.py` の `run_agent()`（最終課題の中身）

## 目的

- Day01〜Day09の部品を統合し、最終課題の最小フローを動かす
- 最終課題のREADME/設計メモの骨格を作る

## ゴール（完了条件）

- `python -m day10.app --text "..."` が起動できる
- `final/agent.py`（スタブでも可）を呼び出す導線がある

## 統合内容

以下を最終課題へ統合します（すべてを完璧に統合できなくてもOKですが、最小フローは動かします）。

- Bedrock呼び出し
- 構造化出力（JSON）
- Tool calling（最低1つ）
- LangGraphでの状態遷移
- フォールバック（最低1つ）
- ログ/エラー処理

## 機能要件

コマンド

- `python -m day10.app` で起動できること（モジュール名は固定）

必須オプション

- `--text`：最終課題へ渡す入力（文字列、必須）

出力

- 標準出力に、最終課題の最小フローの結果を出す（未完成ならエラーでも可）

終了コード

- 正常終了：`0`
- 入力不備：`2`
- 実行失敗：`1`

受け入れ基準

- `final/` に実装したエージェント（またはスタブ）を呼び出す導線がある

## 実装タスク

- `day10/app.py` を編集し、`final.agent.run_agent()` を呼び出して結果を標準出力へ出す
- `final/README.md` と `docs/` の骨格を整える

## 実行方法

### CLI実行

```bash
# 基本的な実行
python -m day10.app --text "〇〇について調査して"
```

### チャットUI（最終課題の動作確認用）

```bash
# チャットUIを起動
streamlit run final/chat_ui.py
```

詳細は `final/README.md` を参照してください。

---

**以下は受講者が記入してください**

## 提出物

- `day10/app.py`
- `day10/README.md`
- `final/`（最終課題のスケルトン）
- `docs/`（設計メモ）

## セルフレビュー

- `self-review-checklist.md` の該当項目：
  - 基本：READMEに実行手順がある
  - 基本：実行してクラッシュしない
  - 基本：例外時に分かりやすいメッセージが出る
  - 基本：ログが最低限入っている
  - テスト項目：正常系
  - テスト項目：異常系（`--text` 不足時は argparse により終了コード 2）
  - Tool calling / エージェント課題：`final.agent.run_agent()` を呼び出す導線がある

最低限、以下を満たしていること。

- 起動手順どおりに動く
- 出力に根拠（出典）が含まれる（RAGを入れた場合）
- 失敗時の挙動が分かる（フォールバック or 明確なエラー）

## 最終課題の進捗

- できたこと：
  - `day10/app.py` が `final.agent.run_agent()` を呼び出し、戻り値の `reply` を標準出力に出すことを確認した
  - 正常系として `python3 -m day10.app --text "統合テスト"` を実行し、終了コード 0 で結果が出力されることを確認した
  - `final/agent.py` の現在の実装はスタブであり、READMEの受け入れ基準である「スタブでも可」の導線を満たしていることを確認した
  - 既存のCLI、終了コード、ログ設定は変更しなかった
- 残っていること：
  - `final.agent.run_agent()` の中身を、LangGraph、Tool calling、フォールバックなどを含む最終課題の実装に置き換える
  - 実行環境によっては `python` コマンドが未設定のため、必要に応じて `python3` または仮想環境の `python` で実行する



## 学び・理解したこと

- `day10/app.py` は最終課題の本体ではなく、CLIから最終課題を呼び出すための入口である
- `--text` に渡した文字列は、`argparse` で受け取られたあと、`final.agent.run_agent(args.text, history=[])` に渡される
- `final/agent.py` の `run_agent()` が返した `reply` を `day10/app.py` が標準出力に表示している
- 現在の `final/agent.py` はスタブ実装のため、実際のBedrock呼び出しやLangGraphの状態遷移はまだ行っていない
- READMEの受け入れ基準である「`final/` に実装したエージェント（またはスタブ）を呼び出す導線がある」は、`day10.app` を実行して `final` 由来の返答が表示されることで確認できる
- 終了コードは、正常終了が `0`、入力不備が `2`、実行失敗が `1` になるように役割が分かれている

## リサーチメモ（任意）

### 今回の課題の位置づけ
主目的は、`day10/app.py` から `final/agent.py` の `run_agent()` を呼び出し、CLIで受け取った入力を最終課題側へ渡せる状態にすること。

現時点では、`final/agent.py` は以下のようなスタブ実装になっている。

- 入力された `message` を受け取る
- `"(agent not implemented yet) You said: " + message` という仮の返答を作る
- `reply` と `meta` を辞書で返す

そのため、Bedrock、構造化出力、Tool calling、LangGraph、フォールバックはまだ実装されていない。  
ただし、`day10` から `final` を呼び出す導線はできているため、今後 `final.agent.run_agent()` の中身を本実装に差し替えれば、同じCLIから最終課題の処理を実行できる。

### 確認したコマンドと結果の要約

- `python3 -m day10.app --text "統合テスト"`：正常終了、終了コード `0`
- `python3 -m day10.app`：必須引数不足、終了コード `2`
- `python3 -m day10.app --text`：引数の値不足、終了コード `2`
- `python3 -m day10.app --text ""`：空文字入力、終了コード `2`
- `python3 -m day10.app --text "統合テスト" --unknown-option`：未知オプション、終了コード `2`
- 記号・改行を含む入力：クラッシュせず終了コード `0`
- 長文入力：クラッシュせず終了コード `0`
- 同じ入力の再実行：クラッシュせず終了コード `0`

### 次に行うこと

次の段階では、`final/agent.py` の `run_agent()` の中身をスタブから本実装に置き換える。  
具体的には、Bedrock呼び出し、構造化出力、Tool calling、LangGraphによる状態遷移、失敗時のフォールバックを順番に追加していく。その後、同じ `python3 -m day10.app --text "..."` の形で、CLIから本実装の動作を確認する。
