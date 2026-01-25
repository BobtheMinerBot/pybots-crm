#!/bin/bash
# ISLA CRM Deployment Script for PythonAnywhere
# Run this after uploading files to PythonAnywhere

echo "🏗️  ISLA CRM Deployment"
echo "======================="

# Set your PythonAnywhere username
PA_USER="${PA_USER:-YOUR_USERNAME}"
PROJECT_DIR="/home/$PA_USER/isla-crm/dashboard"

echo ""
echo "1. Setting up virtual environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

echo ""
echo "2. Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "3. Creating config directory..."
mkdir -p ~/.config/jobtread

echo ""
echo "4. Testing Flask app..."
python -c "from app import app; print('✅ Flask app loads successfully')"

echo ""
echo "======================="
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Go to Web tab in PythonAnywhere"
echo "2. Create new web app (Manual config, Python 3.10)"
echo "3. Set WSGI file (see DEPLOYMENT.md)"
echo "4. Set virtualenv path: $PROJECT_DIR/venv"
echo "5. Add static files mapping: /static/ → $PROJECT_DIR/static"
echo "6. Reload and visit your site!"
echo ""
