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

variable "aws_region" {
  type        = string
  description = "The AWS region to deploy resources to."
}

variable "project_name" {
  type        = string
  description = "The unique name for the project (e.g., 'john-chatapp')."
}

variable "media_allowed_cors_origins" {
  type        = list(string)
  description = "A list of origins allowed to make CORS requests to the media bucket."
  default     = ["*"]
}

module "identity" {
  source = "../modules/identity"

  project_name     = var.project_name
  environment_name = "dev"
}

module "media-storage" {
  source = "../modules/media-storage"

  project_name           = var.project_name
  environment_name       = "dev"
  allowed_cors_origins = var.media_allowed_cors_origins
}

module "api" {
  source = "../modules/api"

  project_name     = var.project_name
  environment_name = "dev"

  cognito_user_pool_id     = module.identity.user_pool_id
  cognito_client_id        = module.identity.user_pool_client_id
  cognito_user_pool_arn    = module.identity.user_pool_arn
  user_profile_table_arn = module.identity.user_profile_table_arn

  media_bucket_name        = module.media_storage.media_bucket_name
  media_bucket_arn         = module.media_storage.media_bucket_arn
  media_metadata_table_arn = module.media_storage.media_metadata_table_arn
}


  media_bucket_name        = module.media_storage.media_bucket_name
  media_bucket_arn         = module.media_storage.media_bucket_arn
  media_metadata_table_arn = module.media_storage.media_metadata_table_arn
}

