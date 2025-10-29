output "user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.id
}

output "user_pool_client_id" {
  description = "The ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.app_client.id
}

output "user_pool_client_secret" {
  description = "The secret of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.app_client.client_secret
  sensitive   = true
}

output "user_pool_arn" {
  description = "The ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.user_pool.arn
}

output "user_profile_table_name" {
  description = "The name of the DynamoDB table for user profiles"
  value       = aws_dynamodb_table.user_profile_table.name
}

output "user_profile_table_arn" {
  description = "The ARN of the DynamoDB table for user profiles"
  value       = aws_dynamodb_table.user_profile_table.arn
}
