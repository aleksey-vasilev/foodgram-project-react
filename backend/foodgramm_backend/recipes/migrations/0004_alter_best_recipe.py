# Generated by Django 3.2.3 on 2023-12-09 07:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0003_auto_20231209_1236'),
    ]

    operations = [
        migrations.AlterField(
            model_name='best',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='in_favorited', to='recipes.recipe'),
        ),
    ]
