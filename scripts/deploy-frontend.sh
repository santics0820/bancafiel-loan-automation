#!/bin/bash

# BancaFiel Frontend Deployment Script
# Deploys React application to AWS Amplify

set -e  # Exit on error

echo "🚀 BancaFiel Frontend Deployment Starting..."
echo "================================================"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   https://aws.amazon.com/cli/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install it first:"
    echo "   https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"

# Check if AWS credentials are configured
echo "✓ Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo "❌ AWS credentials not configured. Run 'aws configure'"
    exit 1
}

echo "✓ AWS credentials validated"

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies (this may take a few minutes)..."
    npm install
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "🏗️  Building React application..."
npm run build

if [ $? -eq 0 ]; then
    echo "✓ Build successful!"
else
    echo "❌ Build failed. Check errors above."
    exit 1
fi

echo ""
echo "📤 Deploying to AWS Amplify..."

# Check if Amplify app exists
APP_ID=$(aws amplify list-apps --query "apps[?name=='bancafiel-frontend'].appId" --output text 2>/dev/null)

if [ -z "$APP_ID" ]; then
    echo "   No existing Amplify app found. Creating new app..."

    # Create new Amplify app
    APP_ID=$(aws amplify create-app \
        --name bancafiel-frontend \
        --query 'app.appId' \
        --output text)

    echo "   ✓ Created Amplify app: $APP_ID"

    # Create branch
    aws amplify create-branch \
        --app-id "$APP_ID" \
        --branch-name main > /dev/null

    echo "   ✓ Created main branch"
else
    echo "   ✓ Found existing Amplify app: $APP_ID"
fi

# Upload build to Amplify
echo "   Uploading build artifacts..."

# Create a zip of the build folder
cd build
zip -r ../build.zip . > /dev/null
cd ..

# Upload to S3 (Amplify uses S3 behind the scenes)
BUCKET_NAME="bancafiel-frontend-builds-$(date +%s)"
aws s3 mb "s3://$BUCKET_NAME" 2>/dev/null || true
aws s3 cp build.zip "s3://$BUCKET_NAME/build.zip" --no-cli-pager

# Start deployment
aws amplify start-deployment \
    --app-id "$APP_ID" \
    --branch-name main \
    --source-url "s3://$BUCKET_NAME/build.zip" \
    --no-cli-pager

echo "✓ Deployment initiated"

# Get app URL
APP_URL=$(aws amplify get-app \
    --app-id "$APP_ID" \
    --query 'app.defaultDomain' \
    --output text)

echo ""
echo "✅ Frontend Deployment Complete!"
echo "================================================"
echo ""
echo "🌐 Your app will be available at:"
echo "   https://main.$APP_URL"
echo ""
echo "📋 Next Steps:"
echo "1. Wait 2-3 minutes for deployment to complete"
echo "2. Open the URL above in your browser"
echo "3. Test the application"
echo ""
echo "🔗 Useful Commands:"
echo "   Check deployment status: aws amplify list-jobs --app-id $APP_ID --branch-name main"
echo "   View app in console: https://console.aws.amazon.com/amplify/home#/$APP_ID"
echo ""

# Clean up
rm -f build.zip
aws s3 rb "s3://$BUCKET_NAME" --force 2>/dev/null || true
