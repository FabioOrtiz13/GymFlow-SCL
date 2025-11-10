from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver


class PerfilUsuario(models.Model):
    """Perfil extendido del usuario"""
    TIPO_CHOICES = [
        ('usuario', 'Usuario'),
        ('entrenador', 'Entrenador'),
        ('administrador', 'Administrador'),
    ]
    
    NIVEL_CHOICES = [
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_CHOICES, default='usuario')
    foto_perfil = models.URLField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='cm')
    peso_actual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='kg')
    nivel_experiencia = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='principiante')
    objetivo = models.TextField(blank=True)
    
    # Para entrenadores
    certificacion = models.CharField(max_length=200, blank=True)
    especialidad = models.CharField(max_length=200, blank=True)
    anos_experiencia = models.IntegerField(null=True, blank=True)
    biografia = models.TextField(blank=True)
    horario = models.TextField(blank=True, help_text='Horarios de atención del entrenador')
    disponible = models.BooleanField(default=True)
    capacidad_clientes = models.IntegerField(default=20)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
    
    def __str__(self):
        return f"{self.user.username} ({self.get_tipo_usuario_display()})"
    
    def es_entrenador(self):
        return self.tipo_usuario == 'entrenador'
    
    def es_admin(self):
        return self.tipo_usuario == 'administrador'


class Ejercicio(models.Model):
    """Ejercicios de ExerciseDB"""
    NIVEL_RIESGO = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
    ]
    
    # Datos de ExerciseDB
    ejercicio_id = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    imagen_url = models.URLField(blank=True)
    gif_url = models.URLField(blank=True)  # GIF animado (preferido)
    video_url = models.URLField(blank=True)  # Video (alternativo)
    equipamiento = models.TextField(blank=True)
    partes_cuerpo = models.TextField(blank=True)
    musculos_principales = models.TextField(blank=True)
    musculos_secundarios = models.TextField(blank=True)
    descripcion = models.TextField(blank=True)
    instrucciones = models.TextField(blank=True)
    consejos = models.TextField(blank=True)
    variaciones = models.TextField(blank=True)
    
    # Seguridad
    nivel_riesgo = models.CharField(max_length=20, choices=NIVEL_RIESGO, default='bajo')
    advertencias = models.TextField(blank=True)
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ejercicio'
        verbose_name_plural = 'Ejercicios'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_youtube_url(self):
        """Convierte embed URL a watch URL para YouTube"""
        if self.video_url and 'youtube.com/embed/' in self.video_url:
            video_id = self.video_url.split('/embed/')[-1].split('?')[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        return self.video_url


class Rutina(models.Model):
    """Rutinas personalizadas"""
    DIFICULTAD = [
        ('facil', 'Fácil'),
        ('intermedio', 'Intermedio'),
        ('dificil', 'Difícil'),
    ]
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rutinas')
    entrenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rutinas_asignadas')
    dificultad = models.CharField(max_length=20, choices=DIFICULTAD, default='intermedio')
    duracion_min = models.IntegerField(default=60, help_text='Minutos')
    objetivo = models.TextField(blank=True)
    es_publica = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rutina'
        verbose_name_plural = 'Rutinas'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.usuario.username}"
    
    def total_ejercicios(self):
        return self.detalles.count()


class DetalleRutina(models.Model):
    """Ejercicios dentro de una rutina"""
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, related_name='detalles')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE)
    orden = models.IntegerField(default=1)
    series = models.IntegerField(default=3)
    repeticiones = models.IntegerField(default=10)
    peso = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    descanso_seg = models.IntegerField(default=60)
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Detalle de Rutina'
        verbose_name_plural = 'Detalles de Rutinas'
        ordering = ['rutina', 'orden']
    
    def __str__(self):
        return f"{self.rutina.nombre} - {self.ejercicio.nombre}"


class RegistroEntrenamiento(models.Model):
    """Entrenamientos completados"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entrenamientos')
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    duracion_min = models.IntegerField(null=True, blank=True)
    calorias = models.IntegerField(null=True, blank=True)
    nivel_esfuerzo = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=5)
    notas = models.TextField(blank=True)
    completado = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Registro de Entrenamiento'
        verbose_name_plural = 'Registros de Entrenamientos'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.rutina.nombre} - {self.fecha.strftime('%d/%m/%Y')}"


class ProgresoFisico(models.Model):
    """Progreso físico del usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progreso')
    fecha = models.DateField(auto_now_add=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2)
    grasa_corporal = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    masa_muscular = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cintura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    pecho = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    brazos = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    piernas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    foto = models.URLField(blank=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Progreso Físico'
        verbose_name_plural = 'Progreso Físico'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.fecha} - {self.peso}kg"


class Favorito(models.Model):
    """Favoritos del usuario"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    ejercicio = models.ForeignKey(Ejercicio, on_delete=models.CASCADE, null=True, blank=True)
    rutina = models.ForeignKey(Rutina, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Favorito'
        verbose_name_plural = 'Favoritos'
    
    def __str__(self):
        if self.ejercicio:
            return f"{self.usuario.username} - {self.ejercicio.nombre}"
        return f"{self.usuario.username} - {self.rutina.nombre}"


# Signal para crear perfil automáticamente
@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)
