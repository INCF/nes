# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiment', '0009_auto_20160428_1446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datafile',
            name='file_format_description',
            field=models.TextField(null=True, default='', blank=True),
        ),
    ]
