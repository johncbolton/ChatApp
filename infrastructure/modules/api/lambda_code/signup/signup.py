import boto3
import os
import json
import re
from datetime import datetime
import hmac
import hashlib
import base64

from botocore.exceptions import ClientError

def get_secret_hash(username, client_id, client_secret):
    """Calculates the secret hash for a given user."""
    message = bytes(username + client_id, 'utf-8')
    key = bytes(client_secret, 'utf-8')
    return base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()

def lambda_handler(event, context):
    
    region = os.environ.get('AWS_REGION')

    dynamodb = boto3.resource('dynamodb', region_name=region)
    cognito = boto3.client('cognito-idp', region_name=region)
    
    try:
        USER_PROFILE_TABLE = os.environ['USER_PROFILE_TABLE_NAME']
        COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
        COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
        COGNITO_CLIENT_SECRET = os.environ['COGNITO_CLIENT_SECRET']
    except KeyError as e:
        print(f"ERROR: Missing environment variable: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Server configuration error: {e}'})
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid JSON format in request body.'})
        }

    username = body.get('username')
    email = body.get('email')
    password = body.get('password')

    if not all([username, email, password]):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Username, email, and password are required.'})
        }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Invalid email format.'})
        }
    
    if len(password) < 8:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Password must be at least 8 characters.'})
        }

    user_sub = None
    try:
        secret_hash = get_secret_hash(username, COGNITO_CLIENT_ID, os.environ['COGNITO_CLIENT_SECRET'])
        response = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            SecretHash=secret_hash,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        
        user_sub = response['UserSub']

        # This is the new, specific try/except block for DynamoDB
        try:
            table = dynamodb.Table(USER_PROFILE_TABLE)
            table.put_item(
                Item={
                    'userID': user_sub,
                    'username': username,
                    'email': email,
                    'createdAt': datetime.utcnow().isoformat()
                }
            )
        
        except ClientError as db_error:
            # This is the error your test is looking for!
            print(f"DynamoDB Error: {db_error}")
            # Here we are using 'error' as the key to match the test
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'User created in Cognito, but failed to create user profile.'})
            }

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'User created successfully. Please check your email to confirm.',
                'userSub': user_sub
            })
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'This username already exists.'})
            }
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            return {
                'statusCode': 400,
                'body': json.dumps({'message': f'Invalid parameter: {str(e)}'})
            }
        print(f"Unhandled ClientError in signup: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f"An unexpected error occurred: {e.response['Error']['Code']}"})
        }
    except Exception as e:
        # This is now a general catch-all for other unexpected errors
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An internal server error occurred: {str(e)}'})
        }


