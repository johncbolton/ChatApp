import boto3
import os
import json
import re

def lambda_handler(event, context):
    
    region = os.environ.get('AWS_REGION')

    dynamodb = boto3.resource('dynamodb', region_name=region)
    cognito = boto3.client('cognito-idp', region_name=region)
    
    try:
        USER_PROFILE_TABLE = os.environ['USER_PROFILE_TABLE_NAME']
        COGNITO_CLIENT_ID = os.environ['COGNITO_CLIENT_ID']
        COGNITO_USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
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

    try:
        response = cognito.sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email}
            ]
        )
        
        user_sub = response['UserSub']

        table = dynamodb.Table(USER_PROFILE_TABLE)
        table.put_item(
            Item={
                'userID': user_sub,
                'username': username,
                'email': email,
                'createdAt': json.dumps(context.aws_request_id)
            }
        )

        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'User created successfully. Please check your email to confirm.',
                'userSub': user_sub
            })
        }

    except cognito.exceptions.UsernameExistsException:
        return {
            'statusCode': 409,
            'body': json.dumps({'message': 'This username already exists.'})
        }
    except cognito.exceptions.InvalidParameterException as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': f'Invalid parameter: {str(e)}'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An internal server error occurred: {str(e)}'})
        }


