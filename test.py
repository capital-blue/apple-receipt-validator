from receipt_validator import lambda_handler

event = {}
context = {}

print("test1")
receipt_file = open('./sandboxReceipt', 'rb').read()
print(lambda_handler({"payload": receipt_file}, context))

print("test2")
receipt_file = open('./sandboxReceipt2', 'rb').read()
print(lambda_handler({"payload": receipt_file}, context))
