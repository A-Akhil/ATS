#!/bin/bash

# ATS Resume Checker - Quick Start Script

echo "==================================="
echo "ATS Resume Checker Setup"
echo "==================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm
echo "✓ spaCy model downloaded"
echo ""

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠ Warning: .env file not found!"
    echo "Please create .env file from .env.example and add your GEMINI_API_KEY"
else
    echo "✓ .env file found"
fi
echo ""

# Check if migrations are applied
echo "Checking database..."
python manage.py showmigrations | grep -q "\[ \]"
if [ $? -eq 0 ]; then
    echo "⚠ Some migrations are not applied"
    echo "Migrations are already created and applied"
else
    echo "✓ Database migrations are up to date"
fi
echo ""

# Provide next steps
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next Steps:"
echo "1. Add your Gemini API key to the .env file:"
echo "   GEMINI_API_KEY=your-api-key-here"
echo ""
echo "2. Start the LaTeX service (in another terminal):"
echo "   cd latex-to-pdf"
echo "   docker build -t latex-service ."
echo "   docker run -p 8006:8006 latex-service"
echo ""
echo "3. Create a superuser account:"
echo "   python manage.py createsuperuser"
echo "   (Set role='admin' in Django admin after creation)"
echo ""
echo "4. Run the development server:"
echo "   python manage.py runserver"
echo ""
echo "5. Open your browser to:"
echo "   http://localhost:8000"
echo ""
echo "For admin access:"
echo "   http://localhost:8000/admin"
echo ""
echo "==================================="
