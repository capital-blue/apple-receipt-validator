#!/bin/bash

set -e

if python3 -m pip install -r requirement.txt --platform manylinux2014_x86_64 --implementation cp  --only-binary=:all: --upgrade --target python/;then
    zip -r pythonlibs.zip python
    # clean up
    rm -rf python
else
    # 失敗した場合の処理
    echo "Failed to install dependencies."
    exit 1
fi

echo "Script executed successfully."
