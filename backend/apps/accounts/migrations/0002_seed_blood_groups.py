from django.db import migrations

BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


def seed_blood_groups(apps, schema_editor):
    BloodGroup = apps.get_model('accounts', 'BloodGroup')
    for name in BLOOD_GROUPS:
        BloodGroup.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_blood_groups, migrations.RunPython.noop),
    ]
