# AWS SAM Deployment Research — Official AWS Documentation Findings

**Date:** 2026-02-17
**Purpose:** Resolve deployment issues with the BancaFiel AWS SAM backend project.
**Sources:** All findings are sourced exclusively from official AWS Documentation via the AWS MCP Documentation tool.

---

## Table of Contents

1. [Question 1: RDS PostgreSQL Free Tier CloudFormation Constraints](#question-1-rds-postgresql-free-tier-cloudformation-constraints)
2. [Question 2: VPC + Publicly Accessible RDS Setup](#question-2-vpc--publicly-accessible-rds-setup-cloudformation)
3. [Question 3: SAM S3 Event + Lambda Circular Dependency](#question-3-sam-s3-event--lambda-circular-dependency)
4. [Question 4: Lambda (outside VPC) connecting to RDS (inside VPC)](#question-4-lambda-outside-vpc-connecting-to-rds-inside-vpc-publiclyaccessible-true)
5. [Question 5: SAM API Gateway + Step Functions Circular Dependency](#question-5-sam-api-gateway--step-functions-circular-dependency)
6. [Summary of Fixes Needed](#summary-of-fixes-needed)

---

## Question 1: RDS PostgreSQL Free Tier CloudFormation Constraints

### 1.1 Correct `EngineVersion` for PostgreSQL on db.t3.micro (Free Tier)

According to the AWS documentation page on [Supported DB engines for DB instance classes](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.Support.html), the `db.t3.micro` instance class for PostgreSQL supports:

> **All PostgreSQL 17, 16, 15, 14, 13, 12, 11, and 10 versions; and 9.6.22 and higher 9 versions**

The AWS Free Tier (12-months free) offers 750 hours/month of `db.t3.micro` usage. PostgreSQL versions supported for `db.t3.micro` include all current major versions from 10 through 17.

**Recommended EngineVersion for production stability (as of early 2026):**
- `"17"` — PostgreSQL 17 (latest major, fully supported on db.t3.micro)
- `"16"` — PostgreSQL 16 (stable, widely used)
- `"15"` — PostgreSQL 15 (also excellent choice)

**Important:** Specify only the major version in CloudFormation (e.g., `"16"`) and AWS will use the latest minor version. Or specify a full minor version string such as `"16.6"` if you need a pinned version. As per the [PostgreSQL DB Versions page](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.DBVersions.html):

> "If a major version is specified but a minor version is not, Amazon RDS defaults to a recent release of the major version you have specified."

**CloudFormation example:**
```yaml
MyDBInstance:
  Type: AWS::RDS::DBInstance
  Properties:
    Engine: postgres
    EngineVersion: "16"          # Major version only — RDS picks latest minor
    DBInstanceClass: db.t3.micro
    AllocatedStorage: "20"       # 20 GB is the free tier limit
```

### 1.2 `StorageEncrypted: true` on db.t3.micro — Is It Allowed?

According to the [Encrypting Amazon RDS resources](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html) page, Amazon RDS encryption is available for most DB instance classes. The following table from the official docs lists the **only** instance classes that do NOT support encryption:

| Instance type | Instance class |
|---|---|
| General purpose (M1) | db.m1.small, db.m1.medium, db.m1.large, db.m1.xlarge |
| Memory optimized (M2) | db.m2.xlarge, db.m2.2xlarge, db.m2.4xlarge |
| Burstable (T2) | **db.t2.micro** |

**Critical Finding:** `db.t3.micro` is NOT in this list. `db.t2.micro` does not support encryption, but `db.t3.micro` DOES support `StorageEncrypted: true`.

However, the free tier error about encryption is typically not an RDS encryption limitation — it is an account-level constraint. **On a brand-new AWS account in the free tier**, enabling encryption requires an AWS KMS key. The default AWS managed key is free, but if a KMS customer-managed key is specified, that incurs charges outside the free tier.

**Conclusion:** `StorageEncrypted: true` is technically supported on `db.t3.micro`. If you encounter errors, omit the `KmsKeyId` property and let RDS use the AWS managed key (free). If deploying on a strict free-tier-only account, set `StorageEncrypted: false` to avoid any potential key-related errors.

```yaml
# Safe for free tier — uses AWS managed key (no additional cost):
StorageEncrypted: true
# KmsKeyId is NOT specified — uses the default aws/rds managed key

# OR, simplest approach for free tier:
StorageEncrypted: false
```

### 1.3 Maximum `BackupRetentionPeriod` for Free Tier

According to the [Backup retention period](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html) documentation:

> "You can set the backup retention period of a DB instance to between **0 and 35 days**. Setting the backup retention period to 0 disables automated backups."

The error message "backup retention period exceeds maximum available to free tier customers" is a runtime enforcement by AWS on accounts using the free tier. The AWS Free Tier offers **20 GB of backup storage** (equivalent to 1x the DB storage). The free tier does NOT cap the retention period at a specific day count in the CloudFormation API — instead, it caps the total backup storage consumed.

**Finding:** The error typically occurs when the backup retention period is set too high (e.g., 7+ days) combined with a large allocated storage, causing the backup storage to exceed the 20 GB free tier limit.

**Recommended fix for free tier:**
```yaml
BackupRetentionPeriod: 0    # Disables automated backups entirely — safest for free tier
                             # OR
BackupRetentionPeriod: 1    # Minimum non-zero value; minimal storage consumption
```

> WARNING: Setting `BackupRetentionPeriod` from 0 to a non-zero value or vice versa causes a DB instance outage (reboot). Plan accordingly.

### 1.4 `PubliclyAccessible: true` — Supported on Free Tier RDS in a VPC?

Per the [Working with a DB instance in a VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html) documentation:

> "If you want your DB instance in the VPC to be publicly accessible, make sure to turn on the VPC attributes **DNS hostnames** and **DNS resolution**."

And from the [Subnets section](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html):

> "For a DB instance to be publicly accessible, **all of the subnets in its DB subnet group must be public**. If a subnet that's associated with a publicly accessible DB instance changes from public to private, it can affect DB instance availability."

**Conclusion:** `PubliclyAccessible: true` IS supported on free tier `db.t3.micro` in a VPC. However, the VPC subnets in the DB subnet group MUST be public subnets (having a route to an Internet Gateway). This is covered in detail in Question 2.

```yaml
PubliclyAccessible: true    # Supported on db.t3.micro in a VPC
                             # Requires: subnets with IGW route, EnableDnsHostnames: true, EnableDnsSupport: true
```

### 1.5 Other CloudFormation Properties Restricted on Free Tier

Based on research across the AWS documentation:

| Property | Free Tier Status | Notes |
|---|---|---|
| `DBInstanceClass` | Must be `db.t3.micro` | Only instance eligible for free tier |
| `AllocatedStorage` | Max 20 GB (gp2) free | Beyond 20 GB incurs charges |
| `MultiAZ` | Must be `false` | Multi-AZ incurs charges |
| `StorageType` | `gp2` recommended | `gp3` and `io1` may incur charges |
| `BackupRetentionPeriod` | 0 or 1 recommended | >1 day may exceed 20 GB backup storage free limit |
| `StorageEncrypted` | Supported on t3.micro | Encryption itself is free; KMS CMK has costs |
| `PerformanceInsights` | Not free tier | Enhanced Monitoring >0 seconds incurs charges |
| `MonitoringInterval` | 0 (disabled) | Enhanced Monitoring incurs charges if >0 |
| `EnableCloudwatchLogsExports` | Incurs costs | CloudWatch logs are not free |

**Minimum safe free-tier CloudFormation snippet:**
```yaml
MyDatabase:
  Type: AWS::RDS::DBInstance
  Properties:
    DBInstanceClass: db.t3.micro
    Engine: postgres
    EngineVersion: "16"
    AllocatedStorage: "20"
    StorageType: gp2
    DBName: mydb
    MasterUsername: !Ref DBUsername
    MasterUserPassword: !Ref DBPassword
    BackupRetentionPeriod: 0
    MultiAZ: false
    PubliclyAccessible: true
    StorageEncrypted: false
    DBSubnetGroupName: !Ref MyDBSubnetGroup
    VPCSecurityGroups:
      - !Ref MyDBSecurityGroup
    DeletionPolicy: Delete
```

---

## Question 2: VPC + Publicly Accessible RDS Setup (CloudFormation)

### 2.1 Official Scenario: Client Application Through the Internet

From [Scenarios for accessing a DB instance in a VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.Scenarios.html):

> "To access a DB instance in a VPC from a client application through the internet, you configure a VPC with a **single public subnet**, and an **internet gateway** to enable communication over the internet."

The official recommendation for this scenario:
- A VPC of size `/16` (e.g., CIDR: `10.0.0.0/16`) — provides 65,536 private IP addresses
- Subnets of size `/24` (e.g., CIDR: `10.0.0.0/24`) — provides 256 private IP addresses
- An Amazon RDS DB instance associated with the VPC and subnet
- An **internet gateway** which connects the VPC to the internet
- A **security group** associated with the DB instance, with inbound rules allowing client access

### 2.2 Does the VPC Need an Internet Gateway?

**Yes — mandatory.** From the [Troubleshooting for Amazon RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html) page, under connectivity issues:

> "**Internet gateway** – For a DB instance to be publicly accessible, the subnets in its DB subnet group must have an internet gateway."

The troubleshooting page also confirms that GATEWAY CHECK is a specific validation step RDS performs.

### 2.3 Do DB Subnets Need to Be Public Subnets?

**Yes — mandatory.** From the [Working with a DB instance in a VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html) documentation:

> "For a DB instance to be publicly accessible, **all of the subnets in its DB subnet group must be public**."

From the [Enable internet access using an internet gateway](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html) VPC documentation:

> "If a subnet is associated with a route table that has a **route to an internet gateway**, it's known as a **public subnet**. If a subnet is associated with a route table that does not have a route to an internet gateway, it's known as a **private subnet**."

**Therefore:** For `PubliclyAccessible: true` RDS in a VPC, each subnet in the DB subnet group must have a route table entry of `0.0.0.0/0 → <InternetGateway>`.

### 2.4 Additional VPC Requirements

From the [Working with a DB instance in a VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html) page:

> "If you want your DB instance in the VPC to be publicly accessible, make sure to turn on the VPC attributes **DNS hostnames** and **DNS resolution**."
> "Your VPC must have at least **two subnets**. These subnets must be in **two different Availability Zones**."
> "Your VPC must have a **DB subnet group** that you create."

### 2.5 Minimum Complete CloudFormation YAML for Publicly Accessible RDS

This is the minimum complete VPC setup supporting a publicly accessible RDS instance, derived from AWS documentation guidance:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  DBUsername:
    Type: String
    Default: dbadmin
  DBPassword:
    Type: String
    NoEcho: true

Resources:

  # ─── VPC ───────────────────────────────────────────────────────────────────
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true    # REQUIRED for PubliclyAccessible: true
      EnableDnsSupport: true      # REQUIRED for PubliclyAccessible: true
      Tags:
        - Key: Name
          Value: bancafiel-vpc

  # ─── Internet Gateway ──────────────────────────────────────────────────────
  InternetGateway:
    Type: AWS::EC2::InternetGateway

  VPCGatewayAttachment:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  # ─── Public Subnets (in 2 AZs — required by RDS DB Subnet Group) ──────────
  PublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']
      MapPublicIpOnLaunch: false  # RDS gets public IP via PubliclyAccessible flag
      Tags:
        - Key: Name
          Value: bancafiel-public-subnet-1

  PublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value: bancafiel-public-subnet-2

  # ─── Route Table with IGW Route (makes subnets PUBLIC) ────────────────────
  PublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC

  PublicRoute:
    Type: AWS::EC2::Route
    DependsOn: VPCGatewayAttachment
    Properties:
      RouteTableId: !Ref PublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway   # Route to IGW = public subnet

  PublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet1
      RouteTableId: !Ref PublicRouteTable

  PublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet2
      RouteTableId: !Ref PublicRouteTable

  # ─── DB Subnet Group (requires subnets in 2 AZs) ─────────────────────────
  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Public subnets for RDS
      SubnetIds:
        - !Ref PublicSubnet1
        - !Ref PublicSubnet2

  # ─── Security Group for RDS ───────────────────────────────────────────────
  DBSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Allow PostgreSQL access
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          CidrIp: 0.0.0.0/0   # Restrict to specific IPs/Lambda SG in production

  # ─── RDS PostgreSQL DB Instance ───────────────────────────────────────────
  Database:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.micro
      Engine: postgres
      EngineVersion: "16"
      AllocatedStorage: "20"
      StorageType: gp2
      DBName: bancafiel
      MasterUsername: !Ref DBUsername
      MasterUserPassword: !Ref DBPassword
      DBSubnetGroupName: !Ref DBSubnetGroup
      VPCSecurityGroups:
        - !Ref DBSecurityGroup
      PubliclyAccessible: true   # Requires public subnets + IGW (done above)
      BackupRetentionPeriod: 0   # 0 = no automated backups (safe for free tier)
      MultiAZ: false
      StorageEncrypted: false
      DeletionPolicy: Delete
```

**Key requirements checklist for PubliclyAccessible RDS:**
- [x] VPC with `EnableDnsHostnames: true` and `EnableDnsSupport: true`
- [x] Internet Gateway attached to the VPC
- [x] At least 2 subnets in 2 different Availability Zones
- [x] Both subnets associated with a route table that has `0.0.0.0/0 -> IGW`
- [x] DB Subnet Group referencing those public subnets
- [x] Security Group allowing inbound on port 5432 from desired source CIDRs

---

## Question 3: SAM S3 Event + Lambda Circular Dependency

### 3.1 Does SAM Handle the Circular Dependency?

The SAM `S3` event type uses `Type: S3` with `Bucket: !Ref MyBucket`. From the [SAM S3 event property documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-s3.html):

> "This field only accepts a **reference to the S3 bucket created in this template**"

SAM does handle the S3 event trigger automatically, but there is an important warning from the [official CloudFormation documentation for AWS::S3::Bucket NotificationConfiguration](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-s3-bucket-notificationconfiguration.html):

> "**Note:** If you create the target resource and related permissions in the same template, you might have a **circular dependency**."
>
> "For example, you might use the `AWS::Lambda::Permission` resource to grant the bucket permission to invoke an AWS Lambda function. However, AWS CloudFormation can't create the bucket until the bucket has permission to invoke the function (AWS CloudFormation checks whether the bucket can invoke the function). If you're using Refs to pass the bucket name, this leads to a circular dependency."

**SAM behavior:** When you use `Type: S3` in SAM with `Bucket: !Ref MyBucket`, SAM automatically creates:
1. An `AWS::Lambda::Permission` resource granting S3 permission to invoke the Lambda
2. A `NotificationConfiguration` on the S3 bucket pointing to the Lambda ARN

SAM resolves the circular dependency internally by using a custom resource or specific ordering — BUT if your Lambda's IAM policy also contains `!Ref MyBucket` in the same Resource ARN, the circular dependency can still manifest depending on how CloudFormation orders resource creation.

### 3.2 Recommended Pattern to Avoid Circular Dependencies

The official CloudFormation documentation provides the **authoritative recommendation**:

> "To avoid this dependency, you can create all resources **without specifying the notification configuration**. Then, **update the stack** with a notification configuration."

This is the two-pass deployment approach. However, SAM typically abstracts this away. The practical recommended patterns are:

**Pattern A: Use SAM S3 event (SAM handles ordering internally)**
```yaml
# SAM automatically manages the circular dependency for S3 events
# defined via Events: Type: S3. This is the recommended SAM approach.

MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: index.handler
    Runtime: python3.12
    Policies:
      - S3ReadPolicy:
          BucketName: !Ref MyBucket
    Events:
      S3Event:
        Type: S3
        Properties:
          Bucket: !Ref MyBucket    # SAM resolves dependency ordering
          Events: s3:ObjectCreated:*

MyBucket:
  Type: AWS::S3::Bucket
  # Do NOT put NotificationConfiguration here when using SAM Events
  # SAM will add it automatically
```

**Pattern B: Manual separation (CloudFormation native — two-resource approach)**
When NOT using SAM's built-in S3 event handling, follow the official guidance: define the S3 bucket without `NotificationConfiguration`, then add it via a separate `AWS::CloudFormation::CustomResource` or via stack update.

**Pattern C: Use hardcoded bucket name to break the Ref dependency**
```yaml
# If the bucket name is known in advance, use a fixed name
# instead of !Ref MyBucket in IAM policies:
Policies:
  - Statement:
      - Effect: Allow
        Action: s3:GetObject
        Resource: !Sub "arn:aws:s3:::my-fixed-bucket-name-${AWS::AccountId}/*"
```

**Pattern D: Use EventBridge instead of S3 direct notification**
```yaml
# S3 -> EventBridge -> Lambda avoids the direct S3-Lambda notification circular dep
MyBucket:
  Type: AWS::S3::Bucket
  Properties:
    NotificationConfiguration:
      EventBridgeConfiguration:
        EventBridgeEnabled: true   # No Lambda reference needed in S3 bucket
```

### 3.3 SAM S3 Event Documentation Key Facts

From [sam-property-function-s3](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-s3.html):

```yaml
# SAM S3 Event syntax:
Events:
  S3Event:
    Type: S3
    Properties:
      Bucket: !Ref ImagesBucket   # Must be a bucket declared in the SAME template
      Events: s3:ObjectCreated:*
      Filter:                      # Optional
        S3Key:
          Rules:
          - Name: prefix           # or "suffix"
            Value: uploads/
```

**Warning from Lambda docs** ([Process Amazon S3 event notifications with Lambda](https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html)):

> "If your Lambda function uses the **same bucket** that triggers it, it could cause the function to run in a **loop**. For example, if the bucket triggers a function each time an object is uploaded, and the function uploads an object to the bucket, then the function indirectly triggers itself. **To avoid this, use two buckets**, or configure the trigger to only apply to a prefix used for incoming objects."

---

## Question 4: Lambda (outside VPC) connecting to RDS (inside VPC, PubliclyAccessible: true)

### 4.1 Is This a Supported Pattern?

**Yes, this is a supported pattern.** From the [Scenarios for accessing a DB instance in a VPC](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.Scenarios.html):

The "A DB instance in a VPC accessed by a client application through the internet" scenario explicitly supports any client connecting over the internet to a publicly accessible RDS instance. Lambda functions outside a VPC are effectively internet clients and connect via the public endpoint of the RDS instance.

This is NOT the recommended best practice for production workloads (placing Lambda in the same VPC as RDS is preferred), but it IS a fully supported and functional configuration.

### 4.2 Security Group Configuration Required

When Lambda is OUTSIDE a VPC and RDS is INSIDE a VPC with `PubliclyAccessible: true`, the connection flows over the internet. The RDS security group must have an inbound rule allowing traffic from Lambda's source IP.

**Challenge:** Lambda functions outside a VPC use dynamic IP addresses from AWS's IP ranges. The recommended approaches are:

**Option A: Allow all IPs (for development/testing only)**
```yaml
DBSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: Allow PostgreSQL
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 5432
        ToPort: 5432
        CidrIp: 0.0.0.0/0   # WARNING: Opens to the internet — not for production
```

**Option B: Restrict to AWS IP ranges for the Lambda service (preferred for dev)**

Lambda outside VPC uses AWS-owned IPs. You can download the [AWS IP ranges](https://ip-ranges.amazonaws.com/ip-ranges.json) and filter for `LAMBDA` service in your region, but this list changes frequently.

**Option C (Production Recommended): Place Lambda INSIDE the same VPC**
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    VpcConfig:
      SecurityGroupIds:
        - !Ref LambdaSecurityGroup
      SubnetIds:
        - !Ref PrivateSubnet1    # Lambda in private subnets
        - !Ref PrivateSubnet2
```
Then configure the RDS security group to allow inbound from the Lambda security group:
```yaml
DBSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 5432
        ToPort: 5432
        SourceSecurityGroupId: !Ref LambdaSecurityGroup   # Lambda SG as source
```

### 4.3 SSL/TLS Requirements When Connecting Lambda to RDS PostgreSQL

From [Using SSL with a PostgreSQL DB instance](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.Security.html):

> "By default, RDS for PostgreSQL uses and expects all clients to connect using SSL/TLS, but you can also require it. RDS for PostgreSQL supports Transport Layer Security (TLS) versions 1.1, 1.2, and 1.3."

> "The `rds.force_ssl` parameter default value is **1 (on) for RDS for PostgreSQL version 15 and later**. For all other RDS for PostgreSQL major versions 14 and older, the default value of this parameter is **0 (off)**."

**Key findings:**
- PostgreSQL 15+ has SSL **enforced by default** (`rds.force_ssl = 1`)
- PostgreSQL 14 and earlier: SSL is supported but NOT enforced by default
- AWS creates an SSL certificate for your PostgreSQL DB instance automatically when the instance is created
- To connect using SSL certificate verification, download the RDS CA certificate bundle

**Lambda connection with SSL (Python pg8000/psycopg2 example):**
```python
import ssl
import pg8000

ssl_context = ssl.SSLContext()
ssl_context.verify_mode = ssl.CERT_NONE   # Or CERT_REQUIRED with CA cert

conn = pg8000.connect(
    host=os.environ['DB_HOST'],
    database=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=5432,
    ssl_context=ssl_context
)
```

**For PostgreSQL 15+ (SSL forced):** Lambda must use SSL — non-SSL connections will be rejected with:
```
FATAL: no pg_hba.conf entry for host "x.x.x.x", user "...", database "...", SSL off
```

**Recommendation:** Always connect with SSL from Lambda, regardless of PostgreSQL version. Use `sslmode=require` at minimum.

---

## Question 5: SAM API Gateway + Step Functions Circular Dependency

### 5.1 The Problem

A circular dependency occurs in this pattern:
1. Lambda function has API Gateway events → SAM creates API Gateway
2. Lambda's IAM policy references Step Functions state machine ARN (`!Ref StateMachine` or `!GetAtt StateMachine.Arn`)
3. Step Functions state machine IAM role references Lambda ARNs (`!GetAtt MyFunction.Arn`)
4. Step Functions resource is created in the same template

CloudFormation cannot determine the order: Lambda depends on StateMachine (for IAM policy), but StateMachine depends on Lambda (for IAM role and DefinitionSubstitutions).

### 5.2 Recommended Pattern: DefinitionSubstitutions

The **official AWS-recommended pattern** is documented at [Using AWS SAM to build Step Functions workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-sam-sfn.html):

> "Use **variable substitution** to substitute ARNs into your state machine at the time of deployment."
>
> "AWS CloudFormation supports `DefinitionSubstitutions` that let you add dynamic references in your workflow definition to a value that you provide in your CloudFormation template."

The official example shows using `!GetAtt` references in `DefinitionSubstitutions` for Lambda ARNs. This pattern passes Lambda ARNs into the state machine definition WITHOUT creating a direct CloudFormation dependency from the state machine's `RoleArn` or `Policies` back to Lambda.

**Correct SAM pattern using DefinitionSubstitutions:**
```yaml
Resources:

  # Step 1: Define Lambda functions (no reference to StateMachine)
  ProcessDocumentFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: python3.12
      Policies:
        # Use !Sub with hardcoded partial ARN to break dependency:
        - Statement:
            - Effect: Allow
              Action: states:StartExecution
              # Use Sub with known partial ARN — does NOT create CFN dependency on StateMachine resource
              Resource: !Sub "arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:*"
      Events:
        Api:
          Type: Api
          Properties:
            Path: /process
            Method: post

  # Step 2: Define Step Functions state machine
  # Uses DefinitionSubstitutions to reference Lambda ARNs
  DocumentWorkflow:
    Type: AWS::Serverless::StateMachine
    Properties:
      DefinitionSubstitutions:
        # These references (GetAtt) mean StateMachine depends on Lambda — NOT the reverse
        ProcessDocumentFunctionArn: !GetAtt ProcessDocumentFunction.Arn
      Policies:
        # StateMachine role uses SAM policy template — references Lambda name, not ARN
        - LambdaInvokePolicy:
            FunctionName: !Ref ProcessDocumentFunction
      Definition:
        Comment: Document processing workflow
        StartAt: ProcessDocument
        States:
          ProcessDocument:
            Type: Task
            Resource: arn:aws:states:::lambda:invoke
            Parameters:
              FunctionName: "${ProcessDocumentFunctionArn}"  # Substituted at deploy
            End: true
```

**Why this breaks the circular dependency:**
- `StateMachine` depends on `ProcessDocumentFunction` (via `DefinitionSubstitutions: !GetAtt`)
- `ProcessDocumentFunction` does NOT depend on `StateMachine` (uses `!Sub` wildcard ARN instead of `!Ref StateMachine`)
- CloudFormation can now order: Lambda first → StateMachine second

### 5.3 Is Using `!Sub "arn:aws:states:..."` the Correct Approach?

**Yes — this is the correct approach to break the Lambda → StateMachine dependency.** When a Lambda function's IAM policy must allow `states:StartExecution` on the state machine, using a hardcoded or wildcard ARN via `!Sub` instead of `!Ref StateMachine` or `!GetAtt StateMachine.Arn` prevents CloudFormation from creating a dependency edge between the Lambda resource and the StateMachine resource.

```yaml
# Option A: Wildcard ARN (allows startExecution on all state machines in account/region)
Resource: !Sub "arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:*"

# Option B: Predictable fixed name (if you control the StateMachine name)
Resource: !Sub "arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:DocumentWorkflow"
# Note: If StateMachine has StateMachineName property set to a fixed name,
# this ARN is deterministic and does NOT create a CloudFormation dependency

# Option C: Use Outputs + Parameters (multi-stack approach)
# Deploy StateMachine in Stack 1, export ARN as Output
# Deploy Lambda in Stack 2, import ARN via !ImportValue
```

### 5.4 Step Functions DefinitionSubstitutions Syntax

From [AWS::StepFunctions::StateMachine CloudFormation reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-stepfunctions-statemachine.html):

> "A map (string to string) that specifies the mappings for placeholder variables in the state machine definition. Substitutions must follow the syntax: `${key_name}` or `${variable_1,variable_2,...}`."

```yaml
DocumentWorkflow:
  Type: AWS::Serverless::StateMachine
  Properties:
    DefinitionSubstitutions:
      # Key names used as ${KeyName} in the ASL definition JSON/YAML
      ProcessFunctionArn: !GetAtt ProcessDocumentFunction.Arn
      ExtractFunctionArn: !GetAtt ExtractDataFunction.Arn
      DDBPutItem: !Sub arn:${AWS::Partition}:states:::dynamodb:putItem
      DDBTable: !Ref DocumentsTable
    DefinitionUri: statemachine/document_workflow.asl.json
```

In `statemachine/document_workflow.asl.json`:
```json
{
  "States": {
    "ProcessDocument": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "${ProcessFunctionArn}"
      }
    }
  }
}
```

---

## Summary of Fixes Needed

Based on the research above, here is the exact list of changes required in `template.yaml`:

### Fix 1: RDS BackupRetentionPeriod

**Problem:** Setting `BackupRetentionPeriod` to 7 or more days causes the error "backup retention period exceeds maximum available to free tier customers."

**Fix:**
```yaml
# BEFORE (causes error):
BackupRetentionPeriod: 7

# AFTER:
BackupRetentionPeriod: 0    # Disables automated backups — safe for free tier
```

### Fix 2: RDS StorageEncrypted

**Problem:** Potential issues with encryption on restricted free-tier accounts.

**Fix:**
```yaml
# OPTION A — Safe for free tier (uses AWS managed key, no extra cost):
StorageEncrypted: false     # Simplest approach for free tier dev environment

# OPTION B — Technically supported on db.t3.micro (NOT db.t2.micro):
StorageEncrypted: true
# Do NOT set KmsKeyId — let it use the default aws/rds managed key
```

**Note:** `db.t2.micro` does NOT support encryption. `db.t3.micro` DOES support encryption. Only `db.m1.*`, `db.m2.*`, and `db.t2.micro` are excluded from encryption support.

### Fix 3: RDS EngineVersion

**Problem:** Using an unsupported or deprecated PostgreSQL version string.

**Fix:**
```yaml
# BEFORE (if using old/unsupported version):
EngineVersion: "12.5"   # Example of potentially deprecated version

# AFTER (use currently supported versions on db.t3.micro):
Engine: postgres
EngineVersion: "16"     # PostgreSQL 16 — fully supported on db.t3.micro
                        # All versions 10-17 are supported on db.t3.micro
```

### Fix 4: VPC Setup for PubliclyAccessible RDS

**Problem:** Missing VPC components prevent the RDS instance from being publicly accessible.

**Fix:** Add all required VPC resources to `template.yaml`:
1. Add `EnableDnsHostnames: true` and `EnableDnsSupport: true` to the VPC resource
2. Create an `AWS::EC2::InternetGateway` resource
3. Create an `AWS::EC2::VPCGatewayAttachment` attaching the IGW to the VPC
4. Create an `AWS::EC2::RouteTable` with a route `0.0.0.0/0 → InternetGateway`
5. Associate BOTH DB subnets with this public route table via `AWS::EC2::SubnetRouteTableAssociation`
6. Ensure the `DBSubnetGroup` uses these public subnets

See the complete CloudFormation example in [Question 2.5](#25-minimum-complete-cloudformation-yaml-for-publicly-accessible-rds).

### Fix 5: Lambda → RDS Connection (SSL for PostgreSQL 15+)

**Problem:** If using PostgreSQL 15 or higher, `rds.force_ssl = 1` by default. Lambda connections without SSL will be rejected.

**Fix:** Always connect with SSL from Lambda code. Use `sslmode=require` at minimum in connection strings:
```python
# psycopg2:
conn = psycopg2.connect(
    host=os.environ['DB_HOST'],
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    port=5432,
    sslmode='require'   # Required for PostgreSQL 15+; good practice for all versions
)
```

**Or in template.yaml:** Set `EngineVersion: "14"` or lower (PostgreSQL 14 has `force_ssl = 0` by default).

### Fix 6: SAM S3 Event Circular Dependency

**Problem:** Lambda function using `Events: Type: S3` with `Bucket: !Ref MyBucket` and the Lambda's IAM policy also referencing `!Ref MyBucket` may cause circular dependency in some configurations.

**Fix Option A (preferred — SAM handles it):** Use SAM's built-in S3 event handling. SAM manages the dependency ordering. Do NOT manually add `NotificationConfiguration` to the S3 bucket resource if using SAM S3 events:
```yaml
MyFunction:
  Type: AWS::Serverless::Function
  Properties:
    Events:
      S3Event:
        Type: S3
        Properties:
          Bucket: !Ref MyBucket
          Events: s3:ObjectCreated:*
    Policies:
      - S3ReadPolicy:          # Use SAM policy templates, not raw !Ref in Resource ARN
          BucketName: !Ref MyBucket

MyBucket:
  Type: AWS::S3::Bucket
  # NO NotificationConfiguration here — SAM adds it automatically
```

**Fix Option B (CloudFormation official guidance):** If manual `NotificationConfiguration` is needed, deploy the bucket first WITHOUT the notification, then update the stack to add the notification.

### Fix 7: SAM Step Functions Circular Dependency

**Problem:** Lambda IAM policy using `!Ref StateMachine` or `!GetAtt StateMachine.Arn` creates a circular dependency when Step Functions also references Lambda ARNs.

**Fix:** Replace `!Ref StateMachine` in Lambda IAM policies with `!Sub` wildcard or hardcoded ARN:
```yaml
# BEFORE (causes circular dependency):
Policies:
  - Statement:
      - Effect: Allow
        Action: states:StartExecution
        Resource: !Ref DocumentWorkflowStateMachine   # Creates CFN dependency

# AFTER (breaks circular dependency):
Policies:
  - Statement:
      - Effect: Allow
        Action: states:StartExecution
        Resource: !Sub "arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:*"
```

Use `DefinitionSubstitutions` in the Step Functions state machine to reference Lambda ARNs via `!GetAtt`:
```yaml
DocumentWorkflow:
  Type: AWS::Serverless::StateMachine
  Properties:
    DefinitionSubstitutions:
      MyFunctionArn: !GetAtt MyFunction.Arn   # StateMachine depends on Lambda
    Policies:
      - LambdaInvokePolicy:
          FunctionName: !Ref MyFunction
```

---

## Official AWS Documentation Sources Consulted

| Topic | URL |
|---|---|
| AWS::RDS::DBInstance CloudFormation Reference | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-rds-dbinstance.html |
| Supported DB engines for DB instance classes (db.t3.micro table) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.DBInstanceClass.Support.html |
| Available PostgreSQL database versions | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.DBVersions.html |
| Encrypting Amazon RDS resources (encryption availability table) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.Encryption.html |
| RDS Backup Retention Period | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.BackupRetention.html |
| RDS Quotas and Constraints | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Limits.html |
| Scenarios for accessing a DB instance in a VPC | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.Scenarios.html |
| Working with a DB instance in a VPC | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html |
| Tutorial: Create a VPC for use with a DB instance | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Tutorials.WebServerDB.CreateVPC.html |
| Enable internet access for a VPC using an internet gateway | https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html |
| Troubleshooting for Amazon RDS (internet gateway connectivity) | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html |
| SAM S3 Event Source Property | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-property-function-s3.html |
| AWS::S3::Bucket NotificationConfiguration (circular dependency note) | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-properties-s3-bucket-notificationconfiguration.html |
| Process Amazon S3 event notifications with Lambda | https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html |
| Using SSL with a PostgreSQL DB instance | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.Security.html |
| Using AWS SAM to build Step Functions workflows (DefinitionSubstitutions) | https://docs.aws.amazon.com/step-functions/latest/dg/concepts-sam-sfn.html |
| AWS::Serverless::StateMachine SAM Reference | https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-statemachine.html |
| AWS::StepFunctions::StateMachine CloudFormation Reference | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-stepfunctions-statemachine.html |
| Creating and connecting to a PostgreSQL DB instance | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.PostgreSQL.html |
| Amazon RDS for PostgreSQL overview | https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html |
