# Generated manually to migrate from first_name/last_name to full_name

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add full_name field to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='full_name',
            field=models.CharField(default='', max_length=200),
        ),
        # Add full_name field to CourierProfile
        migrations.AddField(
            model_name='courierprofile',
            name='full_name',
            field=models.CharField(default='', max_length=200),
        ),
        # Migrate data: combine first_name + last_name into full_name
        migrations.RunSQL(
            sql="UPDATE user_profiles SET full_name = TRIM(CONCAT(first_name, ' ', last_name)) WHERE full_name = '';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql="UPDATE courier_profiles SET full_name = TRIM(CONCAT(first_name, ' ', last_name)) WHERE full_name = '';",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Remove old fields
        migrations.RemoveField(
            model_name='userprofile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='courierprofile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='courierprofile',
            name='last_name',
        ),
    ]

