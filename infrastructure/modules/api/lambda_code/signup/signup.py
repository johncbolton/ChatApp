import json
import boto3
import os
import uuid
import time
from botocore.exceptions import ClientError

cognito_client = boto3.client('cognito-idp')
dynamodb_client = boto3.client('dynamodb')

USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
USER_POOL_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
USER_PROFILE_TABLE = os.environ['USER_PROFILE_TABLE_NAME']

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        
        email = body.get('email')
        password = body.get('password')
        username = body.get('username')

        if not all([email, password, username]):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Email, password, and username are required.'})
            }

        # Sign up user in Cognito 
        try:
            response = cognito_client.sign_up(
                ClientId=USER_POOL_CLIENT_ID,
                Username=email,  
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    },
                    {
                        'Name': 'preferred_username',
                        'Value': username
                    }
                ]
            )
            
            cognito_user_id = response['UserSub']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException':
                return {
                    'statusCode': 409,
                    'body': json.dumps({'error': 'An account with this email already exists.'})
                }
            elif e.response['Error']['Code'] == 'InvalidPasswordException':
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': f"Invalid password: {e.response['Error']['Message']}"})
                }
            else:
                raise e

        # User profile in DynamoDB 
        user_id = cognito_user_id  
        timestamp = str(int(time.time()))

        try:
            dynamodb_client.put_item(
                TableName=USER_PROFILE_TABLE,
                Item={
                    'userId': {'S': user_id},
                    'username': {'S': username},
                    'email': {'S': email},
                    'createdAt': {'N': timestamp},
                    'friendsList': {'L': []} 
                },
                ConditionExpression='attribute_not_exists(userId)'
            )
        except ClientError as e:
            print(f"Error creating DynamoDB profile: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'User created in Cognito, but failed to create user profile.'})
            }
        
        # Success
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'User created successfully. Please check your email to verify your account.',
                'userId': user_id
            })
        }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid JSON in request body.'})
        }
    except Exception as e:
        print(f"Internal server error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
