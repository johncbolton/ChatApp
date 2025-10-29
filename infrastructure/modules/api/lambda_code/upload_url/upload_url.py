import json
import os
import boto3
from botocore.exceptions import ClientError
import uuid

s3_client = boto3.client('s3')

MEDIA_BUCKET_NAME = os.environ.get('MEDIA_BUCKET_NAME')

def lambda_handler(event, context):
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,OPTIONS"
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "CORS preflight OK"})
        }
    if not MEDIA_BUCKET_NAME:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "MEDIA_BUCKET_NAME environment variable is not set."})
        }

    object_key = f"uploads/{uuid.uuid4()}"
    try:
        # Generate a presigned S3 POST URL
        response = s3_client.generate_presigned_post(
            Bucket=MEDIA_BUCKET_NAME,
            Key=object_key,
            Fields={"Content-Type": "image/jpeg"},  # Example: Restrict to JPEGs
            Conditions=[
                {"Content-Type": "image/jpeg"},
                ["content-length-range", 100, 5000000] # 100 bytes to 5 MB
            ],
            ExpiresIn=3600  # URL expires in 1 hour
        )
    except ClientError as e:
        # Log the error and return a generic error message
        print(f"Error generating presigned URL: {e}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Could not generate an upload URL."})
        }

    return {
        "statusCode": 200,
        "headers": headers,
        "body": json.dumps(response)
    }
