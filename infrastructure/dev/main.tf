terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    region  = "us-east-1"
    encrypt = true
    key     = "terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
}

# The variable blocks were removed from this file.
# They should exist in your "dev/variables.tf" file.

module "identity" {
  source = "../modules/identity"

  project_name     = var.project_name
  environment_name = "dev"
}

module "media_storage" {
  source = "../modules/media-storage"

  project_name           = var.project_name
  environment_name       = "dev"
  allowed_cors_origins = var.media_allowed_cors_origins
}

resource "aws_api_gateway_resource" "login" {
  rest_api_id = module.api.api_gateway_rest_api_id
  parent_id   = module.api.api_gateway_rest_api_root_resource_id
  path_part   = "login"
}

resource "aws_api_gateway_method" "login" {
  rest_api_id   = module.api.api_gateway_rest_api_id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login" {
  rest_api_id = module.api.api_gateway_rest_api_id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.api.login_lambda_invoke_arn
}

resource "aws_api_gateway_resource" "get_upload_url" {
  rest_api_id = module.api.api_gateway_rest_api_id
  parent_id   = module.api.api_gateway_rest_api_root_resource_id
  path_part   = "get-upload-url"
}

resource "aws_api_gateway_method" "get_upload_url" {
  rest_api_id   = module.api.api_gateway_rest_api_id
  resource_id   = aws_api_gateway_resource.get_upload_url.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_upload_url" {
  rest_api_id = module.api.api_gateway_rest_api_id
  resource_id = aws_api_gateway_resource.get_upload_url.id
  http_method = aws_api_gateway_method.get_upload_url.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = module.api.get_upload_url_lambda_invoke_arn
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = module.api.api_gateway_rest_api_id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_integration.login.id,
      aws_api_gateway_integration.get_upload_url.id
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

module "api" {
  source = "../modules/api"

  project_name     = var.project_name
  environment_name = "dev"

  cognito_user_pool_id     = module.identity.cognito_user_pool_id
  cognito_client_id        = module.identity.cognito_client_id
  cognito_user_pool_arn    = module.identity.cognito_user_pool_arn
  user_profile_table_arn = module.identity.user_profile_table_arn

  media_bucket_name        = module.media_storage.media_bucket_name
  media_metadata_table_arn = module.media_storage.media_metadata_table_arn
  aws_region                 = var.aws_region
  api_gateway_deployment_id  = aws_api_gateway_deployment.api_deployment.id
}
