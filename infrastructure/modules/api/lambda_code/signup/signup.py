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
        
        # --- CHANGE 1: Added User Pool ID ---
        # This is required for the admin_confirm_sign_up call
        COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
        
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
    
    if len(password) < 6:
        return {
            'statusCode': 400,
            'headers': cors_headers,
            'body': json.dumps({'message': 'Password must be at least 6 characters.'})
        }

    user_sub = None
    try:
        # Use email as the username
        response = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,  
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        
        user_sub = response['UserSub']
        
        # --- CHANGE 2: Auto-confirm the user ---
        # This is the fix for your Postman tests.
        # It moves the user from UNCONFIRMED to CONFIRMED.
        print(f"User {email} created. Attempting to auto-confirm...")
        cognito.admin_confirm_sign_up(
            UserPoolId=COGNITO_USER_POOL_ID,
            Username=email
        )
        print(f"User {email} auto-confirmed.")
        # --- End of Change ---

        try:
            table = dynamodb.Table(USER_PROFILE_TABLE)
            table.put_item(
                Item={
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
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({'message': f'Invalid parameter: {str(e)}'})
            }
        
        # Catch other Cognito errors (e.g., from admin_confirm_sign_up)
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

