output "api_invoke_url" {
  description = "The URL to invoke the deployed API Gateway stage."
  value       = aws_api_gateway_stage.api_stage.invoke_url
}
