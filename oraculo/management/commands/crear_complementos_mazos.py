# oraculo/management/commands/crear_complementos_mazos.py

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from oraculo.models import Mazo, ComplementosMazo


class Command(BaseCommand):
    help = 'Crea registros de ComplementosMazo para todos los mazos existentes que no los tengan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de complementos existentes',
        )
        parser.add_argument(
            '--mazo-id',
            type=int,
            help='Crear complementos solo para un mazo específico por ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la operación sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔮 INICIANDO CREACIÓN DE COMPLEMENTOS PARA MAZOS')
        )
        self.stdout.write('=' * 60)

        # Configurar opciones
        force = options['force']
        mazo_id = options.get('mazo_id')
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  MODO SIMULACIÓN - No se harán cambios reales')
            )

        try:
            # Obtener mazos a procesar
            if mazo_id:
                mazos = Mazo.objects.filter(id=mazo_id)
                if not mazos.exists():
                    raise CommandError(f'No se encontró el mazo con ID {mazo_id}')
                self.stdout.write(f'🎯 Procesando mazo específico: ID {mazo_id}')
            else:
                mazos = Mazo.objects.all().select_related('set')
                self.stdout.write(f'📋 Procesando todos los mazos: {mazos.count()} encontrados')

            # Contadores
            creados = 0
            existentes = 0
            recreados = 0
            errores = 0

            with transaction.atomic():
                for mazo in mazos:
                    try:
                        self.stdout.write(f'\n🃏 Procesando: {mazo.nombre} ({mazo.codigo})')
                        
                        # Verificar si ya existe
                        complementos_exist = hasattr(mazo, 'complementos')
                        
                        if complementos_exist and not force:
                            self.stdout.write(
                                self.style.WARNING(f'   ✓ Ya tiene complementos - saltando')
                            )
                            existentes += 1
                            continue
                        
                        if not dry_run:
                            if force and complementos_exist:
                                # Recrear si se fuerza
                                mazo.complementos.delete()
                                self.stdout.write(
                                    self.style.WARNING(f'   🔄 Eliminando complementos existentes')
                                )
                            
                            # Crear complementos
                            complementos = ComplementosMazo.objects.create(mazo=mazo)
                            
                            if force and complementos_exist:
                                self.stdout.write(
                                    self.style.SUCCESS(f'   ✅ Complementos recreados: ID {complementos.id}')
                                )
                                recreados += 1
                            else:
                                self.stdout.write(
                                    self.style.SUCCESS(f'   ✅ Complementos creados: ID {complementos.id}')
                                )
                                creados += 1
                        else:
                            # Modo simulación
                            if force and complementos_exist:
                                self.stdout.write(
                                    self.style.SUCCESS(f'   🔄 [SIMULACIÓN] Se recrearían complementos')
                                )
                                recreados += 1
                            else:
                                self.stdout.write(
                                    self.style.SUCCESS(f'   ✅ [SIMULACIÓN] Se crearían complementos')
                                )
                                creados += 1

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Error: {str(e)}')
                        )
                        errores += 1
                        continue

            # Resumen final
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE LA OPERACIÓN:'))
            
            if dry_run:
                self.stdout.write(self.style.WARNING('   [MODO SIMULACIÓN]'))
            
            self.stdout.write(f'   ✅ Complementos creados: {creados}')
            if recreados > 0:
                self.stdout.write(f'   🔄 Complementos recreados: {recreados}')
            self.stdout.write(f'   ⚠️  Ya existían: {existentes}')
            if errores > 0:
                self.stdout.write(f'   ❌ Errores: {errores}')
            
            total_procesados = creados + recreados + existentes + errores
            self.stdout.write(f'   📋 Total procesados: {total_procesados}')

            # Verificación final
            if not dry_run:
                total_complementos = ComplementosMazo.objects.count()
                total_mazos = Mazo.objects.count()
                self.stdout.write(f'\n🔍 VERIFICACIÓN:')
                self.stdout.write(f'   Total mazos en BD: {total_mazos}')
                self.stdout.write(f'   Total complementos en BD: {total_complementos}')
                
                if total_complementos >= total_mazos:
                    self.stdout.write(
                        self.style.SUCCESS('   ✅ Todos los mazos tienen complementos')
                    )
                else:
                    faltantes = total_mazos - total_complementos
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Faltan {faltantes} complementos por crear')
                    )

            self.stdout.write('\n' + self.style.SUCCESS('🎉 PROCESO COMPLETADO'))

        except Exception as e:
            raise CommandError(f'Error general en el comando: {str(e)}')

    def mostrar_ayuda(self):
        """Muestra ejemplos de uso del comando"""
        self.stdout.write('\n📖 EJEMPLOS DE USO:')
        self.stdout.write('   # Crear complementos para todos los mazos:')
        self.stdout.write('   python manage.py crear_complementos_mazos')
        self.stdout.write('')
        self.stdout.write('   # Simular sin hacer cambios:')
        self.stdout.write('   python manage.py crear_complementos_mazos --dry-run')
        self.stdout.write('')
        self.stdout.write('   # Crear para un mazo específico:')
        self.stdout.write('   python manage.py crear_complementos_mazos --mazo-id 1')
        self.stdout.write('')
        self.stdout.write('   # Forzar recreación de todos:')
        self.stdout.write('   python manage.py crear_complementos_mazos --force')
        self.stdout.write('')