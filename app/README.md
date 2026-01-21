# FastAPI Application (App Layer)

This directory contains the FastAPI application used in the Multi-AWS infrastructure project
+ The app is designed to run as a stateless container on AWS ECS Fargate
+ It exposes HTTP APIs and a health endpoint for load balancer checks

## Tech Stack

+ Python 3.11
+ FastAPI
+ Uvicorn
+ Docker
+ Docker-compose.yaml (for local testing)

## Application Behavior

+ The application listens on port 80 inside the container
+ A /health endpoint is exposed for ALB target group health checks
+ The app is environment-aware (local vs cloud)
+ Startup logic is lightweight to ensure ECS task stability

## File Structure

+ app.py → Main FastAPI application
+ Dockerfile → Container build instructions
+ requirements.txt → Python dependencies

## Run Locally

+ Build the Docker image
+ The image is pushed to Amazon ECR
+ ECS pulls the image during task startup
+ No state is stored locally inside the container
+ Logs are shipped to CloudWatch Logs via ECS

## Purpose in Overall Project

+ Acts as the Application Tier in a 3-tier AWS architecture
+ Designed to scale horizontally with ECS
+ Works behind an Application Load Balancer

## Status

+ Tested locally using Docker
+ Successfully deployed on AWS ECS Fargate
+ Integrated with ALB health checks
