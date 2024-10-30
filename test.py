import json
import zipfile
from io import BytesIO

import boto3
from moto import mock_aws


def test_lambda():
    with mock_aws():
        role = _get_mock_role()

        lambda_client = boto3.client("lambda", region_name="eu-west-1")

        fn = lambda_client.create_function(
            FunctionName="TestLambdaFunction",
            Runtime="python3.10",
            Role=role["Role"]["Arn"],
            Handler="handler.lambda_handler",
            Code={"ZipFile": _make_lambda_zip()},
        )

        response = lambda_client.invoke(
            FunctionName=fn["FunctionName"],
            Payload=json.dumps({}),
        )

        payload = json.loads(response["Payload"].read().decode())
        assert payload == {"statusCode": 200, "body": "Hello from Lambda!"}

        logs_client = boto3.client("logs", region_name="eu-west-1")
        log_streams = logs_client.describe_log_streams(
            logGroupName=f"/aws/lambda/{fn['FunctionName']}"
        ).get("logStreams")

        log_events = logs_client.get_log_events(
            logGroupName=f"/aws/lambda/{fn['FunctionName']}",
            logStreamName=log_streams[0]["logStreamName"],
        ).get("events")

        assert len([e for e in log_events if e["message"] == "log message"]) == 1


def _make_lambda_zip():
    stream = BytesIO()
    zip_ = zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED)
    with open("./handler.py", "r") as f:
        zip_.writestr("handler.py", f.read())
    zip_.close()
    stream.seek(0)

    return stream.read()


def _get_mock_role():
    iam_client = boto3.client("iam", region_name="eu-west-1")
    return iam_client.create_role(
        RoleName="test-iam-role",
        AssumeRolePolicyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ],
            }
        ),
    )
