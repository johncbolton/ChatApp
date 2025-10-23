variable "aws_region" {
  type        = string
  description = "The AWS region to deploy resources to."
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "The unique project name (e.g., 'john-chatapp')."
}
