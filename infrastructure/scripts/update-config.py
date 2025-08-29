#!/usr/bin/env python3
"""
Utility script to update configuration files with AWS account details
"""

import json
import boto3
import argparse
import os
from pathlib import Path

def get_aws_account_id():
    """Get AWS account ID from AWS STS"""
    try:
        sts = boto3.client('sts')
        response = sts.get_caller_identity()
        return response['Account']
    except Exception as e:
        print(f"Error getting AWS account ID: {e}")
        return None

def update_config_file(config_path, account_id, domain=None, certificate_arn=None):
    """Update configuration file with provided values"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Update account ID
        if account_id:
            config['account'] = account_id
        
        # Update domain if provided
        if domain:
            config['domain'] = domain
        
        # Update certificate ARN if provided
        if certificate_arn:
            config['certificateArn'] = certificate_arn
        
        # Write back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Updated {config_path}")
        return True
        
    except Exception as e:
        print(f"Error updating {config_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Update AWS CDK configuration files')
    parser.add_argument('--account-id', help='AWS Account ID (will auto-detect if not provided)')
    parser.add_argument('--dev-domain', help='Development domain name')
    parser.add_argument('--prod-domain', help='Production domain name')
    parser.add_argument('--dev-certificate', help='Development SSL certificate ARN')
    parser.add_argument('--prod-certificate', help='Production SSL certificate ARN')
    
    args = parser.parse_args()
    
    # Get AWS account ID
    account_id = args.account_id or get_aws_account_id()
    if not account_id:
        print("Could not determine AWS account ID. Please provide it manually with --account-id")
        return
    
    print(f"Using AWS Account ID: {account_id}")
    
    # Get script directory
    script_dir = Path(__file__).parent.parent
    config_dir = script_dir / 'config'
    
    # Update dev config
    dev_config_path = config_dir / 'dev.json'
    if dev_config_path.exists():
        update_config_file(
            dev_config_path, 
            account_id, 
            args.dev_domain, 
            args.dev_certificate
        )
    
    # Update prod config
    prod_config_path = config_dir / 'prod.json'
    if prod_config_path.exists():
        update_config_file(
            prod_config_path, 
            account_id, 
            args.prod_domain, 
            args.prod_certificate
        )
    
    print("\nConfiguration files updated successfully!")
    print("\nNext steps:")
    print("1. Review the configuration files in the config/ directory")
    print("2. Update domain names and certificate ARNs if needed")
    print("3. Run the deployment script: ./deploy.sh dev")

if __name__ == '__main__':
    main()
