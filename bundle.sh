#!/usr/bin/env bash
set -e

mkdir -p bin
mkdir -p tmp/build

rm -rf tmp/build/* bin/* Magus.spec || true

pyinstaller client/__main__.py \
  --onefile \
  --noconsole \
  --paths=common \
  --add-data "assets:assets" \
  --name "Magus" \
  --distpath bin \
  --workpath tmp/build \
  --collect-all client \
  --collect-all common \
  --clean

echo "Build complete: bin/Magus"