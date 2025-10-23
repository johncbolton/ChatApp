output "user_profile_table_name" {
  description = "The name of the user profile DynamoDB table."
  value       = aws_dynamodb_table.user_profile_table.name
}

output "user_profile_table_arn" {
  description = "The ARN of the user profile DynamoDB table."
  value       = aws_dynamodb_table.user_profile_table.arn
}

output "cognito_user_pool_id" {
  description = "The ID of the Cognito User Pool."
  value       = aws_cognito_user_pool.user_pool.id
}

output "cognito_user_pool_arn" {
  description = "The ARN of the Cognito User Pool."
  value       = aws_cognito_user_pool.user_pool.arn
}

output "cognito_client_id" {
  description = "The ID of the Cognito User Pool Client."
  value       = aws_cognito_user_pool_client.app_client.id
}
