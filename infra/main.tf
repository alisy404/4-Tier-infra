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

