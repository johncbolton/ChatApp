# Amazon Cognito User Pool
resource "aws_cognito_user_pool" "user_pool" {
  # Use the project and environment name to create a unique pool name
  name = "${var.project_name}-${var.environment_name}-user-pool"

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = false
    required            = true
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  auto_verified_attributes = ["email"]

  tags = {
    Environment = var.environment_name
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Cognito User Pool Client 
resource "aws_cognito_user_pool_client" "app_client" {
  name         = "${var.project_name}-${var.environment_name}-app-client"
  user_pool_id = aws_cognito_user_pool.user_pool.id

  generate_secret = false
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]
}

# DynamoDB User Profile Table 
resource "aws_dynamodb_table" "user_profile_table" {
  name         = "${var.project_name}-${var.environment_name}-user-profiles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  tags = {
    Environment = var.environment_name
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# Output
output "cognito_app_client_id" {
  value = aws_cognito_user_pool_client.app_client.id
}

