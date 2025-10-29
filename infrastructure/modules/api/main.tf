# Module for the API & Compute Layer

# --- IAM Role & Base Policy ---
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-exec-role-${var.environment_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = var.environment_name
    Project     = var.project_name
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# --- Custom IAM Policy for App Permissions ---
resource "aws_iam_policy" "lambda_app_permissions" {
  name        = "${var.project_name}-lambda-permissions-${var.environment_name}"
  description = "Permissions for the chatapp Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Permissions for Login (cognito:InitiateAuth) and Signup (cognito:SignUp)
        Effect = "Allow"
        Action = [
          "cognito-idp:InitiateAuth",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:SignUp"
        ]
        Resource = [
          var.cognito_user_pool_arn
        ]
      },
      {
        # Permission for get-upload-url (s3:PutObject)
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${var.media_bucket_arn}/*"
        ]
      },
      {
        # Permission for Signup to write to the user profile table
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = [
          var.user_profile_table_arn
        ]
      },
      {
        # Read-only permissions for other functions (e.g., login, get-media)
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = [
          var.user_profile_table_arn,
          var.media_metadata_table_arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_app_permissions" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_app_permissions.arn
}


# --- API Gateway REST API ---
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.project_name}-api-${var.environment_name}"
  description = "API for the ${var.project_name} application"

  binary_media_types = ["image/jpeg", "image/png", "video/mp4"]
}

# --- Lambda: login ---
data "archive_file" "login_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_code/login"
  output_path = "${path.module}/lambda_code/login.zip"
}

resource "aws_lambda_function" "login" {
  function_name    = "${var.project_name}-login-${var.environment_name}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "login.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.login_lambda_zip.output_path
  source_code_hash = data.archive_file.login_lambda_zip.output_base64sha256

  environment {
    variables = {
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
      COGNITO_CLIENT_ID    = var.cognito_client_id
    }
  }
}

# --- Lambda: signup [NEW] ---
data "archive_file" "signup_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_code/signup"
  output_path = "${path.module}/lambda_code/signup.zip"
}

resource "aws_lambda_function" "signup" {
  function_name    = "${var.project_name}-signup-${var.environment_name}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "signup.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.signup_lambda_zip.output_path
  source_code_hash = data.archive_file.signup_lambda_zip.output_base64sha256

  environment {
    variables = {
      COGNITO_USER_POOL_ID    = var.cognito_user_pool_id
      COGNITO_CLIENT_ID       = var.cognito_client_id
      # <--- FIX: Renamed this key to match your Python code (added "_NAME")
      USER_PROFILE_TABLE_NAME = var.user_profile_table_name
    }
  }
}

# --- Lambda: get-upload-url ---
data "archive_file" "upload_url_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_code/upload_url"
  output_path = "${path.module}/lambda_code/upload_url.zip"
}

resource "aws_lambda_function" "get_upload_url" {
  function_name    = "${var.project_name}-get-upload-url-${var.environment_name}"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "upload_url.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.upload_url_lambda_zip.output_path
  source_code_hash = data.archive_file.upload_url_lambda_zip.output_base64sha256

  environment {
    variables = {
      MEDIA_BUCKET_NAME         = var.media_bucket_name
      MEDIA_METADATA_TABLE_NAME = var.media_metadata_table_name
    }
  }
}

# --- API Gateway Wiring: /login ---
resource "aws_api_gateway_resource" "login" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "login"
}

resource "aws_api_gateway_method" "login" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.login.invoke_arn
}

# Give API Gateway permission to invoke the signup Lambda
resource "aws_lambda_permission" "api_gateway_invoke_signup" {
  statement_id  = "AllowAPIGatewayInvokeSignup"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signup.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}

# Give API Gateway permission to invoke the login Lambda
resource "aws_lambda_permission" "api_gateway_invoke_login" {
  statement_id  = "AllowAPIGatewayInvokeLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.login.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}

# <--- FIX: Added missing permission for the get-upload-url Lambda
# Give API Gateway permission to invoke the get_upload_url Lambda
resource "aws_lambda_permission" "api_gateway_invoke_get_upload_url" {
  statement_id  = "AllowAPIGatewayInvokeGetUploadUrl"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_upload_url.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*/*"
}

# --- API Gateway Wiring: /signup [NEW] ---
resource "aws_api_gateway_resource" "signup" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "signup"
}

resource "aws_api_gateway_method" "signup" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.signup.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "signup" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.signup.id
  http_method = aws_api_gateway_method.signup.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.signup.invoke_arn
}

# --- API Gateway Wiring: /get-upload-url ---
resource "aws_api_gateway_resource" "get_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "get-upload-url"
}

resource "aws_api_gateway_method" "get_upload_url" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.get_upload_url.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_upload_url" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.get_upload_url.id
  http_method = aws_api_gateway_method.get_upload_url.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.get_upload_url.invoke_arn
}


# --- Deploy the API ---
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  # <--- FIX: Changed this trigger to timestamp()
  # This forces a new deployment every time you run 'terraform apply',
  # which prevents 404 errors from stale deployments.
  triggers = {
    redeployment = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.environment_name # Stage name will be 'dev', 'prod', etc.
}
