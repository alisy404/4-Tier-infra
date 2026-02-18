variable "project_name" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

variable "redis_sg_id" {
  type = string
}
