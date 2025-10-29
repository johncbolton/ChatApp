import json
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError

mock_os_environ = {
    'COGNITO_USER_POOL_ID': 'test_pool_id',
    'COGNITO_CLIENT_ID': 'test_client_id',
    'USER_PROFILE_TABLE': 'test_profile_table'
}

mock_boto3 = MagicMock()

with patch.dict('os.environ', mock_os_environ):
    with patch('boto3.client', return_value=mock_boto3):
        from signup import lambda_handler

class TestSignupLambda(unittest.TestCase):

    def setUp(self):
        self.cognito_client = mock_boto3
        self.dynamodb_client = mock_boto3
        
        self.cognito_client.reset_mock()
        self.dynamodb_client.reset_mock()

    def test_successful_signup(self):
        self.cognito_client.sign_up.return_value = {
            'UserSub': 'new-user-uuid-12345'
        }
        
        self.dynamodb_client.put_item.return_value = {}

        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'username': 'testuser'
        }
        
        event = {'body': json.dumps(event_body)}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 201)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'User created successfully. Please check your email to verify your account.')
        self.assertEqual(body['userId'], 'new-user-uuid-12345')

        self.cognito_client.sign_up.assert_called_once_with(
            ClientId='test_client_id',
            Username='test@example.com',
            Password='Password123!',
            UserAttributes=[
                {'Name': 'email', 'Value': 'test@example.com'},
                {'Name': 'preferred_username', 'Value': 'testuser'}
            ]
        )

        self.dynamodb_client.put_item.assert_called_once()
        put_item_call_args = self.dynamodb_client.put_item.call_args[1]
        self.assertEqual(put_item_call_args['TableName'], 'test_profile_table')
        self.assertEqual(put_item_call_args['Item']['userId']['S'], 'new-user-uuid-12345')
        self.assertEqual(put_item_call_args['Item']['username']['S'], 'testuser')

    def test_missing_parameters(self):
        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!'
        }
        
        event = {'body': json.dumps(event_body)}
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Email, password, and username are required.')

    def test_username_exists(self):
        error_response = {
            'Error': {
                'Code': 'UsernameExistsException',
                'Message': 'User already exists'
            }
        }
        self.cognito_client.sign_up.side_effect = ClientError(error_response, 'sign_up')

        event_body = {
            'email': 'existing@example.com',
            'password': 'Password123!',
            'username': 'testuser'
        }
        event = {'body': json.dumps(event_body)}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 409)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'An account with this email already exists.')

    def test_invalid_password(self):
        error_response = {
            'Error': {
                'Code': 'InvalidPasswordException',
                'Message': 'Password did not conform with policy'
            }
        }
        self.cognito_client.sign_up.side_effect = ClientError(error_response, 'sign_up')

        event_body = {
            'email': 'test@example.com',
            'password': 'weak',
            'username': 'testuser'
        }
        event = {'body': json.dumps(event_body)}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertIn('Invalid password', body['error'])

    def test_invalid_json_body(self):
        event = {'body': 'this is not json'}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Invalid JSON in request body.')

    def test_dynamodb_put_fails(self):
        self.cognito_client.sign_up.return_value = {
            'UserSub': 'new-user-uuid-12345'
        }
        
        error_response = {
            'Error': {
                'Code': 'ProvisionedThroughputExceededException',
                'Message': 'Rate limit exceeded'
            }
        }
        self.dynamodb_client.put_item.side_effect = ClientError(error_response, 'put_item')
        
        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'username': 'testuser'
        }
        event = {'body': json.dumps(event_body)}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'User created in Cognito, but failed to create user profile.')

if __name__ == '__main__':
    unittest.main()
