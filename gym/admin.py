from django.contrib import admin
from .models import PerfilUsuario, Ejercicio, Rutina, DetalleRutina, RegistroEntrenamiento, ProgresoFisico, Favorito


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['user', 'tipo_usuario', 'nivel_experiencia', 'disponible', 'activo']
    list_filter = ['tipo_usuario', 'nivel_experiencia', 'activo', 'disponible']
    search_fields = ['user__username', 'user__email', 'especialidad']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user', 'tipo_usuario', 'activo')
        }),
        ('Información Personal', {
            'fields': ('foto_perfil', 'telefono', 'fecha_nacimiento', 'altura', 'peso_actual')
        }),
        ('Fitness', {
            'fields': ('nivel_experiencia', 'objetivo')
        }),
        ('Entrenador', {
            'fields': ('certificacion', 'especialidad', 'anos_experiencia', 'biografia', 'horario', 'disponible', 'capacidad_clientes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'equipamiento', 'nivel_riesgo']
    list_filter = ['nivel_riesgo', 'equipamiento']
    search_fields = ['nombre', 'musculos_principales']


@admin.register(Rutina)
class RutinaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'usuario', 'dificultad', 'duracion_min', 'activa']
    list_filter = ['dificultad', 'activa', 'es_publica']
    search_fields = ['nombre', 'usuario__username']


@admin.register(DetalleRutina)
class DetalleRutinaAdmin(admin.ModelAdmin):
    list_display = ['rutina', 'ejercicio', 'orden', 'series', 'repeticiones']


@admin.register(RegistroEntrenamiento)
class RegistroEntrenamientoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rutina', 'fecha', 'duracion_min', 'nivel_esfuerzo']
    list_filter = ['completado', 'fecha']
    date_hierarchy = 'fecha'


@admin.register(ProgresoFisico)
class ProgresoFisicoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha', 'peso', 'grasa_corporal']
    date_hierarchy = 'fecha'


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ejercicio', 'rutina', 'fecha']
