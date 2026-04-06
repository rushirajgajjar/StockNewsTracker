"""CDK stack defining all AWS resources for StockNewsTracker."""

from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_ecr_assets as ecr_assets,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_ses as ses,
)
from constructs import Construct


class StockNewsTrackerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Context values with defaults
        schedule_expression = self.node.try_get_context("schedule") or "rate(6 hours)"
        sender_email = self.node.try_get_context("sender_email") or ""
        recipient_email = self.node.try_get_context("recipient_email") or ""
        anthropic_api_key = self.node.try_get_context("anthropic_api_key") or ""

        # S3 bucket for filing archival
        archive_bucket = s3.Bucket(
            self,
            "ArchiveBucket",
            bucket_name="stocknewstracker-archive",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(90),
                        )
                    ]
                )
            ],
        )

        # Docker image for Lambda
        docker_image = ecr_assets.DockerImageAsset(
            self,
            "LambdaImage",
            directory="..",  # Project root
        )

        # Lambda function
        lambda_fn = _lambda.DockerImageFunction(
            self,
            "StockNewsTrackerFn",
            code=_lambda.DockerImageCode.from_ecr(
                repository=docker_image.repository,
                tag_or_digest=docker_image.asset_hash,
            ),
            memory_size=512,
            timeout=Duration.seconds(900),
            environment={
                "ANTHROPIC_API_KEY": anthropic_api_key,
                "S3_BUCKET_NAME": archive_bucket.bucket_name,
                "EMAIL_TO": recipient_email,
                "EMAIL_FROM": sender_email,
            },
        )

        # Grant Lambda read/write to the archive bucket
        archive_bucket.grant_read_write(lambda_fn)

        # Grant Lambda SES send permissions
        lambda_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"],
            )
        )

        # EventBridge schedule
        rule = events.Rule(
            self,
            "ScheduleRule",
            schedule=events.Schedule.expression(schedule_expression),
        )
        rule.add_target(targets.LambdaFunction(lambda_fn))

        # SES email identities
        if sender_email:
            ses.EmailIdentity(
                self,
                "SenderIdentity",
                identity=ses.Identity.email(sender_email),
            )

        if recipient_email:
            ses.EmailIdentity(
                self,
                "RecipientIdentity",
                identity=ses.Identity.email(recipient_email),
            )
