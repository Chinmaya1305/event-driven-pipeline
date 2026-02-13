import json
import boto3
import csv
import os

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

TABLE_NAME = os.environ['DYNAMODB_TABLE']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
PROCESSED_BUCKET = os.environ['PROCESSED_BUCKET']

def lambda_handler(event, context):

    # Get file details
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    response = s3.get_object(Bucket=bucket, Key=key)
    file_content = response['Body'].read().decode('utf-8')

    total_rows = 0
    total_amount = 0

    csv_reader = csv.DictReader(file_content.splitlines())

    for row in csv_reader:
        total_rows += 1
        total_amount += float(row['amount'])

    summary = {
        "file_name": key,
        "total_rows": total_rows,
        "total_amount": total_amount
    }

    # Store in DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item=summary)

    # Save summary to processed bucket
    s3.put_object(
        Bucket=PROCESSED_BUCKET,
        Key=f"processed_{key}.json",
        Body=json.dumps(summary)
    )

    # Send notification
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject="File Processed Successfully",
        Message=json.dumps(summary)
    )

    return {
        "statusCode": 200,
        "body": json.dumps("Processing Completed")
    }

