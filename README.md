# react-cloudfront-s3-cdk

A sample project showcasing how to deploy a React (Node.js) UI to an AWS serverless architecture using the AWS Cloud Development Kit (CDK) in Python.

This repository provides a ready-to-use blueprint that builds a React app and deploys it to an S3 bucket behind a CloudFront distribution, with optional custom domain, SSL, and basic WAF. It also includes opinionated security defaults and secret-scanning hooks.

## Features

- React app (Create React App) with Material UI theme
- AWS CDK (Python) infrastructure-as-code
  - S3 static website bucket (private) + CloudFront distribution
  - Optional custom domain and ACM certificate
  - SPA-friendly error responses (403/404 → index.html)
  - Optional AWS WAF (managed rules + rate limiting)
  - Simple API Gateway + Lambda scaffold (optional)
- CI: GitHub Actions secret scan with gitleaks
- Local pre-commit secret scan (Husky + gitleaks) – optional
- .gitignore hardened to avoid committing secrets and local artifacts

## Repository Structure

- `/src`, `/public` – React application source and static assets
- `/infrastructure` – AWS CDK (Python) project
  - `config/dev.json`, `config/prod.json` – environment configuration (placeholders)
  - `stacks/material_dashboard_stack.py` – main stack definition
  - `deploy.sh` – helper script for quick deploys
- `.github/workflows/secret-scan.yml` – CI secret scanning (gitleaks)

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+ and pip
- AWS account and credentials configured (for deployment)
- AWS CDK CLI: `npm install -g aws-cdk`
- (Optional) gitleaks for local secret scans: `brew install gitleaks`

## Getting Started

Install dependencies and run locally:

- npm install
- npm start

Build production bundle:

- npm run build

## Configure Environments

Edit the infrastructure/config files and replace placeholders:

- infrastructure/config/dev.json
- infrastructure/config/prod.json

Replace values such as:

- YOUR_AWS_ACCOUNT_ID
- yourdomain.com
- YOUR_HOSTED_ZONE_ID
- certificate ARNs (if using custom DNS/SSL)

Note: Do not commit real secrets. Environment values should be provided via parameters or env vars; .env files are ignored by Git.

## Deploy with AWS CDK

First-time only per account/region:

- cdk bootstrap aws://ACCOUNT-ID/REGION

Quick deploy via helper script:

- ./infrastructure/deploy.sh dev
- ./infrastructure/deploy.sh prod

Manual deploy example:

- cd infrastructure
- python3 -m venv venv && source venv/bin/activate
- pip install -r requirements.txt
- cd .. && npm run build
- cd infrastructure && cdk deploy --context environment=dev

## Security and Compliance

- Secret scanning: GitHub Actions workflow runs gitleaks on push/PR.
- Local pre-commit hook runs gitleaks when installed; skips if not present.
- .gitignore includes env files, keys, certificates, OS/editor files, caches, and venvs.

## Attribution and License

This UI uses the Material Dashboard React template by Creative Tim for demo purposes. See LICENSE.md for details and the Creative Tim license.

## Troubleshooting

- 403/404 routing: CloudFront is configured to serve index.html for SPA routes.
- Region/account mismatches: ensure your config files match your target region and account.
- Permissions: verify your AWS credentials have sufficient permissions for CDK deploys.
