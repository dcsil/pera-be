# Generated by Django 5.1.7 on 2025-03-29 16:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Passage',
            fields=[
                ('passage_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('language', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('difficulty', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.userprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Sentence',
            fields=[
                ('sentence_id', models.BigAutoField(primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('completion_status', models.BooleanField(null=True)),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('passage_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='texts.passage')),
            ],
        ),
    ]
