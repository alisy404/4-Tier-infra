resource "aws_ecs_task_definition" "this" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  depends_on = [aws_cloudwatch_log_group.ecs]


  container_definitions = jsonencode([
    {
      name      = "app"
      image     = "${var.container_image}"
      essential = true

      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "APP_ENV", value = "aws" },

        # DB (even if RDS not live yet, values must exist)
        { name = "DB_HOST", value = "dummy" },
        { name = "DB_NAME", value = "dummy" },
        { name = "DB_USER", value = "dummy" },
        { name = "DB_PASSWORD", value = "dummy" },

        # Redis
        { name = "REDIS_HOST", value = "dummy" },
        { name = "REDIS_PORT", value = "6379" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/multi-aws"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "app"
        }
      }
    }
  ])

}
