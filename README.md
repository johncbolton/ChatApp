# ChatApp

Chat App Project (Public Template)

Infrastructure Setup

The infrastructure is managed by Terraform and deployed via GitHub Actions.

Required GitHub Setup

To use this template, you must configure the following in your repository's settings (Settings > Secrets and variables > Actions):

1. Repository Variables

These are non-secret values used to configure the deployment:

AWS_ACCOUNT_ID: Your 12-digit AWS Account ID.

AWS_DEV_ROLE_NAME: The name of the IAM Role for the dev environment.

AWS_REGION: The AWS region for deployments 

PROJECT_NAME: Your unique project name 

2. Repository Secrets

These are sensitive values that are encrypted:

DEV_TF_STATE_BUCKET: The name of the S3 bucket for the dev state file.

DEV_TF_LOCK_TABLE: The name of the DynamoDB table for the dev state lock.


Required AWS Setup (One-Time)

You must create the state buckets, lock tables, and the IAM Role for the GitHub Action to use.

Create State Backends: Manually create the S3 buckets and DynamoDB tables for each environment (dev, uat, prod). See the setup guide.

Create IAM Role: Create an IAM OIDC Provider and an IAM Role for GitHub Actions to assume. This role must have permissions to manage your AWS resources. The name of this role must match the AWS_DEV_ROLE_NAME variable.

## Workflows

This project uses GitHub Actions to automate CI/CD. The workflows are defined in the `.github/workflows` directory.

- **`blink-dev-infra.yml`**: A manually triggered workflow to apply or destroy the `dev` infrastructure.
- **`deploy-dev.yml`**: Deploys the `dev` environment when changes are pushed to the `main` branch.
- **`drift-correction.yml`**: A manually triggered workflow to detect and correct Terraform state drift for the `dev` environment.
- **`force-unlock-dev.yml`**: A manually triggered workflow to force unlock the Terraform state for the `dev` environment.
- **`lint-and-scan.yml`**: Lints and scans the Terraform code on every push.
- **`python-tests.yml`**: Runs Python tests on every push to `main` or `dev`, and on pull requests to `main` or `dev`.
- **`sandbox-create.yml`**: Creates a temporary sandbox environment for each pull request.

## Project Structure

- **`infrastructure/`**: Contains all the Terraform code for the project.
- **`postman/`**: Contains the Postman collection for testing the API.

## Testing

This project uses `pytest` for Python tests.

### Running the tests

1. **Install dependencies:**
   ```bash
   pip install pytest boto3 botocore
   ```

2. **Run the tests:**
   ```bash
   pytest
   ```