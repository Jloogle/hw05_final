# Generated by Django 2.2.16 on 2022-01-29 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0017_auto_20220128_2244'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
        ),
    ]
