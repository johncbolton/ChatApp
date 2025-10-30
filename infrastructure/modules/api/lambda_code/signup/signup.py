import boto3
import os
import json
import re
import datetime # Added for timestamps

from botocore.exceptions import ClientError

# --- CORS Headers ---
# Define headers here to be reused in all responses
cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'OPTIONS,POST'
}

def lambda_handler(event, context):
    
    region = os.environ.get('AWS_REGION')

    dynamodb = boto3.resource('dynamodb', region_name=region)
    cognito = boto3.client('cognito-idp', region_name=region)
    
    try:
        USER_PROFILE_TABLE = os.environ['USER_PROFILE_TABLE_NAME']
        COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
        # We don't need COGNITO_USER_POOL_ID for sign_up
    except KeyError as e:
        print(f"ERROR: Missing environment variable: {e}")
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': f'Server configuration error: {e}'})
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Invalid JSON format in request body.'})
        }

    # --- FIX 1: Remove 'username' ---
    # We only need email and password
    email = body.get('email')
    password = body.get('password')

    if not all([email, password]):
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Email and password are required.'})
        }

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Invalid email format.'})
        }
    
    # --- FIX 2: Match password policy from Terraform ---
    if len(password) < 6:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Password must be at least 6 characters.'})
        }

    user_sub = None
    try:
        # --- FIX 3: Pass 'email' as the 'Username' parameter ---
        response = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,  # Use email as the username
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        
        user_sub = response['UserSub']

        try:
            table = dynamodb.Table(USER_PROFILE_TABLE)
            table.put_item(
                Item={
                    # --- FIX 4: Match 'userId' hash_key from Terraform ---
                    'userId': user_sub, 
                    'email': email,
                    'createdAt': datetime.datetime.utcnow().isoformat()
                }
            )
        
        except ClientError as db_error:
            print(f"DynamoDB Error: {db_error}")
            # User is created in Cognito, but profile failed. This is a 500 state.
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({'error': 'User created in Cognito, but failed to create user profile.'})
            }

        # --- FIX 5: Return 'id' to match Postman test ---
        return {
            'statusCode': 201,
            'headers': cors_headers,
            'body': json.dumps({
                'id': user_sub
            })
        }

    except ClientError as e:
        if e.response['Error']['Code'] == 'UsernameExistsException':
            return {
                'statusCode': 409, # 409 Conflict is more specific
                'headers': cors_headers,
                'body': json.dumps({'message': 'This email already exists.'})
            }
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # This is the 400 error you were getting before
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Invalid parameter: {str(e)}'})
            }
        
        # Catch other Cognito errors
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': f'Cognito error: {str(e)}'})
        }
        
    except Exception as e:
        # This is a general catch-all for other unexpected errors
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({'message': f'An internal server error occurred: {str(e)}'})
        }

