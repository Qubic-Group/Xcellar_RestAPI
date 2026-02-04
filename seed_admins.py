
import os
import django
from django.conf import settings

def seed_admins():
    print("Starting admin seeding...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admins = [
        ('admin1@xcellar.com', 'admin123', '+2347000000001'),
        ('admin2@xcellar.com', 'admin123', '+2347000000002')
    ]
    
    for email, password, phone in admins:
        if not User.objects.filter(email=email).exists():
            print(f"Creating superuser {email}...")
            try:
                User.objects.create_superuser(
                    email=email,
                    password=password,
                    phone_number=phone,
                    user_type='USER'
                )
                print(f"Successfully created {email}")
            except Exception as e:
                print(f"Failed to create {email}: {e}")
        else:
            print(f"Superuser {email} already exists.")

if __name__ == "__main__":
    import sys
    if 'django' not in sys.modules:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xcellar.settings.production')
        django.setup()
    seed_admins()
