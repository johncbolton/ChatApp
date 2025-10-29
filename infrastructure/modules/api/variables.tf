variable "project_name" {
  description = "The name of the project"
  type        = string
}

variable "environment_name" {
  description = "The name of the environment (e.g., dev, prod)"
  type        = string
}

variable "aws_region" {
  description = "The AWS region for the API Gateway."
  type        = string
}

# --- Inputs from 'identity' module ---
variable "cognito_user_pool_id" {
  description = "The ID of the Cognito User Pool"
  type        = string
}

variable "cognito_client_id" {
  description = "The ID of the Cognito User Pool Client"
  type        = string
}

variable "cognito_client_secret" {
  description = "The secret of the Cognito User Pool Client"
  type        = string
  sensitive   = true
}

variable "cognito_user_pool_arn" {
  description = "The ARN of the Cognito User Pool"
  type        = string
}

variable "user_profile_table_name" {
  description = "The name of the DynamoDB table for user profiles"
  type        = string
}

variable "user_profile_table_arn" {
  description = "The ARN of the DynamoDB table for user profiles"
  type        = string
}

# --- Inputs from 'media-storage' module ---
variable "media_bucket_name" {
  description = "The name of the S3 bucket for media uploads"
  type        = string
}

variable "media_bucket_arn" {
  description = "The ARN of the S3 bucket for media uploads"
  type        = string
}

variable "media_metadata_table_arn" {
  description = "The ARN of the DynamoDB table for media metadata"
  type        = string
}

variable "media_metadata_table_name" {
  description = "The name of the DynamoDB table for media metadata"
  type        = string
}