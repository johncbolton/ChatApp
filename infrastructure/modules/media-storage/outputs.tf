output "media_bucket_name" {
  description = "The name of the S3 bucket for media uploads"
  value       = aws_s3_bucket.media_bucket.bucket
}

output "media_bucket_arn" {
  description = "The ARN of the S3 bucket for media uploads"
  value       = aws_s3_bucket.media_bucket.arn
}

output "media_metadata_table_name" {
  description = "The name of the DynamoDB table for media metadata"
  value       = aws_dynamodb_table.media_metadata.name
}

output "media_metadata_table_arn" {
  description = "The ARN of the DynamoDB table for media metadata"
  value       = aws_dynamodb_table.media_metadata.arn
}