resource "random_id" "ecr_suffix" {
  byte_length = 4
}

resource "aws_ecr_repository" "app" {
  name = "${var.project_name}-app-${random_id.ecr_suffix.hex}"

  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-ecr"
  }
}
