from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic Celery tasks for DVA transaction syncing'

    def handle(self, *args, **options):
        # Create interval schedule for every 10 seconds
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.SECONDS,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created interval schedule: Every {schedule.every} {schedule.period}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Interval schedule already exists: Every {schedule.every} {schedule.period}'))

        # Create or update periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name='Sync Pending DVA Transactions',
            defaults={
                'task': 'apps.payments.tasks.sync_pending_dva_transactions',
                'interval': schedule,
                'enabled': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created periodic task: Sync Pending DVA Transactions'))
        else:
            # Update existing task
            task.interval = schedule
            task.enabled = True
            task.save()
            self.stdout.write(self.style.SUCCESS('Updated periodic task: Sync Pending DVA Transactions'))

        self.stdout.write(self.style.SUCCESS('\n✅ Periodic task setup completed!'))
        self.stdout.write(self.style.SUCCESS('Task will run every 10 seconds to sync pending DVA transactions.'))

