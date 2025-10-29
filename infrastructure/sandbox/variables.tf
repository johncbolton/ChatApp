variable "environment_name" {
  type        = string
  description = "The dynamic name for the sandbox (e.g., 'pr-123' or 'feature-login')."
  # No default, this MUST be provided by the workflow.
}

variable "aws_region" {
  type        = string
  description = "The AWS region to deploy to."
}

variable "project_name" {
  type        = string
  description = "The unique project name (e.all, 'john-chatapp')."
}

variable "media_allowed_cors_origins" {
  type        = list(string)
  description = "Allowed CORS origins for the media bucket."
  default     = ["*"]
}