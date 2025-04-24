#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from dotenv import load_dotenv  # Import dotenv

def main():
    """Run administrative tasks."""
    load_dotenv()  # Load environment variables from the .env file
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'online_learning.settings')
    
    # Get the port from environment variables, default to 8000 if not set
    port = os.getenv("PORT", "8000")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    # Run the Django server on the correct port
    execute_from_command_line([sys.argv[0], "runserver", f"0.0.0.0:{port}"])

if __name__ == '__main__':
    main()
