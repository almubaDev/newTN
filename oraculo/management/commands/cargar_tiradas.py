# oraculo/management/commands/cargar_tiradas.py

import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.files import File
from oraculo.models import Tirada, Mazo


class Command(BaseCommand):
    help = 'Carga tiradas desde archivos JSON con sus configuraciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--archivo',
            type=str,
            help='Archivo JSON específico para cargar',
        )
        parser.add_argument(
            '--directorio',
            type=str,
            default='oraculo/data/tiradas/',
            help='Directorio donde buscar archivos JSON de tiradas',
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Fuerza la recreación de tiradas existentes',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la operación sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔮 INICIANDO CARGA DE TIRADAS')
        )
        self.stdout.write('=' * 60)

        archivo = options.get('archivo')
        directorio = options.get('directorio')
        forzar = options['forzar']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  MODO SIMULACIÓN - No se harán cambios reales')
            )

        try:
            if archivo:
                # Cargar archivo específico
                archivos = [archivo]
            else:
                # Buscar todos los JSON en el directorio
                if not os.path.exists(directorio):
                    raise CommandError(f'El directorio {directorio} no existe')
                
                archivos = [
                    os.path.join(directorio, f) 
                    for f in os.listdir(directorio) 
                    if f.endswith('.json')
                ]
                
                if not archivos:
                    raise CommandError(f'No se encontraron archivos JSON en {directorio}')

            # Contadores
            creadas = 0
            actualizadas = 0
            errores = 0

            with transaction.atomic():
                for archivo_json in archivos:
                    try:
                        self.stdout.write(f'\n📁 Procesando: {archivo_json}')
                        
                        # Cargar y validar JSON
                        tirada_data = self.cargar_json(archivo_json)
                        
                        # Procesar tirada
                        if not dry_run:
                            resultado = self.crear_tirada(tirada_data, forzar)
                            if resultado['creada']:
                                creadas += 1
                                self.stdout.write(
                                    self.style.SUCCESS(f'   ✅ Tirada creada: {resultado["nombre"]}')
                                )
                            elif resultado['actualizada']:
                                actualizadas += 1
                                self.stdout.write(
                                    self.style.WARNING(f'   🔄 Tirada actualizada: {resultado["nombre"]}')
                                )
                            else:
                                self.stdout.write(
                                    self.style.ERROR(f'   ⚠️  Tirada ya existe: {resultado["nombre"]}')
                                )
                        else:
                            # Modo simulación
                            self.stdout.write(
                                self.style.SUCCESS(f'   ✅ [SIMULACIÓN] Tirada: {tirada_data["nombre"]}')
                            )
                            creadas += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Error procesando {archivo_json}: {str(e)}')
                        )
                        errores += 1
                        continue

            # Resumen final
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE LA OPERACIÓN:'))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('   [MODO SIMULACIÓN]'))
            
            self.stdout.write(f'   ✅ Tiradas creadas: {creadas}')
            self.stdout.write(f'   🔄 Tiradas actualizadas: {actualizadas}')
            if errores > 0:
                self.stdout.write(f'   ❌ Errores: {errores}')
            
            total_procesadas = creadas + actualizadas + errores
            self.stdout.write(f'   📋 Total procesadas: {total_procesadas}')

            self.stdout.write('\n' + self.style.SUCCESS('🎉 PROCESO COMPLETADO'))

        except Exception as e:
            raise CommandError(f'Error general en el comando: {str(e)}')

    def cargar_json(self, archivo_path):
        """Carga y valida un archivo JSON de tirada"""
        try:
            with open(archivo_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar estructura requerida
            campos_requeridos = ['nombre', 'mazo_codigo', 'posiciones']
            for campo in campos_requeridos:
                if campo not in data:
                    raise ValueError(f'Campo requerido faltante: {campo}')
            
            # Validar posiciones
            if not isinstance(data['posiciones'], dict):
                raise ValueError('Las posiciones deben ser un objeto JSON')
            
            if not data['posiciones']:
                raise ValueError('Debe haber al menos una posición definida')
            
            # Validar cada posición
            for pos_num, pos_data in data['posiciones'].items():
                try:
                    int(pos_num)  # Verificar que sea numérico
                except ValueError:
                    raise ValueError(f'La posición {pos_num} debe ser un número')
                
                if not isinstance(pos_data, dict):
                    raise ValueError(f'Los datos de la posición {pos_num} deben ser un objeto')
                
                if 'nombre' not in pos_data or 'descripcion' not in pos_data:
                    raise ValueError(f'La posición {pos_num} debe tener "nombre" y "descripcion"')
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f'Error al parsear JSON: {str(e)}')
        except FileNotFoundError:
            raise ValueError(f'Archivo no encontrado: {archivo_path}')

    def crear_tirada(self, tirada_data, forzar=False):
        """Crea o actualiza una tirada basada en los datos JSON"""
        nombre = tirada_data['nombre']
        mazo_codigo = tirada_data['mazo_codigo']
        
        # Buscar mazo
        try:
            mazo = Mazo.objects.get(codigo=mazo_codigo)
        except Mazo.DoesNotExist:
            raise ValueError(f'Mazo con código {mazo_codigo} no encontrado')
        
        # Verificar si ya existe
        tirada_existente = Tirada.objects.filter(
            nombre=nombre, 
            mazo=mazo
        ).first()
        
        if tirada_existente and not forzar:
            return {
                'creada': False,
                'actualizada': False,
                'nombre': nombre
            }
        
        # Crear o actualizar tirada
        if tirada_existente and forzar:
            # Actualizar existente
            tirada = tirada_existente
            tirada.posiciones = tirada_data['posiciones']
            tirada.permite_invertidas = tirada_data.get('permite_invertidas', True)
            tirada.descripcion = tirada_data.get('descripcion', '')
            tirada.activa = tirada_data.get('activa', True)
            
            # Actualizar imagen si se proporciona
            imagen_path = tirada_data.get('imagen_mesa')
            if imagen_path and os.path.exists(imagen_path):
                with open(imagen_path, 'rb') as img_file:
                    tirada.imagen_mesa.save(
                        os.path.basename(imagen_path),
                        File(img_file),
                        save=False
                    )
            
            tirada.save()
            
            return {
                'creada': False,
                'actualizada': True,
                'nombre': nombre
            }
        else:
            # Crear nueva
            tirada = Tirada(
                nombre=nombre,
                mazo=mazo,
                posiciones=tirada_data['posiciones'],
                permite_invertidas=tirada_data.get('permite_invertidas', True),
                descripcion=tirada_data.get('descripcion', ''),
                activa=tirada_data.get('activa', True)
            )
            
            # Agregar imagen si se proporciona
            imagen_path = tirada_data.get('imagen_mesa')
            if imagen_path and os.path.exists(imagen_path):
                with open(imagen_path, 'rb') as img_file:
                    tirada.imagen_mesa.save(
                        os.path.basename(imagen_path),
                        File(img_file),
                        save=False
                    )
            
            tirada.save()
            
            return {
                'creada': True,
                'actualizada': False,
                'nombre': nombre
            }

    def mostrar_ayuda(self):
        """Muestra ejemplos de uso del comando"""
        self.stdout.write('\n📖 EJEMPLOS DE USO:')
        self.stdout.write('   # Cargar todas las tiradas del directorio:')
        self.stdout.write('   python manage.py cargar_tiradas')
        self.stdout.write('')
        self.stdout.write('   # Cargar archivo específico:')
        self.stdout.write('   python manage.py cargar_tiradas --archivo tirada_tiempo.json')
        self.stdout.write('')
        self.stdout.write('   # Simular sin hacer cambios:')
        self.stdout.write('   python manage.py cargar_tiradas --dry-run')
        self.stdout.write('')
        self.stdout.write('   # Forzar actualización de existentes:')
        self.stdout.write('   python manage.py cargar_tiradas --forzar')
        
        
# python manage.py cargar_tiradas

# # 2. Cargar archivo específico
# python manage.py cargar_tiradas --archivo oraculo/data/tiradas/tirada_del_tiempo.json

# # 3. Simular carga sin hacer cambios
# python manage.py cargar_tiradas --dry-run

# # 4. Forzar actualización de tiradas existentes
# python manage.py cargar_tiradas --forzar

# # 5. Cargar desde directorio personalizado
# python manage.py cargar_tiradas --directorio mi_directorio/tiradas/