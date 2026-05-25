---
trigger: always_on
glob: '**/*'
description: Mandatory behavioral guidelines to reduce common LLM coding mistakes, derived from Andrej Karpathy's observations.
---

# Mandatory Behavioral Rules

## 1. Think Before Coding
- 前提条件を明示し、不確実な場合は推測せず質問する。
- 複数の解釈がある場合は、勝手に判断せず提示する。
- 不明点がある場合は立ち止まり、何が不明かを明確にして質問する。

## 2. Simplicity First
- 要求された最小限のコードを記述する。
- 未使用の抽象化や不要な「柔軟性/設定可能性」は導入しない。
- 200行で書かれたものが50行で書けるなら、シンプルに書き直す。

## 3. Surgical Changes
- 必要な箇所のみを修正し、無関係な箇所の修正や「改善」は行わない。
- 既存 of コードスタイルに合わせる。

## 4. Goal-Driven Execution
- 開発時は目標を検証可能な状態（テスト等）にし、検証を繰り返してループする。
