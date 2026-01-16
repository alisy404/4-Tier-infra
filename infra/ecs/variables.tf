variable "project_name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

variable "ecs_sg_id" {
  type = string
}

variable "target_group_arn" {
  type = string
}

variable "container_image" {
  type = string
}

variable "container_port" {
  type    = number
  default = 80
}

variable "ecr_repo_url" {
  description = "ECR repository URL for FastAPI image"
  type        = string
}
