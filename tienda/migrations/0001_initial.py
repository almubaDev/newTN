# Generated by Django 5.2.1 on 2025-05-28 19:53

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('oraculo', '0003_alter_carta_imagen_alter_carta_significado_invertido_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TarotProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precio', models.DecimalField(decimal_places=2, help_text='Precio del producto en la moneda local', max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio')),
                ('precio_oferta', models.DecimalField(blank=True, decimal_places=2, help_text='Precio con descuento (opcional)', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Precio de Oferta')),
                ('link_compra', models.URLField(help_text='URL donde se procesa el pago del producto', max_length=500, verbose_name='Link de Compra')),
                ('descripcion_adicional', models.TextField(blank=True, help_text='Información extra sobre el producto (opcional)', verbose_name='Descripción Adicional')),
                ('estado', models.CharField(choices=[('activo', 'Activo'), ('inactivo', 'Inactivo'), ('agotado', 'Agotado'), ('proximamente', 'Próximamente')], default='activo', max_length=20, verbose_name='Estado del Producto')),
                ('destacado', models.BooleanField(default=False, help_text='Marcar para mostrar en la sección de destacados', verbose_name='Producto Destacado')),
                ('orden', models.PositiveIntegerField(default=0, help_text='Número para ordenar productos (menor número aparece primero)', verbose_name='Orden de Aparición')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('mazo', models.OneToOneField(help_text='Mazo que se vende en este producto', on_delete=django.db.models.deletion.CASCADE, related_name='producto', to='oraculo.mazo', verbose_name='Mazo asociado')),
            ],
            options={
                'verbose_name': 'Producto de Tarot',
                'verbose_name_plural': 'Productos de Tarot',
                'ordering': ['orden', '-destacado', '-fecha_creacion'],
            },
        ),
    ]
