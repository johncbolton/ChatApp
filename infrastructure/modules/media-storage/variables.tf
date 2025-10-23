variable "project_name" {
  type        = string
  description = "The unique project name (e.g., 'john-chatapp')."
}

variable "environment_name" {
  type        = string
  description = "The name of the environment (e.g., 'dev', 'prod')."
}

variable "allowed_cors_origins" {
  type        = list(string)
  description = "A list of origins (URLs) allowed to upload to the S3 bucket."
  default     = ["*"] 
}