# logs.tf

# Set up CloudWatch group and log stream and retain logs for 30 days
resource "aws_cloudwatch_log_group" "burr_log_group" {
  name              = "/ecs/burr-app"
  retention_in_days = 30

  tags = {
    Name = "burr-log-group"
  }
}

resource "aws_cloudwatch_log_stream" "burr_log_stream" {
  name           = "burr-log-stream"
  log_group_name = aws_cloudwatch_log_group.burr_log_group.name
}
