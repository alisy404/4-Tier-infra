module "vpc" {
  source       = "./vpc"
  project_name = var.project_name
  vpc_cidr     = var.vpc_cidr
}

module "security" {
  source       = "./security"
  project_name = var.project_name
  vpc_id       = module.vpc.vpc_id
}

module "alb" {
  source         = "./alb"
  project_name   = var.project_name
  vpc_id         = module.vpc.vpc_id
  public_subnets = module.vpc.public_subnets
  alb_sg_id      = module.security.alb_sg_id
}

module "ecs" {
  source           = "./ecs"
  project_name     = var.project_name
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnets
  ecs_sg_id        = module.security.ecs_sg_id
  target_group_arn = module.alb.target_group_arn

  # TEMP image (replace with your app image)
  container_image = "public.ecr.aws/nginx/nginx:latest"
}

module "ecr" {
  source       = "./ecr"
  project_name = var.project_name
}
