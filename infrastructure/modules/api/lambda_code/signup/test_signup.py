import json
import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import os # Import os to use for @patch.dict
from datetime import datetime

# Import lambda_handler at the top
from signup import lambda_handler

mock_os_environ = {
    'COGNITO_USER_POOL_ID': 'test_pool_id',
    'COGNITO_CLIENT_ID': 'test_client_id',
    'COGNITO_CLIENT_SECRET': 'test_client_secret',
    'USER_PROFILE_TABLE_NAME': 'test_profile_table',
    'AWS_REGION': 'us-east-1' # Add region to prevent NoRegionError
}

mock_boto3_client = MagicMock()
mock_boto3_resource = MagicMock()

class TestSignupLambda(unittest.TestCase):

    def setUp(self):
        # Set up patchers
        self.patchers = [
            patch.dict(os.environ, mock_os_environ, clear=True),
            patch('boto3.client', return_value=mock_boto3_client),
            patch('boto3.resource', return_value=mock_boto3_resource)
        ]
        # Start patchers
        for p in self.patchers:
            p.start()

        # This mocks the cognito client
        self.cognito_client = mock_boto3_client
        
        # This mocks the dynamodb resource, table, and put_item call
        self.dynamodb_resource = mock_boto3_resource
        self.mock_table = MagicMock()
        self.dynamodb_resource.Table.return_value = self.mock_table
        
        # Reset mocks before each test
        self.cognito_client.reset_mock()
        self.dynamodb_resource.reset_mock()
        self.mock_table.reset_mock()

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_successful_signup(self):
        self.cognito_client.sign_up.return_value = {
            'UserSub': 'new-user-uuid-12345'
        }
        
        self.mock_table.put_item.return_value = {}

        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'username': 'testuser'
        }
        
        event = {'body': json.dumps(event_body)}
        
        # This is a mock context object
        mock_context = MagicMock()
        mock_context.aws_request_id = 'test-request-id'
        
        response = lambda_handler(event, mock_context)
        
        self.assertEqual(response['statusCode'], 201)
        body = json.loads(response['body'])
        # Updated message to match the one in the new signup.py
        self.assertEqual(body['message'], 'User created successfully. Please check your email to confirm.')
        self.assertEqual(body['userSub'], 'new-user-uuid-12345') # Updated key

        # Assert cognito was called correctly
        self.cognito_client.sign_up.assert_called_once_with(
            ClientId='test_client_id',
            SecretHash=unittest.mock.ANY,
            Username='testuser', # Updated to match signup.py
            Password='Password123!',
            UserAttributes=[
                {'Name': 'email', 'Value': 'test@example.com'}
            ]
        )

        # Assert DynamoDB Table resource was called
        self.dynamodb_resource.Table.assert_called_once_with('test_profile_table')
        
        # Assert put_item was called on the table object
        self.mock_table.put_item.assert_called_once()
        put_item_call_args = self.mock_table.put_item.call_args[1]
        self.assertEqual(put_item_call_args['Item']['userID'], 'new-user-uuid-12345')
        self.assertEqual(put_item_call_args['Item']['username'], 'testuser')

        # Verify the timestamp
        self.assertIn('createdAt', put_item_call_args['Item'])
        created_at_str = put_item_call_args['Item']['createdAt']
        self.assertTrue(isinstance(created_at_str, str))
        try:
            datetime.fromisoformat(created_at_str)
        except ValueError:
            self.fail("createdAt is not a valid ISO 8601 timestamp")

    def test_missing_parameters(self):
        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!'
            # 'username' is missing
        }
        
        event = {'body': json.dumps(event_body)}
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        # Updated message to match signup.py
        self.assertEqual(body['message'], 'Username, email, and password are required.')

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
        self.assertEqual(body['message'], 'This username already exists.')

    def test_invalid_password(self):
        # Test the internal password logic
        event_body = {
            'email': 'test@example.com',
            'password': 'weak', # Less than 8 chars
            'username': 'testuser'
        }
        event = {'body': json.dumps(event_body)}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Password must be at least 8 characters.')

    def test_invalid_json_body(self):
        event = {'body': 'this is not json'}
        
        response = lambda_handler(event, {})
        
        self.assertEqual(response['statusCode'], 400)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'Invalid JSON format in request body.')

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
        # Make the mock table's put_item fail
        self.mock_table.put_item.side_effect = ClientError(error_response, 'put_item')
        
        event_body = {
            'email': 'test@example.com',
            'password': 'Password123!',
            'username': 'testuser'
        }
        event = {'body': json.dumps(event_body)}

        # This is a mock context object
        mock_context = MagicMock()
        mock_context.aws_request_id = 'test-request-id'
        
        response = lambda_handler(event, mock_context)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        # This now matches the error key from the updated signup.py
        self.assertEqual(body['message'], 'User created in Cognito, but failed to create user profile.')

if __name__ == '__main__':
    unittest.main()