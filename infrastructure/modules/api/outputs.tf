output "api_gateway_rest_api_id" {
  description = "The ID of the API Gateway REST API."
  value       = aws_api_gateway_rest_api.api.id
}

output "api_gateway_rest_api_root_resource_id" {
  description = "The ID of the API Gateway REST API's root resource."
  value       = aws_api_gateway_rest_api.api.root_resource_id
}

output "login_lambda_invoke_arn" {
  description = "The Invoke ARN of the login Lambda function."
  value       = aws_lambda_function.login.invoke_arn
}

output "get_upload_url_lambda_invoke_arn" {
  description = "The Invoke ARN of the get_upload_url Lambda function."
  value       = aws_lambda_function.get_upload_url.invoke_arn
}

output "signup_lambda_invoke_arn" {
  description = "The Invoke ARN of the signup Lambda function."
  value       = aws_lambda_function.signup.invoke_arn
}

output "api_invoke_url" {
  description = "The invoke URL for the API Gateway."
  value       = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment_name}"
}

output "api_gateway_deployment_id" {
  description = "The ID of the API Gateway deployment."
  value       = aws_api_gateway_deployment.api_deployment.id
}
