# Generated by Django 2.1.5 on 2019-01-09 04:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_auto_20190108_2342'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='inventoryCount',
            new_name='productInventory',
        ),
    ]
