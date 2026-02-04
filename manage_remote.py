
import os
import sys
import django
from django.conf import settings
from dotenv import load_dotenv

# Load env vars from .env
load_dotenv(override=True)

# Ensure DB settings are present
print(f"Target DB Host: {os.environ.get('DB_HOST', 'Not Set')}")
print(f"Target DB Name: {os.environ.get('DB_NAME', 'Not Set')}")

if not os.environ.get('DB_HOST'):
    print("Error: DB_HOST not found in .env")
    sys.exit(1)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcellar.settings.production')
django.setup()

from django.core.management import call_command

print("\n--- Running Migrations ---")
call_command('migrate')

print("\n--- Running Seeding ---")
try:
    # Append current directory to path
    sys.path.append(os.getcwd())
    
    print("Running Marketplace Seed...")
    from seed_marketplace import seed_marketplace
    seed_marketplace()
    
    print("\nRunning Admin Seed...")
    from seed_admins import seed_admins
    seed_admins()
    
except ImportError as e:
    print(f"Error importing seed script: {e}")
except Exception as e:
    print(f"Error seeding: {e}")

print("\n--- Done ---")
