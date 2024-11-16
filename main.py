import os
import sys
from src.app.routes import app

if __name__ == '__main__':
    try:
        # Add project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(project_root)
        
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Error running app: {e}") 