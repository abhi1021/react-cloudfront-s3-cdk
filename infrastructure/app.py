#!/usr/bin/env python3
"""
AWS CDK App for Material Dashboard React
Deploys serverless infrastructure for both dev and prod environments
"""

import json
import os
from aws_cdk import App, Environment
from stacks.material_dashboard_stack import MaterialDashboardStack

def load_config(environment: str) -> dict:
    """Load configuration for the specified environment"""
    config_path = f"config/{environment}.json"
    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    app = App()
    
    # Deploy dev stack only
    dev_config = load_config('dev')
    MaterialDashboardStack(
        app, 
        f"MaterialDashboard-{dev_config['environment'].title()}",
        config=dev_config,
        env=Environment(
            account=dev_config['account'],
            region=dev_config['region']
        )
    )
    
    app.synth()

if __name__ == '__main__':
    main()
