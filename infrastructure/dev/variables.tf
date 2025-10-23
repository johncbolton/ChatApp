variable "media_allowed_cors_origins" {
  type        = list(string)
  description = "Allowed CORS origins for the media bucket."
  default     = []
}

variable "aws_region" {
  type        = string
  description = "The AWS region."
}

variable "project_name" {
  type        = string
  description = "The unique project name (e.g., 'john-chatapp')."
}
