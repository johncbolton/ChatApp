# Media Storage layer


# S3 Bucket for Media
resource "aws_s3_bucket" "media_bucket" {
  bucket = "${var.project_name}-media-${var.environment_name}"

  tags = {
    Name        = "${var.project_name}-media-bucket"
    Environment = var.environment_name
  }
}

#S3 Security
resource "aws_s3_bucket_public_access_block" "media_bucket_access" {
  bucket = aws_s3_bucket.media_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "media_bucket_encryption" {
  bucket = aws_s3_bucket.media_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# versioning 
resource "aws_s3_bucket_versioning" "media_bucket_versioning" {
  bucket = aws_s3_bucket.media_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Cross-Origin Resource Sharing
resource "aws_s3_bucket_cors_configuration" "media_bucket_cors" {
  bucket = aws_s3_bucket.media_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = var.allowed_cors_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_dynamodb_table" "media_metadata" {
  name = "${var.project_name}-media-metadata-${var.environment_name}"

  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "mediaID"
  range_key    = "userID"

  attribute {
    name = "mediaID"
    type = "S"
  }

  attribute {
    name = "userID"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-media-metadata"
    Environment = var.environment_name
  }
}
