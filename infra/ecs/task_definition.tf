resource "aws_ecs_task_definition" "this" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  depends_on               = [aws_cloudwatch_log_group.ecs]


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
        { name = "DB_HOST", value = "${var.db_host}" },
        { name = "DB_NAME", value = "${var.db_name}" },
        { name = "DB_USER", value = "${var.db_user}" },
        { name = "DB_PASSWORD", value = "${var.db_password}" },

        # Redis
        { name = "REDIS_HOST", value = "${var.redis_host}" },
        { name = "REDIS_PORT", value = "${var.redis_port}" }
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
