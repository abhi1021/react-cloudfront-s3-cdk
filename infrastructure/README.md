# Material Dashboard React - AWS CDK Infrastructure

This directory contains the AWS CDK infrastructure code for deploying the Material Dashboard React application as a serverless stack.

## Architecture

The infrastructure creates the following AWS resources:

- **S3 Bucket**: Static website hosting for the React application
- **CloudFront Distribution**: Global content delivery network for fast loading
- **API Gateway**: REST API for backend functionality
- **Lambda Function**: Serverless backend API
- **CloudWatch Logs**: Logging for Lambda functions and CloudFront

## Prerequisites

1. **AWS CLI** installed and configured with appropriate credentials
2. **Python 3.8+** installed
3. **Node.js 14+** installed
4. **AWS CDK CLI** installed globally (`npm install -g aws-cdk`)

## Configuration

### Environment Configuration Files

The infrastructure uses separate configuration files for different environments:

- `config/dev.json` - Development environment (eu-west-1)
- `config/prod.json` - Production environment (eu-west-2)

### Required Configuration Updates

Before deploying, update the following in both configuration files:

1. **AWS Account ID**: Replace `YOUR_AWS_ACCOUNT_ID` with your actual AWS account ID
2. **Domain Names**: Update the domain names to match your domain
3. **SSL Certificates**: Update the certificate ARNs if you have custom SSL certificates

## Deployment

### Quick Deployment

Use the provided deployment script:

```bash
# Deploy to development environment
./infrastructure/deploy.sh dev

# Deploy to production environment
./infrastructure/deploy.sh prod
```

### Manual Deployment

1. **Install Python dependencies**:
   ```bash
   cd infrastructure
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Build the React application**:
   ```bash
   cd ..  # Back to project root
   npm install
   npm run build
   ```

3. **Bootstrap CDK** (first time only):
   ```bash
   cd infrastructure
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

4. **Deploy the stack**:
   ```bash
   cdk deploy --context environment=dev  # or prod
   ```

## Stack Structure

### Development Stack (eu-west-1)
- Stack Name: `MaterialDashboard-Dev`
- S3 Bucket: `material-dashboard-dev-{account-id}`
- CloudFront Distribution: Optimized for development

### Production Stack (eu-west-2)
- Stack Name: `MaterialDashboard-Prod`
- S3 Bucket: `material-dashboard-prod-{account-id}`
- CloudFront Distribution: Optimized for production with global edge locations

## Features

### S3 Bucket Configuration
- Versioning enabled
- Server-side encryption (SSE-S3)
- Public access blocked
- CORS configured for web access
- Lifecycle policies for cost optimization

### CloudFront Configuration
- HTTPS redirect
- Optimized caching policies
- SPA routing support (404 → index.html)
- Compression enabled
- Access logging to S3

### API Gateway & Lambda
- REST API with CORS support
- Python 3.9 runtime
- Configurable memory and timeout
- CloudWatch logging

## Outputs

After deployment, the following outputs are available:

- **WebsiteBucketName**: S3 bucket name
- **CloudFrontDistributionId**: CloudFront distribution ID
- **CloudFrontDomainName**: CloudFront domain name
- **WebsiteUrl**: Full website URL

## Cost Optimization

### Development Environment
- CloudFront Price Class: PriceClass_100 (US, Canada, Europe)
- Lambda: 512MB memory, 30s timeout
- S3: Standard storage

### Production Environment
- CloudFront Price Class: PriceClass_All (Global)
- Lambda: 1024MB memory, 60s timeout
- S3: Standard storage with lifecycle policies

## Security

- All S3 buckets have public access blocked
- CloudFront uses Origin Access Identity for secure S3 access
- Lambda functions have minimal IAM permissions
- All resources are tagged for cost tracking and management

## Monitoring

- CloudWatch logs for Lambda functions
- CloudFront access logs stored in S3
- CloudFormation stack events for deployment monitoring

## Cleanup

To destroy the infrastructure:

```bash
cd infrastructure
cdk destroy --context environment=dev  # or prod
```

**Warning**: This will permanently delete all resources including S3 buckets and their contents.

## Troubleshooting

### Common Issues

1. **CDK Bootstrap Required**: If you get a bootstrap error, run:
   ```bash
   cdk bootstrap aws://ACCOUNT-NUMBER/REGION
   ```

2. **Build Directory Missing**: Ensure you've run `npm run build` before deployment

3. **Permission Errors**: Verify your AWS credentials have the necessary permissions

4. **Region Mismatch**: Ensure you're deploying to the correct region for each environment

### Logs

- **CloudFormation**: Check the AWS Console for stack events
- **Lambda**: CloudWatch logs in `/aws/lambda/MaterialDashboard-{env}-ApiLambda`
- **CloudFront**: Access logs in the S3 bucket `material-dashboard-logs-{env}-{account}`

## Support

For issues or questions:
1. Check the CloudFormation stack events
2. Review CloudWatch logs
3. Verify configuration files are correct
4. Ensure all prerequisites are met
