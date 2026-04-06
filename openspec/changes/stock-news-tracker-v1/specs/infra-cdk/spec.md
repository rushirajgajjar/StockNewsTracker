## ADDED Requirements

### Requirement: CDK stack defines Lambda function
The CDK stack SHALL define a Lambda function using a Docker container image from ECR. The function MUST be configured with: 512MB memory, 900-second timeout, and environment variables for API keys and config.

#### Scenario: Stack synthesizes successfully
- **WHEN** `cdk synth` is run
- **THEN** a CloudFormation template is generated with a Lambda function resource using a container image

### Requirement: CDK stack defines EventBridge schedule
The CDK stack SHALL define an EventBridge rule that triggers the Lambda function on a configurable cron schedule. The default schedule MUST be every 6 hours.

#### Scenario: Default schedule deployment
- **WHEN** the stack is deployed without overriding the schedule
- **THEN** an EventBridge rule triggers the Lambda every 6 hours

#### Scenario: Custom schedule via CDK context
- **WHEN** the stack is deployed with `--context schedule="rate(12 hours)"`
- **THEN** the EventBridge rule uses the custom schedule

### Requirement: CDK stack defines S3 bucket
The CDK stack SHALL define an S3 bucket for filing archival with lifecycle rules to transition objects to Infrequent Access after 90 days.

#### Scenario: Bucket created with lifecycle
- **WHEN** the stack is deployed
- **THEN** an S3 bucket is created with IA transition after 90 days

### Requirement: CDK stack defines SES identity
The CDK stack SHALL define SES email identity resources for the sender and recipient addresses.

#### Scenario: Email identities created
- **WHEN** the stack is deployed with sender and recipient email addresses
- **THEN** SES email identity resources are created for both addresses

### Requirement: CDK stack grants least-privilege IAM
The CDK stack SHALL grant the Lambda function only the permissions it needs: SES send email, S3 read/write to the archive bucket, and CloudWatch Logs.

#### Scenario: Lambda IAM permissions
- **WHEN** the stack is deployed
- **THEN** the Lambda execution role has policies for SES SendEmail, S3 GetObject/PutObject on the archive bucket, and CloudWatch Logs CreateLogGroup/CreateLogStream/PutLogEvents
