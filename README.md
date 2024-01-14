# Apple Receipt Validator
Appleに作成されるレシートの検証をするためのAWS Lambda用関数と外部ライブラリ

```
├── README.md
├── make_lambda_layer.sh ... 外部ライブラリのzipファイルを作成
├── receipt_validator.py ... Lambda用関数
├── requirement.txt ... 外部依存ライブラリのリスト
├── sandboxReceipt ... サンプルレシート
└── test.py ... Lamgda関数をテスト実行
```

Layerに追加する外部ライブラリのzipファイルを作成

```
// pythonlibs.zipというファイルが生成される
$ sh make_lambda_layer.sh
```

テスト実行

```
$ python test.py
```

サンプルリクエスト

```
$ curl -X POST -H "Content-Type: application/json" -d '{"payload": "base64 encoded receipt data"}' https://5zzehzkwt4.execute-api.ap-northeast-1.amazonaws.com/test/verify-apple-receipt
```
