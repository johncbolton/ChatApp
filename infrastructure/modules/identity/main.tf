resource "aws_cognito_user_pool" "user_pool" {
  name = "${var.project_name}-${var.environment_name}-user-pool"

  username_attributes = ["email"]

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = false
    required            = true

    # --- ADDED ---
    # This is required by Terraform when defining a string attribute
    # to avoid plan diffs.
    string_attribute_constraints {
      min_length = 1
      max_length = 2048
    }
  }

  # --- CHANGE ---
  # Weakened password policy to be as permissive as possible
  password_policy {
    minimum_length    = 6 # This is the minimum value Cognito will accept
    require_lowercase = false
    require_numbers   = false
    require_symbols   = false
    require_uppercase = false
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


