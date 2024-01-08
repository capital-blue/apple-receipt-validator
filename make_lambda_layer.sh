#!/bin/bash

set -e

if python3 -m pip install -r requirement.txt -t pythonlibs/; then
    zip -r pythonlibs.zip pythonlibs
    rm -rf pythonlibs
else
    # 失敗した場合の処理
    echo "Failed to install dependencies."
    exit 1
fi

echo "Script executed successfully."