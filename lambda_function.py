import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

comprehend = boto3.client("comprehend")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb") if os.environ.get("DDB_TABLE") else None

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "en")
NEGATIVE_THRESHOLD = float(os.environ.get("NEGATIVE_THRESHOLD", "0.6"))

def format_output(message_id, text, sentiment, scores):
    return {
        "messageId": message_id,
        "text": text,
        "sentiment": sentiment,
        "sentimentScore": scores,
        "languageCode": LANGUAGE_CODE,
        "triggeredNotification": False,
        "snsTopic": SNS_TOPIC_ARN or None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def publish_alert(payload, sentiment):
    if not SNS_TOPIC_ARN:
        logger.warning("SNS_TOPIC_ARN not configured. Skipping publish.")
        return False
    subject = f"Sentiment Alert: {sentiment}"
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=json.dumps(payload, indent=2)
        )
        logger.info("Published alert to SNS.")
        return True
    except ClientError as e:
        logger.error("Failed to publish SNS message: %s", e)
        return False

def store_to_dynamodb(table_name, item):
    if not dynamodb:
        logger.warning("DynamoDB not configured.")
        return False
    try:
        table = dynamodb.Table(table_name)
        table.put_item(Item=item)
        logger.info("Stored result to DynamoDB table %s", table_name)
        return True
    except ClientError as e:
        logger.error("Error storing to DynamoDB: %s", e)
        return False

def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))

    if isinstance(event.get("body"), str):
        try:
            body = json.loads(event["body"])
        except Exception:
            body = {}
    else:
        body = event

    message_id = body.get("messageId") or body.get("id") or event.get("messageId") or None
    text = body.get("message") or body.get("text") or event.get("message") or ""

    if not text:
        logger.warning("No text provided in the request.")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No 'message' text provided."})
        }

    try:
        resp = comprehend.detect_sentiment(Text=text, LanguageCode=LANGUAGE_CODE)
    except ClientError as e:
        logger.error("Comprehend failed: %s", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Comprehend detect_sentiment failed", "details": str(e)})
        }

    sentiment = resp.get("Sentiment", "UNKNOWN")
    scores = resp.get("SentimentScore", {})

    output = format_output(message_id, text, sentiment, scores)

    notify = False
    negative_score = scores.get("Negative") or 0.0
    if sentiment.upper() in ("NEGATIVE", "MIXED") and negative_score >= NEGATIVE_THRESHOLD:
        notify = True

    if notify and SNS_TOPIC_ARN:
        published = publish_alert(output, sentiment)
        output["triggeredNotification"] = bool(published)

    ddb_table = os.environ.get("DDB_TABLE")
    if ddb_table:
        item = output.copy()
        if not item.get("messageId"):
            item["messageId"] = context.aws_request_id if context else "no-id"
        store_to_dynamodb(ddb_table, item)

    return {
        "statusCode": 200,
        "body": json.dumps(output)
    }
