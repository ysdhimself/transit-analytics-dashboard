#!/bin/bash
# Quick start script for transit analytics dashboard

set -e

echo "🚌 Edmonton Transit Analytics Dashboard - Quick Start"
echo "======================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your AWS credentials"
fi

# Run tests
echo ""
echo "Running tests..."
pytest tests/ -v

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your AWS credentials (if deploying to AWS)"
echo "2. Run the dashboard locally with mock data:"
echo "   streamlit run dashboard/app.py"
echo ""
echo "3. Or test GTFS-RT parsing:"
echo "   python -m src.ingestion.gtfs_rt_parser"
echo ""
echo "4. See SETUP_GUIDE.md for AWS deployment instructions"
