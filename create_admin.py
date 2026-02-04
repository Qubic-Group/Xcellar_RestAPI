#!/usr/bin/env python
"""
Script to create an admin (superuser) on the remote database.
Run with: python create_admin.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcellar.settings.production')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

ADMIN_EMAIL = 'admin@xcellar.com'
ADMIN_PASSWORD = 'XcellarAdmin2026!'
ADMIN_PHONE = '+2348000000001'


def create_admin():
    if User.objects.filter(email=ADMIN_EMAIL).exists():
        print(f"Admin user '{ADMIN_EMAIL}' already exists.")
        return
    
    user = User.objects.create_superuser(
        email=ADMIN_EMAIL,
        phone_number=ADMIN_PHONE,
        password=ADMIN_PASSWORD,
    )
    print(f"Admin user created successfully!")
    print(f"  Email: {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print(f"  Phone: {ADMIN_PHONE}")


if __name__ == '__main__':
    create_admin()
