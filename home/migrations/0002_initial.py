# Generated by Django 5.1.6 on 2025-03-14 12:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('home', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='bannedmember',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='channel',
            name='banned_users',
            field=models.ManyToManyField(blank=True, related_name='banned_channels', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='channel',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_channels', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='bannedmember',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banned_members', to='home.channel'),
        ),
        migrations.AddField(
            model_name='channelmember',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='home.channel'),
        ),
        migrations.AddField(
            model_name='channelmember',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='channelmessage',
            name='channel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='home.channel'),
        ),
        migrations.AddField(
            model_name='channelmessage',
            name='sender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
