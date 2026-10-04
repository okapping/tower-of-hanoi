#!/usr/bin/env sh
set -eu

# このシェルが置かれているディレクトリを基準にする
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 仮想環境へ入る
source .venv/bin/activate

# pyxapp化
pyxel package source source/main.py

# html化
pyxel app2html source.pyxapp

# ゲームパッド不要の場合
sed 's/gamepad:[[:space:]]*"enabled"/gamepad: "disabled"/g' source.html > source.html.tmp &&
mv source.html.tmp source.html

# docsへ移動
mkdir -p docs
mv source.html ./docs/index.html
mv source.pyxapp ./docs/source.pyxapp

# distのクリーンアップ
# rm -rf ./dist/*
# appファイルの作成
# pyxel app2exe ./docs/source.pyxapp