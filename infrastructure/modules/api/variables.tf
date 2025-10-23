variable "project_name" {
  type        = string
  description = "The unique project name (e.g., 'john-chatapp')."
}

variable "environment_name" {
  type        = string
  description = "The name of the environment (e.g., 'dev', 'prod')."
}

# --- Inputs from Identity Module ---
variable "cognito_user_pool_id" {
  type        = string
  description = "The ID of the Cognito User Pool."
}

variable "cognito_user_pool_arn" {
  type        = string
  description = "The ARN of the Cognito User Pool."
}

variable "cognito_client_id" {
  type        = string
  description = "The ID of the Cognito User Pool Client."
}

variable "user_profile_table_arn" {
  type        = string
  description = "The ARN of the user profile DynamoDB table."
}

variable "media_bucket_name" {
  type        = string
  description = "The name of the S3 bucket for media."
}

variable "media_metadata_table_arn" {
  type        = string
  description = "The ARN of the media metadata DynamoDB table."
}