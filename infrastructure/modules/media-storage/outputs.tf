output "media_bucket_name" {
  description = "The name of the S3 bucket created for media storage."
  value       = aws_s3_bucket.media_bucket.id
}

output "media_metadata_table_name" {
  description = "The name of the DynamoDB table for media metadata."
  value       = aws_dynamodb_table.media_metadata.name
}
