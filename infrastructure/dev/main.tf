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
}
