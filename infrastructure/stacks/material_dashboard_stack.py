"""
Material Dashboard React Infrastructure Stack
Deploys S3, CloudFront, and related resources for hosting the React application
"""

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Tags,
)
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct
from pathlib import Path
import os
from typing import Dict, Any


class MaterialDashboardStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environment = config['environment']
        region = config['region']
        account = config['account']
        
        # Create S3 bucket for website hosting
        website_bucket = s3.Bucket(
            self, 
            'WebsiteBucket',
            bucket_name=f"material-dashboard-{environment}-{account}",
            versioned=True,
            public_read_access=False,  # Use Origin Access Identity instead
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY if environment == 'dev' else RemovalPolicy.RETAIN,
            auto_delete_objects=True if environment == 'dev' else False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            # Remove website hosting configuration
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                    allowed_origins=['*'],
                    allowed_headers=['*'],
                    max_age=3000
                )
            ],
            lifecycle_rules=[
                s3.LifecycleRule(
                    id='DeleteOldVersions',
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(30 if environment == 'dev' else 90)
                )
            ]
        )

        # CloudFront Origin Access Identity
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, 
            'OriginAccessIdentity',
            comment=f"OAI for {environment} environment"
        )

        # Grant read access to CloudFront
        website_bucket.grant_read(origin_access_identity)

        # CloudFront Function for SPA routing
        spa_function = cloudfront.Function(
            self, 
            'SpaFunction',
            code=cloudfront.FunctionCode.from_inline("""
                function handler(event) {
                    var request = event.request;
                    var uri = request.uri;
                    
                    // Handle SPA routing - redirect to index.html for non-file requests
                    if (uri.endsWith('/')) {
                        request.uri += 'index.html';
                    } else if (!uri.includes('.')) {
                        request.uri += '/index.html';
                    }
                    
                    return request;
                }
            """)
        )

        # Optional: Route53 hosted zone and ACM certificate in us-east-1 for custom domain
        domain = config.get('domain')
        hosted_zone_id = config.get('hostedZoneId')
        hosted_zone_name = config.get('hostedZoneName')
        zone = None
        certificate = None
        if domain and hosted_zone_id and hosted_zone_name:
            zone = route53.HostedZone.from_hosted_zone_attributes(
                self,
                'HostedZone',
                hosted_zone_id=hosted_zone_id,
                zone_name=hosted_zone_name,
            )
            certificate = acm.DnsValidatedCertificate(
                self,
                'SiteCertificate',
                domain_name=domain,
                hosted_zone=zone,
                region='us-east-1',  # CloudFront requires certs in us-east-1
            )

        # Resolve CloudFront price class from config string
        price_class_input = config['cloudfront']['priceClass']
        price_class_map = {
            'PriceClass_100': cloudfront.PriceClass.PRICE_CLASS_100,
            'PriceClass_200': cloudfront.PriceClass.PRICE_CLASS_200,
            'PriceClass_All': cloudfront.PriceClass.PRICE_CLASS_ALL,
        }
        price_class_value = price_class_map.get(price_class_input, cloudfront.PriceClass.PRICE_CLASS_100)

        # CloudFront Distribution
        distribution = cloudfront.Distribution(
            self, 
            'Distribution',
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    website_bucket,
                    origin_access_identity=origin_access_identity
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                # For S3 origins, do NOT forward the Host header; use managed CORS S3 policy
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
                function_associations=[
                    cloudfront.FunctionAssociation(
                        function=spa_function,
                        event_type=cloudfront.FunctionEventType.VIEWER_REQUEST
                    )
                ]
            ),
            default_root_object='index.html',
            price_class=price_class_value,
            certificate=certificate,
            domain_names=[domain] if certificate else None,
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path='/index.html'
                ),
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path='/index.html'
                )
            ],
            enable_logging=False
        )

        # Add WAF for production environment
        if environment == 'prod':
            web_acl = wafv2.CfnWebACL(
                self, 
                'WebACL',
                default_action=wafv2.CfnWebACL.DefaultActionProperty(allow=wafv2.CfnWebACL.AllowActionProperty()),
                scope='CLOUDFRONT',
                visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name='WebACLMetric',
                    sampled_requests_enabled=True
                ),
                rules=[
                    wafv2.CfnWebACL.RuleProperty(
                        name='AWSManagedRulesCommonRuleSet',
                        priority=1,
                        statement=wafv2.CfnWebACL.StatementProperty(
                            managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                                name='AWSManagedRulesCommonRuleSet',
                                vendor_name='AWS'
                            )
                        ),
                        override_action=wafv2.CfnWebACL.OverrideActionProperty(none=wafv2.CfnWebACL.NoneActionProperty()),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            cloud_watch_metrics_enabled=True,
                            metric_name='AWSManagedRulesCommonRuleSetMetric',
                            sampled_requests_enabled=True
                        )
                    ),
                    wafv2.CfnWebACL.RuleProperty(
                        name='RateLimit',
                        priority=2,
                        statement=wafv2.CfnWebACL.StatementProperty(
                            rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                                limit=2000,
                                aggregate_key_type='IP'
                            )
                        ),
                        action=wafv2.CfnWebACL.RuleActionProperty(block=wafv2.CfnWebACL.BlockActionProperty()),
                        visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                            cloud_watch_metrics_enabled=True,
                            metric_name='RateLimitMetric',
                            sampled_requests_enabled=True
                        )
                    )
                ]
            )
            # Associate WAF with CloudFront distribution
            distribution = cloudfront.Distribution(
                self, 
                'DistributionWithWAF',
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.S3Origin(
                        website_bucket,
                        origin_access_identity=origin_access_identity
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                    response_headers_policy=cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
                    function_associations=[
                        cloudfront.FunctionAssociation(
                            function=spa_function,
                            event_type=cloudfront.FunctionEventType.VIEWER_REQUEST
                        )
                    ]
                ),
                default_root_object='index.html',
                price_class=price_class_value,
                certificate=certificate,
                domain_names=[domain] if certificate else None,
                error_responses=[
                    cloudfront.ErrorResponse(
                        http_status=403,
                        response_http_status=200,
                        response_page_path='/index.html'
                    ),
                    cloudfront.ErrorResponse(
                        http_status=404,
                        response_http_status=200,
                        response_page_path='/index.html'
                    )
                ],
                enable_logging=False,
                web_acl_id=web_acl.attr_arn
            )

        # Route53 alias records to CloudFront for the custom domain
        if zone and domain:
            # Compute record name relative to zone (e.g., 'dev' for dev.bharade.com)
            record_name = domain
            if domain.endswith('.' + hosted_zone_name):
                record_name = domain[:-(len(hosted_zone_name) + 1)]
            route53.ARecord(
                self,
                'AliasRecordA',
                zone=zone,
                record_name=record_name,
                target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution)),
            )
            route53.AaaaRecord(
                self,
                'AliasRecordAAAA',
                zone=zone,
                record_name=record_name,
                target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution)),
            )

        # Deploy website assets from project build directory to S3 and invalidate CloudFront
        project_root = Path(__file__).resolve().parents[2]
        build_dir = project_root / 'build'
        s3_deployment.BucketDeployment(
            self,
            'DeployWebsite',
            sources=[s3_deployment.Source.asset(str(build_dir))],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=['/*'],
            prune=False
        )

        # Add tags to all resources
        Tags.of(self).add('Environment', environment)
        Tags.of(self).add('Project', 'material-dashboard-react')
        Tags.of(self).add('ManagedBy', 'cdk')

        # Outputs
        CfnOutput(
            self, 
            'WebsiteBucketName',
            value=website_bucket.bucket_name,
            description='S3 Bucket Name for Website Assets'
        )

        CfnOutput(
            self, 
            'CloudFrontDistributionId',
            value=distribution.distribution_id,
            description='CloudFront Distribution ID'
        )

        CfnOutput(
            self, 
            'CloudFrontDomainName',
            value=distribution.distribution_domain_name,
            description='CloudFront Distribution Domain Name'
        )

        CfnOutput(
            self, 
            'WebsiteUrl',
            value=f"https://{distribution.distribution_domain_name}",
            description='Website URL'
        )

        if environment == 'prod' and 'web_acl' in locals():
            CfnOutput(
                self, 
                'WebACLId',
                value=web_acl.attr_id,
                description='WAF Web ACL ID'
            )
