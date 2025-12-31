#!/bin/bash

echo "=================================="
echo "LSCP Setup Script"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
cd backend
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
echo "This may take several minutes..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
cd ..
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set LLAMA_MODEL_PATH to your model file!"
    echo "   Example: LLAMA_MODEL_PATH=/Users/yourname/models/llama-2-7b.Q4_K_M.gguf"
fi

# Create data directory
echo ""
echo "Creating data directory..."
mkdir -p data/vectors

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and set LLAMA_MODEL_PATH"
echo "2. Activate the virtual environment: cd backend && source venv/bin/activate"
echo "3. Run a test scan: python main.py --scan 'time'"
echo "4. Or start the server: python main.py --server"
echo ""
