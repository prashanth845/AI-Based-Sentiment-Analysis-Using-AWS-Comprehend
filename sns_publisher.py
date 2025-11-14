import os
import json
import boto3

sns = boto3.client("sns")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

def publish(message, subject="Sentiment Alert"):
    if not SNS_TOPIC_ARN:
        raise ValueError("SNS_TOPIC_ARN not configured")
    return sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
