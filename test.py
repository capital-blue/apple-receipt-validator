from receipt_validator import lambda_handler

event = {}
context = {}

receipt_file = open('./sandboxReceipt2', 'rb').read()
print(lambda_handler({"payload": receipt_file}, context))
