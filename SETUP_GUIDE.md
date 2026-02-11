# Complete Setup Guide

This guide walks you through setting up the Edmonton Transit Analytics Dashboard from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Data Collection](#data-collection)
5. [Model Training](#model-training)
6. [Dashboard Deployment](#dashboard-deployment)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

- **AWS Account** (Free Tier eligible)
  - Sign up: https://aws.amazon.com/free/
  - Note: Some services require credit card verification

- **GitHub Account**
  - Sign up: https://github.com/join

- **Streamlit Cloud Account** (optional, for dashboard hosting)
  - Sign up: https://streamlit.io/cloud

### Required Software

```bash
# Python 3.11 or higher
python --version  # Should show 3.11.x

# Git
git --version

# AWS CLI (for deployment)
# Install: https://aws.amazon.com/cli/
aws --version

# AWS SAM CLI (optional, for SAM deployment)
# Install: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
sam --version
```

---

## Local Development Setup

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/transit-analytics-dashboard.git
cd transit-analytics-dashboard

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
# On Windows:
notepad .env
# On macOS/Linux:
nano .env
```

**Minimal `.env` for local testing (no AWS required):**
```bash
# Leave AWS credentials empty for local mock data testing
GTFS_RT_VEHICLE_POSITIONS_URL=https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/Vehicle/VehiclePositions.pb
GTFS_RT_TRIP_UPDATES_URL=https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/TripUpdate/TripUpdates.pb
GTFS_STATIC_ZIP_URL=https://gtfs.edmonton.ca/TMGTFSRealTimeWebService/GTFS/gtfs.zip
```

### Step 3: Test Components

```bash
# Test static GTFS loader
python -m src.processing.static_gtfs_loader

# Test GTFS-RT parser (fetches live data)
python -m src.ingestion.gtfs_rt_parser

# Test data quality validator
python -m src.ingestion.data_quality

# Run all tests
pytest tests/ -v
```

### Step 4: Launch Dashboard (Local with Mock Data)

```bash
streamlit run dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501` with mock data.

---

## AWS Infrastructure Setup

### Step 1: Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: [Your key]
# AWS Secret Access Key: [Your secret]
# Default region name: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### Step 2: Create S3 Bucket

```bash
# Create bucket for raw data storage
aws s3 mb s3://ets-transit-data --region us-east-1

# Verify creation
aws s3 ls
```

### Step 3: Create DynamoDB Table

```bash
# Create table with on-demand billing (free tier eligible)
aws dynamodb create-table \
  --table-name ets_transit_processed \
  --attribute-definitions \
    AttributeName=pk,AttributeType=S \
    AttributeName=sk,AttributeType=S \
  --key-schema \
    AttributeName=pk,KeyType=HASH \
    AttributeName=sk,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Verify creation
aws dynamodb list-tables
```

### Step 4: Deploy Lambda Function

**Option A: Using SAM (Recommended)**

```bash
# Build
sam build

# Deploy with guided setup
sam deploy --guided

# Follow prompts:
# Stack Name: ets-transit-analytics
# AWS Region: us-east-1
# Confirm changes: Y
# Allow SAM CLI IAM role creation: Y
# Save arguments to config: Y
```

**Option B: Manual ZIP deployment**

```bash
# Package dependencies
mkdir lambda_package
pip install -r requirements-lambda.txt -t lambda_package/
cp -r src lambda_package/

# Create ZIP
cd lambda_package
zip -r ../lambda_deployment.zip .
cd ..

# Create Lambda function
aws lambda create-function \
  --function-name ETS-Transit-Ingestion \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler src.ingestion.lambda_handler.handler \
  --zip-file fileb://lambda_deployment.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables="{S3_BUCKET_NAME=ets-transit-data,DYNAMODB_TABLE_NAME=ets_transit_processed}"

# Create EventBridge rule for scheduling
aws events put-rule \
  --name ets-transit-ingestion-schedule \
  --schedule-expression "rate(1 minute)"

# Add Lambda permission for EventBridge
aws lambda add-permission \
  --function-name ETS-Transit-Ingestion \
  --statement-id AllowEventBridgeInvoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com

# Create target
aws events put-targets \
  --rule ets-transit-ingestion-schedule \
  --targets "Id"="1","Arn"="arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ETS-Transit-Ingestion"
```

### Step 5: Verify Lambda Execution

```bash
# Invoke Lambda manually
aws lambda invoke \
  --function-name ETS-Transit-Ingestion \
  --payload '{}' \
  response.json

# View response
cat response.json

# Check CloudWatch logs
aws logs tail /aws/lambda/ETS-Transit-Ingestion --follow
```

---

## Data Collection

### Wait for Data Accumulation

The Lambda function will run every minute, collecting:
- ~1,440 snapshots per day
- ~50-100 vehicle positions per snapshot
- ~500-1000 trip updates per snapshot

**Recommended collection period:** 2-7 days before training ML model.

### Monitor Data Collection

```bash
# Check S3 bucket size
aws s3 ls s3://ets-transit-data/transit/ --recursive --summarize

# Check DynamoDB item count
aws dynamodb scan \
  --table-name ets_transit_processed \
  --select "COUNT"

# View sample records
aws dynamodb scan \
  --table-name ets_transit_processed \
  --limit 5
```

---

## Model Training

### Step 1: Export Data from DynamoDB

```python
# Create a script: export_data.py
import boto3
import pandas as pd

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ets_transit_processed')

# Scan trip updates
response = table.scan(
    FilterExpression='record_type = :type',
    ExpressionAttributeValues={':type': 'trip_update'}
)

items = response['Items']
df = pd.DataFrame(items)
df.to_csv('trip_updates_raw.csv', index=False)
print(f"Exported {len(df)} records")
```

```bash
python export_data.py
```

### Step 2: Process and Engineer Features

```python
# Create script: prepare_training_data.py
import pandas as pd
from src.processing.static_gtfs_loader import load_static_schedule
from src.processing.delay_calculator import DelayCalculator
from src.processing.feature_engineer import FeatureEngineer

# Load static schedule
schedule = load_static_schedule()

# Load trip updates
trip_updates_df = pd.read_csv('trip_updates_raw.csv')

# Calculate delays
calculator = DelayCalculator(schedule)
delays_df = calculator.merge_realtime_with_schedule(
    calculator.calculate_delay_from_trip_updates(trip_updates_df.to_dict('records'))
)

# Engineer features
engineer = FeatureEngineer()
features_df = engineer.create_feature_set(delays_df)

# Save
features_df.to_csv('features_for_training.csv', index=False)
print(f"Prepared {len(features_df)} training samples")
```

```bash
python prepare_training_data.py
```

### Step 3: Train Model

```python
# Create script: train.py
from src.ml.train_model import DelayPredictor

feature_cols = [
    'hour_of_day',
    'day_of_week',
    'is_weekend',
    'is_rush_hour',
    'route_id_encoded',
    'stop_sequence'
]

trainer = DelayPredictor(model_type='random_forest')
metrics = trainer.train_and_evaluate(
    pd.read_csv('features_for_training.csv'),
    feature_cols
)

print(f"Model trained! R² score: {metrics['r2_score']:.4f}")
```

```bash
python train.py
```

The trained model will be saved to `src/ml/model_artifacts/delay_model.joblib`.

---

## Dashboard Deployment

### Option 1: Streamlit Cloud (Recommended)

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file path: `dashboard/app.py`
   - Click "Advanced settings" → "Secrets"
   - Add your secrets in TOML format:
     ```toml
     [aws]
     AWS_ACCESS_KEY_ID = "your_key"
     AWS_SECRET_ACCESS_KEY = "your_secret"
     AWS_DEFAULT_REGION = "us-east-1"
     S3_BUCKET_NAME = "ets-transit-data"
     DYNAMODB_TABLE_NAME = "ets_transit_processed"
     ```
   - Click "Deploy"

3. **Your dashboard will be live at:** `https://your-app.streamlit.app`

### Option 2: Local/Server Deployment

```bash
# Run with production settings
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Troubleshooting

### Issue: "AWS credentials not found"

**Solution:**
```bash
# Re-configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: "Lambda timeout"

**Solution:**
```bash
# Increase Lambda timeout (max 15 minutes)
aws lambda update-function-configuration \
  --function-name ETS-Transit-Ingestion \
  --timeout 120
```

### Issue: "DynamoDB throughput exceeded"

**Solution:**
DynamoDB on-demand mode should handle any reasonable load. If issues persist:
```bash
# Switch to provisioned mode with auto-scaling
aws dynamodb update-table \
  --table-name ets_transit_processed \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=10,WriteCapacityUnits=10
```

### Issue: "Streamlit dashboard showing 'No data'"

**Solution:**
1. Check if Lambda is running: `aws lambda invoke --function-name ETS-Transit-Ingestion test.json`
2. Check DynamoDB has data: `aws dynamodb scan --table-name ets_transit_processed --limit 1`
3. Verify dashboard can connect to AWS (check secrets configuration)

### Issue: "GTFS-RT feed returns 404"

**Solution:**
Edmonton's GTFS-RT feeds are sometimes temporarily unavailable. Wait 5-10 minutes and try again.

---

## Next Steps

- Set up GitHub Actions for CI/CD (already configured in `.github/workflows/deploy.yml`)
- Add more ML features (weather integration)
- Implement alerting (email/Slack notifications for delays)
- Create custom Streamlit theme
- Add user authentication

---

## Support

For issues or questions:
1. Check the [main README](README.md)
2. Review [troubleshooting](#troubleshooting)
3. Open an issue on GitHub
4. Contact: your.email@example.com
