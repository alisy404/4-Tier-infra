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
  source = "./ecs"

  project_name     = var.project_name
  vpc_id           = module.vpc.vpc_id
  alb_listener_arn = module.alb.listener_arn

  private_subnets = module.vpc.private_subnets
  ecs_sg_id       = module.security.ecs_sg_id

  target_group_arn = module.alb.target_group_arn
  ecr_repo_url     = module.ecr.repository_url
  container_image  = "${module.ecr.repository_url}:latest"

  # DB
  db_host     = module.rds.db_endpoint
  db_name     = module.rds.db_name
  db_user     = var.db_username
  db_password = var.db_password

  # Redis
  redis_host = module.elasticache.redis_endpoint
  redis_port = module.elasticache.redis_port
}


module "ecr" {
  source       = "./ecr"
  project_name = var.project_name
}

module "rds" {
  source          = "./rds"
  project_name    = var.project_name
  private_subnets = module.vpc.private_subnets
  rds_sg_id       = module.security.rds_sg_id
  db_name         = var.db_name
  db_username     = var.db_username
  db_password     = var.db_password
}

module "elasticache" {
  source          = "./elasticache"
  project_name    = var.project_name
  private_subnets = module.vpc.private_subnets
  redis_sg_id     = module.security.redis_sg_id
}
