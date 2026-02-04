from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a superuser admin account'

    def handle(self, *args, **options):
        User = get_user_model()
        
        admin_email = 'admin@xcellar.com'
        admin_password = 'XcellarAdmin2026!'
        admin_phone = '+2348000000001'
        
        if User.objects.filter(email=admin_email).exists():
            self.stdout.write(self.style.WARNING(f"Admin '{admin_email}' already exists."))
            return
        
        User.objects.create_superuser(
            email=admin_email,
            phone_number=admin_phone,
            password=admin_password,
        )
        
        self.stdout.write(self.style.SUCCESS(f"Admin created successfully!"))
        self.stdout.write(f"  Email: {admin_email}")
        self.stdout.write(f"  Password: {admin_password}")
