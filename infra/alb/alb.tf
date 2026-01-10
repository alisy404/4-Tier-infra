resource "aws_lb" "this" {
  name               = "${var.project_name}-alb"
  load_balancer_type = "application"
  internal           = false

  security_groups = [var.alb_sg_id]
  subnets         = var.public_subnets

  tags = {
    Name = "${var.project_name}-alb"
  }
}
