# Sentiment Analysis AWS

This repository contains a serverless AI-based sentiment analysis project using **AWS Lambda**, **Amazon Comprehend**, and **Amazon SNS**.

## Files
- `lambda_function.py` - Main Lambda handler that calls Comprehend and publishes to SNS.
- `sns_publisher.py` - Simple SNS publish helper.
- `template.yaml` - AWS SAM template to deploy Lambda and SNS topic.
- `requirements.txt` - Python dependencies.
- `test_event.json` - Sample event for testing locally.
- `.gitignore` - Files to ignore in git.
- `config_example.json` - Example configuration for local testing.

## Deployment (using AWS SAM)
1. Install and configure AWS CLI and AWS SAM.
2. Build and deploy:
```bash
sam build
sam deploy --guided
```
3. After deployment, set an email subscription for the SNS topic and confirm it.

## Usage
Send a POST request to the API Gateway endpoint (or invoke Lambda directly) with JSON body:
```json
{"messageId":"m1","message":"This is awful service."}
```

The Lambda function will call Amazon Comprehend, analyze sentiment, and if negative, publish an alert to the configured SNS topic.

