resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/multi-aws"
  retention_in_days = 7
}
