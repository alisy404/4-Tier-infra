##### Multi-AWS FastAPI Infrastructure Project

# Project Description

+  This project implements a production-grade AWS infrastructure to deploy a containerized FastAPI application
+  The focus is on real-world DevOps infrastructure, networking, security, and container orchestration
+  Infrastructure is built fully using Terraform with no default AWS resources
+  The project is designed to be cost-optimized, modular, and scalable

---------------------------------------------------------------------------------------------------------------------------------------

# Current Infrastructure Tier:

+ 4-Tier Architecture
  +  Presentation Tier → Application Load Balancer (ALB)
  +  Application Tier → ECS Fargate (FastAPI containers)
  +  Data Tier → RDS (PostgreSQL) + ElastiCache (Redis)
  +  Infrastructure Tier → VPC, subnets, routing, security

--------------------------------------------------------------------------------------------------------------------

## Architecture Overview:

1. Users access the application using the ALB DNS
2. ALB listens on port 80
3. Traffic is forwarded to ECS tasks via target groups
4. FastAPI runs inside Docker containers
5. Containers are pulled from Amazon ECR
6. ECS tasks run inside private subnets
7. Application checks Redis (ElastiCache) for cached data first
8. On cache miss, application queries PostgreSQL (RDS) and caches the result
9. NAT Gateway allows outbound internet access
10. VPC provides complete network isolation

--------------------------------------------------------------------------------------------------------------------

## AWS Services Used

1.  Amazon VPC
2.  Public and Private Subnets (Multi-AZ)
3.  Internet Gateway
4.  NAT Gateway
5.  Application Load Balancer
6.  Target Groups and Health Checks
7.  Amazon ECS (Fargate)
8.  Amazon ECR
9.  Amazon RDS (PostgreSQL)
10. Amazon ElastiCache (Redis)
11. IAM Roles and Policies
12. CloudWatch Logs
13. Security Groups

---------------------------------------------------------------------------------------------------------------------------------------

## Design Principles

+ **Terraform (Infrastructure as Code)**
+ **Networking Design**
  + Custom VPC with CIDR 10.0.0.0/16
  + 2 Public Subnets for ALB and NAT Gateway
  + 2 Private Subnets for ECS tasks
  + Explicit route tables for public and private routing
  + ECS tasks have no public IPs
  + All outbound traffic from private subnets goes through NAT Gateway

+ **Security Design**
  + ALB Security Group allows inbound HTTP traffic on port 80 from the internet
  + ECS Security Group allows inbound traffic only from ALB security group
  + RDS Security Group allows inbound traffic only from ECS security group on port 5432
  + Redis Security Group allows inbound traffic only from ECS security group on port 6379
  + No direct internet access to ECS tasks
  + IAM execution role scoped only for ECS and CloudWatch logs

+ **Application Design**
  + FastAPI application containerized using Docker
  + Application listens on port 80
  + Health check endpoint exposed at /health
  + Docker image stored in Amazon ECR
  + ECS task definition references ECR image

+ **Data Design**
  + RDS PostgreSQL (db.t3.micro) as primary database
  + ElastiCache Redis (cache.t3.micro) as caching layer
  + Redis-first lookup with database fallback on cache miss
  + Cached responses expire after 60 seconds (TTL)
  + Both services deployed in private subnets only

+ **Load Balancer Configuration**
  + Application Load Balancer (internet-facing)
  + Listener on port 80
  + Target group type set to ip
  + Health check path set to /health
  + Only healthy ECS tasks receive traffic

+ **Terraform Design**
  + Modular Terraform structure
  + No AWS default resources used
  + All resources explicitly defined
  + Safe to destroy and recreate to minimize billing
  + Backend can be extended to S3 + DynamoDB later

---------------------------------------------------------------------------------------------------------------------------------------

## How the System Works

1. Client sends HTTP request to ALB DNS
2. ALB listener receives request on port 80
3. Request forwarded to healthy ECS task
4. FastAPI checks Redis cache for requested data
5. On cache hit → returns cached response immediately
6. On cache miss → queries PostgreSQL (RDS) for data
7. Result is cached in Redis with 60s TTL
8. Response returned back to client via ALB

---------------------------------------------------------------------------------------------------------------------------------------

## How to Run Locally (Application Only)

Build Docker image:
```bash
docker build -t multi-aws-fastapi .
```

Run container locally:
```bash
docker run -p 8080:80 multi-aws-fastapi
```

Access application:
```
http://localhost:8080
```

## How to Deploy on AWS

Authenticate Docker with ECR:
```bash
aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

Build and tag Docker image:
```bash
docker build -t multi-aws-fastapi .
docker tag multi-aws-fastapi:latest <ecr-repo-url>:latest
```

Push image to ECR:
```bash
docker push <ecr-repo-url>:latest
```

Initialize Terraform:
```bash
terraform init
```

Apply infrastructure:
```bash
terraform apply
```

Access application using ALB DNS from Terraform output.

---------------------------------------------------------------------------------------------------------------------------------------

## Project Outcomes

+ Fully working 4-Tier FastAPI application on AWS
+ High availability using multi-AZ subnets
+ Secure container deployment using ECS Fargate
+ Proper ALB health checks and traffic routing
+ Database persistence with PostgreSQL (RDS)
+ Redis caching layer for improved performance
+ Production-style networking and security
+ Resume-ready DevOps project

## Current Status

+ Infrastructure successfully deployed
+ ECS tasks running and healthy
+ ALB target group showing healthy targets
+ Application reachable via ALB DNS
+ Logs available in CloudWatch

---------------------------------------------------------------------------------------------------------------------------------------

#   --THANK-YOU--