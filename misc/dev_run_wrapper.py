import os
import sys

# Ensure the root directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the mock script BEFORE anything else
import mock_heavy_libs

# Import the real app
from app import app

# Add a redirect for convenience
@app.route('/')
def index_redirect():
    from flask import redirect
    return redirect('/indi-allsky/')
