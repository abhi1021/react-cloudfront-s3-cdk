#!/bin/bash

# Material Dashboard React - AWS CDK Deployment Script
# This script builds the React application and deploys it to AWS using CDK

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment is provided
if [ -z "$1" ]; then
    print_error "Usage: $0 <environment> [region]"
    print_error "Environment must be 'dev' or 'prod'"
    exit 1
fi

ENVIRONMENT=$1
REGION=${2:-""}

# Validate environment
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
    print_error "Environment must be 'dev' or 'prod'"
    exit 1
fi

# Set region based on environment if not provided
if [ -z "$REGION" ]; then
    if [ "$ENVIRONMENT" = "dev" ]; then
        REGION="eu-west-1"
    else
        REGION="eu-west-2"
    fi
fi

print_status "Deploying Material Dashboard React to $ENVIRONMENT environment in $REGION"

# Get the project root directory
PROJECT_ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"

print_status "Project root: $PROJECT_ROOT"
print_status "Infrastructure directory: $INFRASTRUCTURE_DIR"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/package.json" ]; then
    print_error "package.json not found. Please run this script from the project root."
    exit 1
fi

# Check if infrastructure directory exists
if [ ! -d "$INFRASTRUCTURE_DIR" ]; then
    print_error "Infrastructure directory not found: $INFRASTRUCTURE_DIR"
    exit 1
fi

# Change to infrastructure directory
cd "$INFRASTRUCTURE_DIR"

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating Python virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install AWS CDK if not already installed
if ! command -v cdk &> /dev/null; then
    print_status "Installing AWS CDK..."
    npm install -g aws-cdk
fi

# Change back to project root
cd "$PROJECT_ROOT"

# Install Node.js dependencies if not already installed
if [ ! -d "node_modules" ]; then
    print_status "Installing Node.js dependencies..."
    npm install
fi

# Build the React application
print_status "Building React application..."
npm run build

# Check if build was successful
if [ ! -d "build" ]; then
    print_error "Build failed. 'build' directory not found."
    exit 1
fi

print_success "React application built successfully"

# Change to infrastructure directory for CDK deployment
cd "$INFRASTRUCTURE_DIR"

# Bootstrap CDK if needed
print_status "Checking CDK bootstrap status..."
if ! cdk list --context environment=$ENVIRONMENT &> /dev/null; then
    print_status "Bootstrapping CDK in $REGION..."
    cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/$REGION
fi

# Deploy the stack
print_status "Deploying CDK stack for $ENVIRONMENT environment..."
cdk deploy --context environment=$ENVIRONMENT --require-approval never

print_success "Deployment completed successfully!"
print_status "You can find the CloudFormation outputs above for your deployment details."
