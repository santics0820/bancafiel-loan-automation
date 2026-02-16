#!/bin/bash

# BancaFiel Backend Deployment Script
# Deploys Lambda functions, RDS, Step Functions, and API Gateway to AWS

set -e  # Exit on error

echo "🚀 BancaFiel Backend Deployment Starting..."
echo "================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

# Check if user is authenticated
echo "✓ Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo "❌ AWS credentials not configured. Run 'aws configure'"
    exit 1
}

echo "✓ AWS credentials validated"

# Load environment variables
if [ -f "../.env" ]; then
    echo "✓ Loading environment variables..."
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo "❌ .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Set AWS region
AWS_REGION=${AWS_REGION:-us-east-1}
echo "✓ Using AWS region: $AWS_REGION"

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

echo ""
echo "📦 Step 1: Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "🏗️  Step 2: Building Lambda deployment packages..."

# Create deployment packages for each Lambda
LAMBDAS=("document-processor" "fraud-detector" "credit-scorer" "notification-sender")

for lambda in "${LAMBDAS[@]}"; do
    echo "   Building $lambda..."
    cd "src/lambdas/$lambda"

    # Create deployment package
    zip -r "function.zip" . -x "*.pyc" "*.git*" > /dev/null

    cd ../../..
done

echo "✓ Lambda packages created"

echo ""
echo "☁️  Step 3: Deploying infrastructure with CloudFormation..."

# Deploy CloudFormation stacks
aws cloudformation deploy \
    --template-file infrastructure/cloudformation/lambda.yaml \
    --stack-name bancafiel-lambdas \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION \
    --no-fail-on-empty-changeset

aws cloudformation deploy \
    --template-file infrastructure/cloudformation/rds.yaml \
    --stack-name bancafiel-rds \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION \
    --no-fail-on-empty-changeset

aws cloudformation deploy \
    --template-file infrastructure/cloudformation/step-functions.yaml \
    --stack-name bancafiel-step-functions \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION \
    --no-fail-on-empty-changeset

echo "✓ Infrastructure deployed"

echo ""
echo "📤 Step 4: Uploading Lambda functions..."

for lambda in "${LAMBDAS[@]}"; do
    echo "   Uploading $lambda..."

    # Get function name from CloudFormation outputs
    FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name bancafiel-lambdas \
        --query "Stacks[0].Outputs[?OutputKey=='${lambda}FunctionName'].OutputValue" \
        --output text \
        --region $AWS_REGION)

    # Update function code
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://src/lambdas/$lambda/function.zip" \
        --region $AWS_REGION \
        --no-cli-pager > /dev/null
done

echo "✓ Lambda functions uploaded"

echo ""
echo "🗄️  Step 5: Setting up database..."

# Get RDS endpoint
RDS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name bancafiel-rds \
    --query 'Stacks[0].Outputs[?OutputKey==`RDSEndpoint`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo "   RDS Endpoint: $RDS_ENDPOINT"
echo "   ⚠️  Note: You need to manually run database migrations:"
echo "   psql -h $RDS_ENDPOINT -U postgres -d bancafiel_loans -f src/database/schema.sql"

echo ""
echo "✅ Backend Deployment Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo "1. Run database migrations (see note above)"
echo "2. Test API Gateway endpoints"
echo "3. Deploy frontend with ./deploy-frontend.sh"
echo ""
echo "🔗 Useful Commands:"
echo "   View Lambda logs: aws logs tail /aws/lambda/[function-name] --follow"
echo "   Test API: curl \$API_GATEWAY_URL/health"
echo ""
