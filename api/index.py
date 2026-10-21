import sys
import os

# Ensure the root project directory is on sys.path so app can import modules and find folders
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

# Vercel WSGI entry point
# Expose `app` for Vercel's Python runtime
if __name__ == '__main__':
    app.run(debug=True)
