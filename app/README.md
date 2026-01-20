##### Multi-AWS FastAPI Infrastructure Project

# Project Description

+  This project implements a production-grade AWS infrastructure to deploy a containerized FastAPI application
+  The focus is on real-world DevOps infrastructure, networking, security, and container orchestration
+  Infrastructure is built fully using Terraform with no default AWS resources
+  The project is designed to be cost-optimized, modular, and scalable

---------------------------------------------------------------------------------------------------------------------------------------

# Current Infrastructure Tier:

+ 3-Tier Architecture
  +  Presentation Tier → Application Load Balancer (ALB)
  +  Application Tier → ECS Fargate (FastAPI containers)
  +  Infrastructure Tier → VPC, subnets, routing, security

--------------------------------------------------------------------------------------------------------------------

## Architecture Overview:

1. Users access the application using the ALB DNS
2. ALB listens on port 80
3. Traffic is forwarded to ECS tasks via target groups
4. FastAPI runs inside Docker containers
5. Containers are pulled from Amazon ECR
6. ECS tasks run inside private subnets
7. NAT Gateway allows outbound internet access
8. VPC provides complete network isolation

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
9.  IAM Roles and Policies
10. CloudWatch Logs
11. Security Groups

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
  + No direct internet access to ECS tasks
  + IAM execution role scoped only for ECS and CloudWatch logs

+ **Application Design**
  + FastAPI application containerized using Docker
  + Application listens on port 80
  + Health check endpoint exposed at /health
  + Docker image stored in Amazon ECR
  + ECS task definition references ECR image

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
4. FastAPI processes the request
5. Response returned back to client via ALB

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

+ Fully working FastAPI application on AWS
+ High availability using multi-AZ subnets
+ Secure container deployment using ECS Fargate
+ Proper ALB health checks and traffic routing
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