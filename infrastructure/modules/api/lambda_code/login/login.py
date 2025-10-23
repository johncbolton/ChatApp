import json
import os
import boto3
from botocore.exceptions import ClientError

cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')

def lambda_handler(event, context):
    
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,OPTIONS" 
    }

    if event.get('httpMethod') == 'OPTIONS':
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"message": "CORS preflight OK"})
        }

    try:
        try:
            body = json.loads(event.get('body', '{}'))
            username = body.get('username')
            password = body.get('password')
            
            if not username or not password:
                raise ValueError("Username and password are required.")
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "statusCode": 400, 
                "headers": headers,
                "body": json.dumps({"error": f"Invalid input: {str(e)}"})
            }

        response = cognito_client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )
        
        auth_result = response.get('AuthenticationResult', {})
        id_token = auth_result.get('IdToken')
        access_token = auth_result.get('AccessToken')
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "Login successful",
                "id_token": id_token,
                "access_token": access_token
            })
        }

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code')
        if error_code == 'NotAuthorizedException':
            return {
                "statusCode": 401, 
                "headers": headers,
                "body": json.dumps({"error": "Invalid username or password"})
            }
        elif error_code == 'UserNotFoundException':
            return {
                "statusCode": 404, 
                "headers": headers,
                "body": json.dumps({"error": "User not found"})
            }
        else:
            return {
                "statusCode": 400, 
                "headers": headers,
                "body": json.dumps({"error": f"Cognito error: {e.response['Error']['Message']}"})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }