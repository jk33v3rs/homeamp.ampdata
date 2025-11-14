"""
Pulumi Infrastructure Automation for Plugin Update Monitoring

This module defines the Pulumi infrastructure for automated hourly
plugin update checks. It sets up:
- Scheduled Lambda/Cloud Function for hourly checks
- S3/Storage for staging area
- Integration with monitoring systems
- Excel spreadsheet output automation
"""

import pulumi
import pulumi_aws as aws
from pulumi import Output
from pathlib import Path
from typing import Dict, Any


class PluginUpdateInfrastructure:
    """
    Pulumi infrastructure for plugin update automation
    
    Creates:
    - S3 bucket for plugin staging
    - Lambda function for hourly checks
    - CloudWatch Events for scheduling
    - IAM roles and policies
    - SNS topic for notifications
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Pulumi infrastructure
        
        Args:
            config: Configuration dict with:
                - project_name: Name of the project
                - environment: dev/staging/prod
                - schedule_expression: Cron expression (default: "cron(0 * * * ? *)" for hourly)
                - notification_email: Email for update notifications
                - plugin_registry_path: Path to plugin registry YAML
                - excel_output_bucket: S3 bucket for Excel files
        """
        self.config = config
        self.project_name = config.get('project_name', 'archivesmp-plugin-updates')
        self.environment = config.get('environment', 'prod')
        self.schedule = config.get('schedule_expression', 'cron(0 * * * ? *)')  # Hourly
        
        # Create resources
        self.staging_bucket = self._create_staging_bucket()
        self.excel_bucket = self._create_excel_bucket()
        self.lambda_role = self._create_lambda_role()
        self.lambda_function = self._create_lambda_function()
        self.cloudwatch_rule = self._create_schedule_rule()
        self.sns_topic = self._create_sns_topic()
        
        # Connect components
        self._configure_lambda_permissions()
        self._configure_notifications()
        
        # Export outputs
        self._export_outputs()
    
    def _create_staging_bucket(self) -> aws.s3.Bucket:
        """Create S3 bucket for staged plugin JARs"""
        bucket = aws.s3.Bucket(
            f"{self.project_name}-staging-{self.environment}",
            bucket=f"{self.project_name}-staging-{self.environment}",
            acl="private",
            versioning=aws.s3.BucketVersioningArgs(
                enabled=True  # Keep version history
            ),
            lifecycle_rules=[
                aws.s3.BucketLifecycleRuleArgs(
                    enabled=True,
                    expiration=aws.s3.BucketLifecycleRuleExpirationArgs(
                        days=90  # Clean up old staged plugins after 90 days
                    )
                )
            ],
            tags={
                "Project": self.project_name,
                "Environment": self.environment,
                "Purpose": "plugin-staging"
            }
        )
        
        return bucket
    
    def _create_excel_bucket(self) -> aws.s3.Bucket:
        """Create S3 bucket for Excel reports"""
        bucket = aws.s3.Bucket(
            f"{self.project_name}-reports-{self.environment}",
            bucket=f"{self.project_name}-reports-{self.environment}",
            acl="private",
            versioning=aws.s3.BucketVersioningArgs(
                enabled=True
            ),
            tags={
                "Project": self.project_name,
                "Environment": self.environment,
                "Purpose": "excel-reports"
            }
        )
        
        return bucket
    
    def _create_lambda_role(self) -> aws.iam.Role:
        """Create IAM role for Lambda function"""
        role = aws.iam.Role(
            f"{self.project_name}-lambda-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }]
            }"""
        )
        
        # Attach basic Lambda execution policy
        aws.iam.RolePolicyAttachment(
            f"{self.project_name}-lambda-basic-execution",
            role=role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        )
        
        # Attach S3 access policy
        s3_policy = aws.iam.RolePolicy(
            f"{self.project_name}-lambda-s3-access",
            role=role.name,
            policy=Output.all(
                self.staging_bucket.arn,
                self.excel_bucket.arn
            ).apply(lambda args: f"""{{
                "Version": "2012-10-17",
                "Statement": [{{
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "{args[0]}/*",
                        "{args[1]}/*",
                        "{args[0]}",
                        "{args[1]}"
                    ]
                }}]
            }}""")
        )
        
        return role
    
    def _create_lambda_function(self) -> aws.lambda_.Function:
        """Create Lambda function for plugin update checks"""
        
        # Package Lambda function code
        # In production, this would be a proper deployment package
        lambda_code = pulumi.AssetArchive({
            '.': pulumi.FileArchive('./lambda_package.zip')  # Pre-built package
        })
        
        function = aws.lambda_.Function(
            f"{self.project_name}-update-checker",
            name=f"{self.project_name}-update-checker-{self.environment}",
            runtime="python3.10",
            handler="handler.main",
            role=self.lambda_role.arn,
            code=lambda_code,
            timeout=300,  # 5 minutes
            memory_size=512,
            environment=aws.lambda_.FunctionEnvironmentArgs(
                variables={
                    "STAGING_BUCKET": self.staging_bucket.id,
                    "EXCEL_BUCKET": self.excel_bucket.id,
                    "PLUGIN_REGISTRY_PATH": self.config.get('plugin_registry_path', '/config/plugin_registry.yaml'),
                    "ENVIRONMENT": self.environment
                }
            ),
            tags={
                "Project": self.project_name,
                "Environment": self.environment
            }
        )
        
        return function
    
    def _create_schedule_rule(self) -> aws.cloudwatch.EventRule:
        """Create CloudWatch Events rule for hourly scheduling"""
        rule = aws.cloudwatch.EventRule(
            f"{self.project_name}-hourly-check",
            name=f"{self.project_name}-hourly-check-{self.environment}",
            description="Trigger plugin update check every hour",
            schedule_expression=self.schedule
        )
        
        # Create target to invoke Lambda
        target = aws.cloudwatch.EventTarget(
            f"{self.project_name}-lambda-target",
            rule=rule.name,
            arn=self.lambda_function.arn
        )
        
        return rule
    
    def _create_sns_topic(self) -> aws.sns.Topic:
        """Create SNS topic for update notifications"""
        topic = aws.sns.Topic(
            f"{self.project_name}-notifications",
            name=f"{self.project_name}-notifications-{self.environment}",
            display_name="ArchiveSMP Plugin Update Notifications"
        )
        
        # Subscribe email if configured
        notification_email = self.config.get('notification_email')
        if notification_email:
            aws.sns.TopicSubscription(
                f"{self.project_name}-email-subscription",
                topic=topic.arn,
                protocol="email",
                endpoint=notification_email
            )
        
        return topic
    
    def _configure_lambda_permissions(self):
        """Configure Lambda permissions for CloudWatch Events"""
        aws.lambda_.Permission(
            f"{self.project_name}-cloudwatch-invoke",
            action="lambda:InvokeFunction",
            function=self.lambda_function.name,
            principal="events.amazonaws.com",
            source_arn=self.cloudwatch_rule.arn
        )
    
    def _configure_notifications(self):
        """Configure SNS notifications from Lambda"""
        # Add SNS publish permission to Lambda role
        aws.iam.RolePolicy(
            f"{self.project_name}-lambda-sns-publish",
            role=self.lambda_role.name,
            policy=self.sns_topic.arn.apply(lambda arn: f"""{{
                "Version": "2012-10-17",
                "Statement": [{{
                    "Effect": "Allow",
                    "Action": [
                        "sns:Publish"
                    ],
                    "Resource": "{arn}"
                }}]
            }}""")
        )
    
    def _export_outputs(self):
        """Export Pulumi stack outputs"""
        pulumi.export('staging_bucket_name', self.staging_bucket.id)
        pulumi.export('excel_bucket_name', self.excel_bucket.id)
        pulumi.export('lambda_function_name', self.lambda_function.name)
        pulumi.export('lambda_function_arn', self.lambda_function.arn)
        pulumi.export('sns_topic_arn', self.sns_topic.arn)
        pulumi.export('schedule_expression', self.schedule)


def create_infrastructure():
    """
    Main entry point for Pulumi stack creation
    
    Call this from __main__.py:
        import pulumi
        from automation.pulumi_infrastructure import create_infrastructure
        
        create_infrastructure()
    """
    
    # Load configuration from Pulumi config
    config = pulumi.Config()
    
    infrastructure_config = {
        'project_name': config.get('projectName') or 'archivesmp-plugin-updates',
        'environment': config.get('environment') or 'prod',
        'schedule_expression': config.get('scheduleExpression') or 'cron(0 * * * ? *)',
        'notification_email': config.get('notificationEmail'),
        'plugin_registry_path': config.get('pluginRegistryPath') or '/config/plugin_registry.yaml',
        'excel_output_bucket': config.get('excelOutputBucket')
    }
    
    infrastructure = PluginUpdateInfrastructure(infrastructure_config)
    
    return infrastructure


if __name__ == "__main__":
    create_infrastructure()
