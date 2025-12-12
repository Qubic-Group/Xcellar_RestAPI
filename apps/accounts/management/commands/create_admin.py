from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a Django admin superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@xcellar.com',
            help='Admin email address'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='+2340000000000',
            help='Admin phone number'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Admin password (will prompt if not provided)'
        )
        parser.add_argument(
            '--user-type',
            type=str,
            default='USER',
            choices=['USER', 'COURIER'],
            help='User type (default: USER)'
        )

    def handle(self, *args, **options):
        email = options['email']
        phone_number = options['phone']
        password = options['password']
        user_type = options['user_type']

        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists.')
            )
            return

        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('Passwords do not match.')
                )
                return

        try:
            user = User.objects.create_superuser(
                email=email,
                phone_number=phone_number,
                password=password,
                user_type=user_type
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created superuser: {email}'
                )
            )
            self.stdout.write(
                f'Access admin at: http://localhost:8000/admin/'
            )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )

