def lambda_handler(event, context):
    print("log message")

    return {"statusCode": 200, "body": "Hello from Lambda!"}
