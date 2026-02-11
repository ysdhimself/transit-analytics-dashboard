#!/bin/bash
# Deployment script for AWS Lambda using SAM

set -e

echo "Deploying ETS Transit Analytics Dashboard - Lambda Function"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: AWS SAM CLI not found. Please install it first:"
    echo "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Please install and configure it first."
    exit 1
fi

echo "Building Lambda function..."
sam build

echo "Deploying to AWS..."
sam deploy --guided

echo "Deployment complete!"
echo ""
echo "To test the Lambda function locally:"
echo "  sam local invoke TransitIngestionFunction"
echo ""
echo "To view logs:"
echo "  sam logs -n TransitIngestionFunction --tail"
