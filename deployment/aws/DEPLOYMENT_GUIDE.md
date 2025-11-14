# UltraWealth AWS Deployment Guide

## Overview

This guide covers deploying UltraWealth to AWS using Terraform for infrastructure as code and ECS Fargate for container orchestration.

## Architecture

### AWS Services Used

**Compute:**
- **ECS Fargate**: Serverless container orchestration
- **Application Load Balancer**: HTTPS traffic distribution
- **Auto Scaling**: Dynamic scaling based on CPU/memory

**Data:**
- **RDS PostgreSQL 16**: Primary database (Multi-AZ)
- **ElastiCache Redis**: Caching layer (Multi-AZ)
- **MSK (Managed Kafka)**: Event streaming (3-broker cluster)
- **S3**: Document and data storage

**Security:**
- **Secrets Manager**: API keys and passwords
- **KMS**: Encryption keys
- **VPC**: Network isolation
- **Security Groups**: Firewall rules

**Monitoring:**
- **CloudWatch**: Logs and metrics
- **Container Insights**: ECS monitoring
- **X-Ray**: Distributed tracing (optional)

**AI:**
- **OpenAI API**: GPT-4 for Anya AI assistant

## Prerequisites

### 1. AWS Account Setup

```bash
# Install AWS CLI
brew install awscli  # macOS
# or
choco install awscli  # Windows

# Configure AWS credentials
aws configure
```

Enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region: `ap-southeast-2` (Sydney)
- Default output format: `json`

### 2. Terraform Installation

```bash
# macOS
brew install terraform

# Windows
choco install terraform

# Verify
terraform --version
```

### 3. Docker Installation

Required for building and pushing container images.

```bash
# Verify
docker --version
```

### 4. OpenAI API Key

1. Sign up at https://platform.openai.com
2. Create API key
3. Save for later use

## Deployment Steps

### Step 1: Initialize Terraform

```bash
cd deployment/aws/terraform

# Initialize Terraform
terraform init
```

### Step 2: Create Terraform State Bucket

```bash
# Create S3 bucket for Terraform state
aws s3 mb s3://ultrawealth-terraform-state --region ap-southeast-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ultrawealth-terraform-state \
  --versioning-configuration Status=Enabled
```

### Step 3: Store OpenAI API Key in Secrets Manager

```bash
# Store OpenAI API key
aws secretsmanager create-secret \
  --name ultrawealth/openai-api-key \
  --secret-string "your-openai-api-key-here" \
  --region ap-southeast-2
```

### Step 4: Review and Apply Infrastructure

```bash
# Review planned changes
terraform plan

# Apply infrastructure
terraform apply
```

This will create:
- VPC with public/private subnets
- RDS PostgreSQL database
- ElastiCache Redis cluster
- MSK Kafka cluster
- ECS cluster
- Application Load Balancer
- Security groups
- IAM roles

**Estimated time:** 20-30 minutes

### Step 5: Build and Push Docker Image

```bash
# Get ECR login
aws ecr get-login-password --region ap-southeast-2 | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_repository_url | cut -d'/' -f1)

# Build image
cd ../../..  # Back to project root
docker build -t ultrawealth -f Dockerfile.ultrawealth .

# Tag image
docker tag ultrawealth:latest $(cd deployment/aws/terraform && terraform output -raw ecr_repository_url):latest

# Push image
docker push $(cd deployment/aws/terraform && terraform output -raw ecr_repository_url):latest
```

### Step 6: Deploy ECS Service

```bash
cd deployment/aws/terraform

# Update ECS service to use new image
aws ecs update-service \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service $(terraform output -raw ecs_service_name) \
  --force-new-deployment \
  --region ap-southeast-2
```

### Step 7: Initialize Database

```bash
# Get ECS task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service-name $(terraform output -raw ecs_service_name) \
  --region ap-southeast-2 \
  --query 'taskArns[0]' \
  --output text | cut -d'/' -f3)

# Run database initialization
aws ecs execute-command \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --task $TASK_ID \
  --container ultrawealth-api \
  --interactive \
  --command "python -m ultrawealth.database.init_db" \
  --region ap-southeast-2
```

### Step 8: Configure DNS

```bash
# Get ALB DNS name
terraform output alb_dns_name
```

Create a CNAME record in your DNS provider:
- **Name:** `api.ultrawealth.com.au`
- **Type:** CNAME
- **Value:** [ALB DNS name from above]

### Step 9: Verify Deployment

```bash
# Check service status
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services $(terraform output -raw ecs_service_name) \
  --region ap-southeast-2

# Test API
curl https://api.ultrawealth.com.au/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ultrawealth",
  "version": "1.0.0"
}
```

## Post-Deployment Configuration

### 1. Set Up Monitoring

**CloudWatch Dashboards:**
```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name UltraWealth \
  --dashboard-body file://cloudwatch-dashboard.json \
  --region ap-southeast-2
```

**Alarms:**
```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ultrawealth-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --region ap-southeast-2
```

### 2. Enable Backups

**RDS Automated Backups:**
Already configured in Terraform:
- Retention: 30 days
- Backup window: 03:00-04:00 UTC
- Multi-AZ: Enabled

**S3 Versioning:**
Already enabled for data bucket.

### 3. Set Up CI/CD (Optional)

Create GitHub Actions workflow for automated deployments:

```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-southeast-2
      
      - name: Login to ECR
        run: |
          aws ecr get-login-password --region ap-southeast-2 | \
            docker login --username AWS --password-stdin \
            ${{ secrets.ECR_REPOSITORY }}
      
      - name: Build and push
        run: |
          docker build -t ultrawealth -f Dockerfile.ultrawealth .
          docker tag ultrawealth:latest ${{ secrets.ECR_REPOSITORY }}:latest
          docker push ${{ secrets.ECR_REPOSITORY }}:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster ultrawealth-cluster-production \
            --service ultrawealth-api \
            --force-new-deployment
```

## Cost Estimation

**Monthly costs (Sydney region):**

| Service | Configuration | Monthly Cost (AUD) |
|:--------|:--------------|:-------------------|
| ECS Fargate | 2 tasks (2 vCPU, 4GB) | $120 |
| RDS PostgreSQL | db.t3.medium Multi-AZ | $180 |
| ElastiCache Redis | cache.t3.medium Multi-AZ | $100 |
| MSK Kafka | 3x kafka.m5.large | $600 |
| Application Load Balancer | Standard | $30 |
| NAT Gateway | 1 gateway | $60 |
| Data Transfer | 100GB/month | $15 |
| S3 Storage | 100GB | $3 |
| CloudWatch Logs | 10GB/month | $7 |
| **Total** | | **~$1,115/month** |

**Cost optimization tips:**
- Use Reserved Instances for RDS/ElastiCache (save 30-40%)
- Enable S3 Intelligent-Tiering
- Use Spot instances for non-critical workloads
- Review CloudWatch log retention

## Scaling

### Horizontal Scaling

Auto-scaling is configured for:
- **Min:** 2 tasks
- **Max:** 10 tasks
- **Target CPU:** 70%
- **Target Memory:** 80%

### Vertical Scaling

To increase task resources:

```bash
# Edit terraform/ecs.tf
# Update cpu and memory values
cpu    = "4096"  # 4 vCPU
memory = "8192"  # 8 GB

# Apply changes
terraform apply
```

## Disaster Recovery

### Backup Strategy

**RDS:**
- Automated daily backups (30-day retention)
- Multi-AZ for high availability
- Point-in-time recovery

**S3:**
- Versioning enabled
- Cross-region replication (optional)

**Kafka:**
- Multi-AZ deployment
- Automated backups to S3

### Recovery Procedures

**Database Restore:**
```bash
# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ultrawealth-postgres-restored \
  --db-snapshot-identifier [snapshot-id] \
  --region ap-southeast-2
```

**Complete Infrastructure Rebuild:**
```bash
# Terraform will rebuild from state
terraform apply
```

## Security Checklist

- [x] VPC with private subnets
- [x] Security groups with least privilege
- [x] Secrets in AWS Secrets Manager
- [x] Encryption at rest (RDS, Redis, Kafka, S3)
- [x] Encryption in transit (TLS/SSL)
- [x] Multi-AZ for high availability
- [x] IAM roles with minimal permissions
- [x] CloudWatch logging enabled
- [ ] WAF rules (optional, add if needed)
- [ ] GuardDuty enabled (optional)
- [ ] Security Hub enabled (optional)

## Troubleshooting

### Service Won't Start

```bash
# Check ECS task logs
aws logs tail /ecs/ultrawealth-api --follow --region ap-southeast-2

# Check task status
aws ecs describe-tasks \
  --cluster ultrawealth-cluster-production \
  --tasks [task-id] \
  --region ap-southeast-2
```

### Database Connection Issues

```bash
# Test database connectivity from ECS task
aws ecs execute-command \
  --cluster ultrawealth-cluster-production \
  --task [task-id] \
  --container ultrawealth-api \
  --interactive \
  --command "psql -h [rds-endpoint] -U ultracore -d ultracore" \
  --region ap-southeast-2
```

### High Costs

```bash
# Review cost breakdown
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

## Support

For issues or questions:
- **Documentation:** https://turingdynamics.atlassian.net/wiki/spaces/UW
- **Email:** support@turingdynamics.ai
- **GitHub:** https://github.com/TuringDynamics3000/UltraCore/issues
