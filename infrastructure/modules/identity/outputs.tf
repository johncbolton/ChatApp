output "user_pool_id" {
  description = "The ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_client_id" {
  description = "The ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.main.id
}

output "user_pool_arn" {
  description = "The ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "user_profile_table_name" {
  description = "The name of the DynamoDB table for user profiles"
  value       = aws_dynamodb_table.user_profiles.name
}

output "user_profile_table_arn" {
  description = "The ARN of the DynamoDB table for user profiles"
  value       = aws_dynamodb_table.user_profiles.arn
}
