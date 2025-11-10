from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import Ejercicio, Rutina, DetalleRutina, RegistroEntrenamiento, ProgresoFisico, Favorito, PerfilUsuario
from .exercisedb_service import ExerciseDBService
from .forms import RegistroForm, RutinaForm, DetalleRutinaForm, ProgresoForm, PerfilForm


# ============ AUTENTICACIÓN ============

def login_view(request):
    """Login con redirección según tipo de usuario"""
    if request.user.is_authenticated:
        # Redirigir según tipo de usuario
        return _redirect_por_tipo_usuario(request.user)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # IMPORTANTE: Verificar y crear perfil si no existe
            try:
                perfil = user.perfil
            except PerfilUsuario.DoesNotExist:
                # Crear perfil si no existe
                perfil = PerfilUsuario.objects.create(
                    user=user,
                    tipo_usuario='usuario'
                )
                messages.info(request, 'Se ha creado tu perfil automáticamente.')
            
            # Mensaje personalizado según tipo de usuario
            tipo = perfil.get_tipo_usuario_display()
            emoji = _get_emoji_tipo_usuario(perfil.tipo_usuario)
            messages.success(request, f'¡Bienvenido {emoji} {user.username}! ({tipo})')
            
            # Redirigir según tipo de usuario
            return _redirect_por_tipo_usuario(user)
        else:
            # Mostrar errores del formulario
            messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = AuthenticationForm()
    
    return render(request, 'gym/login.html', {'form': form})


def _redirect_por_tipo_usuario(user):
    """Redirige según el tipo de usuario"""
    try:
        tipo = user.perfil.tipo_usuario
    except PerfilUsuario.DoesNotExist:
        # Si no tiene perfil, crearlo y redirigir a dashboard normal
        PerfilUsuario.objects.create(user=user, tipo_usuario='usuario')
        return redirect('dashboard')
    
    if tipo == 'administrador':
        return redirect('dashboard_admin')
    elif tipo == 'entrenador':
        return redirect('dashboard_entrenador')
    else:  # usuario normal
        return redirect('dashboard')


def _get_emoji_tipo_usuario(tipo):
    """Retorna emoji según tipo de usuario"""
    emojis = {
        'usuario': '💪',
        'entrenador': '👨‍🏫',
        'administrador': '👑',
    }
    return emojis.get(tipo, '💪')


def registro_view(request):
    """Registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # El perfil se crea automáticamente por el signal
                login(request, user)
                messages.success(request, '¡Cuenta creada! Bienvenido a GymFlow.')
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f'Error al crear cuenta: {str(e)}')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroForm()
    
    return render(request, 'gym/register.html', {'form': form})


def logout_view(request):
    """Logout"""
    logout(request)
    messages.info(request, 'Sesión cerrada.')
    return redirect('login')


# ============ DASHBOARD ============

@login_required
def dashboard(request):
    """Dashboard principal - USUARIOS normales"""
    # Si no es usuario normal, redirigir a su dashboard
    if request.user.perfil.tipo_usuario != 'usuario':
        return _redirect_por_tipo_usuario(request.user)
    
    total_rutinas = Rutina.objects.filter(usuario=request.user).count()
    total_entrenamientos = RegistroEntrenamiento.objects.filter(usuario=request.user).count()
    rutinas_recientes = Rutina.objects.filter(usuario=request.user, activa=True)[:5]
    entrenamientos_recientes = RegistroEntrenamiento.objects.filter(usuario=request.user)[:5]
    favoritos_count = Favorito.objects.filter(usuario=request.user).count()
    
    # Progreso más reciente
    ultimo_progreso = ProgresoFisico.objects.filter(usuario=request.user).first()
    
    context = {
        'total_rutinas': total_rutinas,
        'total_entrenamientos': total_entrenamientos,
        'favoritos_count': favoritos_count,
        'rutinas_recientes': rutinas_recientes,
        'entrenamientos_recientes': entrenamientos_recientes,
        'ultimo_progreso': ultimo_progreso,
    }
    
    return render(request, 'gym/dashboard.html', context)


@login_required
def dashboard_entrenador(request):
    """Dashboard para ENTRENADORES"""
    # Verificar que sea entrenador
    if not request.user.perfil.es_entrenador():
        messages.error(request, 'Acceso denegado: Solo para entrenadores')
        return redirect('dashboard')
    
    # Estadísticas del entrenador
    mis_rutinas = Rutina.objects.filter(usuario=request.user)
    rutinas_asignadas = Rutina.objects.filter(entrenador=request.user)
    
    # Clientes únicos
    clientes = User.objects.filter(
        rutinas__entrenador=request.user
    ).distinct()
    
    # Rutinas recientes creadas
    rutinas_recientes = mis_rutinas.order_by('-fecha_creacion')[:5]
    
    # Últimas asignaciones
    ultimas_asignaciones = rutinas_asignadas.order_by('-fecha_creacion')[:5]
    
    context = {
        'total_rutinas_creadas': mis_rutinas.count(),
        'total_rutinas_asignadas': rutinas_asignadas.count(),
        'total_clientes': clientes.count(),
        'rutinas_recientes': rutinas_recientes,
        'ultimas_asignaciones': ultimas_asignaciones,
        'clientes': clientes[:5],  # Primeros 5 clientes
    }
    
    return render(request, 'gym/dashboard_entrenador.html', context)


@login_required
def dashboard_admin(request):
    """Dashboard para ADMINISTRADORES"""
    # Verificar que sea admin
    if not request.user.perfil.es_admin():
        messages.error(request, 'Acceso denegado: Solo para administradores')
        return redirect('dashboard')
    
    # Estadísticas generales del sistema
    total_usuarios = User.objects.filter(perfil__tipo_usuario='usuario').count()
    total_entrenadores = User.objects.filter(perfil__tipo_usuario='entrenador').count()
    total_rutinas = Rutina.objects.all().count()
    total_ejercicios = Ejercicio.objects.all().count()
    total_entrenamientos = RegistroEntrenamiento.objects.all().count()
    
    # Usuarios recientes
    usuarios_recientes = User.objects.order_by('-date_joined')[:5]
    
    # Rutinas más populares (más entrenamientos registrados)
    rutinas_populares = Rutina.objects.annotate(
        num_entrenamientos=Count('registroentrenamiento')
    ).order_by('-num_entrenamientos')[:5]
    
    # Entrenadores más activos
    entrenadores_activos = User.objects.filter(
        perfil__tipo_usuario='entrenador'
    ).annotate(
        num_rutinas_asignadas=Count('rutinas_asignadas')
    ).order_by('-num_rutinas_asignadas')[:5]
    
    context = {
        'total_usuarios': total_usuarios,
        'total_entrenadores': total_entrenadores,
        'total_rutinas': total_rutinas,
        'total_ejercicios': total_ejercicios,
        'total_entrenamientos': total_entrenamientos,
        'usuarios_recientes': usuarios_recientes,
        'rutinas_populares': rutinas_populares,
        'entrenadores_activos': entrenadores_activos,
    }
    
    return render(request, 'gym/dashboard_admin.html', context)


# ============ EJERCICIOS (ExerciseDB API) ============

@login_required
def ejercicios_list(request):
    """Lista de ejercicios desde ExerciseDB API con filtros por zona"""
    query = request.GET.get('q', '')
    zona = request.GET.get('zona', '')  # Filtro por zona muscular
    
    # Obtener todos los ejercicios
    if query:
        ejercicios = ExerciseDBService.search_exercises(query)
    else:
        # Solicitar 100 ejercicios comunes de gym (optimizado)
        ejercicios = ExerciseDBService.get_all_exercises(limit=100)
    
    # Filtrar por zona si está seleccionada
    if zona:
        # Mapeo de zonas español -> inglés para filtrado
        zona_map = {
            'pecho': ['chest', 'pecho'],
            'piernas': ['legs', 'upper legs', 'lower legs', 'piernas'],
            'espalda': ['back', 'espalda'],
            'hombros': ['shoulders', 'hombros'],
            'brazos': ['arms', 'upper arms', 'lower arms', 'brazos'],
            'core': ['waist', 'core', 'abs']
        }
        
        # Obtener términos de búsqueda para la zona seleccionada
        zona_lower = zona.lower()
        terminos_busqueda = zona_map.get(zona_lower, [zona_lower])
        
        # Filtrar ejercicios que contengan alguno de los términos
        ejercicios = [
            e for e in ejercicios 
            if any(termino in e.get('bodyParts', '').lower() for termino in terminos_busqueda)
        ]
    
    # Favoritos del usuario
    favoritos_ids = Favorito.objects.filter(
        usuario=request.user, 
        ejercicio__isnull=False
    ).values_list('ejercicio__ejercicio_id', flat=True)
    
    # Zonas disponibles para filtrar
    zonas = ['Pecho', 'Piernas', 'Espalda', 'Hombros', 'Brazos', 'Core']
    
    context = {
        'ejercicios': ejercicios,
        'query': query,
        'zona': zona,
        'zonas': zonas,
        'favoritos_ids': list(favoritos_ids),
        'total_ejercicios': len(ejercicios),
    }
    
    return render(request, 'gym/ejercicios.html', context)


@login_required
def ejercicio_detail(request, ejercicio_id):
    """Detalle de ejercicio"""
    # Obtener de ExerciseDB API
    ejercicio_data = ExerciseDBService.get_exercise_by_id(ejercicio_id)
    
    if not ejercicio_data:
        messages.error(request, 'Ejercicio no encontrado')
        return redirect('ejercicios_list')
    
    # Guardar en BD si no existe
    ejercicio, created = Ejercicio.objects.get_or_create(
        ejercicio_id=ejercicio_id,
        defaults={
            'nombre': ejercicio_data['name'],
            'imagen_url': ejercicio_data.get('imageUrl', ''),
            'gif_url': ejercicio_data.get('gifUrl', ''),  # GIF animado
            'video_url': ejercicio_data.get('videoUrl', ''),
            'equipamiento': ejercicio_data.get('equipments', ''),
            'partes_cuerpo': ejercicio_data.get('bodyParts', ''),
            'musculos_principales': ejercicio_data.get('targetMuscles', ''),
            'musculos_secundarios': ejercicio_data.get('secondaryMuscles', ''),
            'descripcion': ejercicio_data.get('overview', ''),
        }
    )
    
    # Verificar si es favorito
    es_favorito = Favorito.objects.filter(usuario=request.user, ejercicio=ejercicio).exists()
    
    context = {
        'ejercicio': ejercicio,
        'ejercicio_data': ejercicio_data,
        'es_favorito': es_favorito,
    }
    
    return render(request, 'gym/ejercicio_detail.html', context)


# ============ RUTINAS ============

@login_required
def rutinas_list(request):
    """Lista de rutinas del usuario"""
    rutinas = Rutina.objects.filter(usuario=request.user).annotate(num_ejercicios=Count('detalles'))
    
    filtro = request.GET.get('filtro', 'todas')
    if filtro == 'activas':
        rutinas = rutinas.filter(activa=True)
    elif filtro == 'inactivas':
        rutinas = rutinas.filter(activa=False)
    
    context = {
        'rutinas': rutinas,
        'filtro': filtro,
    }
    
    return render(request, 'gym/rutinas.html', context)


@login_required
def rutina_detail(request, rutina_id):
    """Detalle de rutina"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    detalles = DetalleRutina.objects.filter(rutina=rutina).select_related('ejercicio').order_by('orden')
    
    context = {
        'rutina': rutina,
        'detalles': detalles,
    }
    
    return render(request, 'gym/rutina_detail.html', context)


@login_required
def rutina_create(request):
    """Crear rutina - SOLO para entrenadores y admins"""
    # Verificar que sea entrenador o admin
    if not (request.user.perfil.es_entrenador() or request.user.perfil.es_admin()):
        messages.error(request, '⛔ Solo los entrenadores y administradores pueden crear rutinas.')
        return redirect('rutinas_list')
    
    if request.method == 'POST':
        form = RutinaForm(request.POST)
        if form.is_valid():
            rutina = form.save(commit=False)
            rutina.usuario = request.user
            rutina.save()
            messages.success(request, '✅ Rutina creada exitosamente!')
            return redirect('rutina_detail', rutina_id=rutina.id)
    else:
        form = RutinaForm()
    
    return render(request, 'gym/rutina_form.html', {'form': form, 'action': 'Crear'})


@login_required
def rutina_edit(request, rutina_id):
    """Editar rutina - SOLO para entrenadores y admins"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    
    # Verificar que sea entrenador o admin
    if not (request.user.perfil.es_entrenador() or request.user.perfil.es_admin()):
        messages.error(request, '⛔ Solo los entrenadores y administradores pueden editar rutinas.')
        return redirect('rutina_detail', rutina_id=rutina.id)
    
    if request.method == 'POST':
        form = RutinaForm(request.POST, instance=rutina)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Rutina actualizada!')
            return redirect('rutina_detail', rutina_id=rutina.id)
    else:
        form = RutinaForm(instance=rutina)
    
    return render(request, 'gym/rutina_form.html', {'form': form, 'action': 'Editar', 'rutina': rutina})


@login_required
def rutina_delete(request, rutina_id):
    """Eliminar rutina - SOLO para entrenadores y admins"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    
    # Verificar que sea entrenador o admin
    if not (request.user.perfil.es_entrenador() or request.user.perfil.es_admin()):
        messages.error(request, '⛔ Solo los entrenadores y administradores pueden eliminar rutinas.')
        return redirect('rutina_detail', rutina_id=rutina.id)
    
    if request.method == 'POST':
        rutina.delete()
        messages.success(request, '✅ Rutina eliminada')
        return redirect('rutinas_list')
    
    return render(request, 'gym/rutina_confirm_delete.html', {'rutina': rutina})


@login_required
def agregar_ejercicio(request, rutina_id):
    """Buscar ejercicios de la API para agregar a rutina"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    
    # Verificar que sea entrenador o admin
    if not (request.user.perfil.es_entrenador() or request.user.perfil.es_admin()):
        messages.error(request, '⛔ Solo los entrenadores y administradores pueden modificar rutinas.')
        return redirect('rutina_detail', rutina_id=rutina.id)
    
    # Búsqueda de ejercicios
    query = request.GET.get('q', '')
    zona = request.GET.get('zona', '')
    
    if query or zona:
        # Obtener ejercicios de la API
        if query:
            ejercicios = ExerciseDBService.search_exercises(query)
        else:
            ejercicios = ExerciseDBService.get_all_exercises(limit=150)
        
        # Filtrar por zona si está seleccionada
        if zona:
            ejercicios = [e for e in ejercicios if zona.lower() in e.get('bodyParts', '').lower()]
    else:
        ejercicios = ExerciseDBService.get_all_exercises(limit=100)
    
    # Zonas disponibles
    zonas = ['Pecho', 'Piernas', 'Espalda', 'Hombros', 'Brazos', 'Core']
    
    context = {
        'rutina': rutina,
        'ejercicios': ejercicios,
        'query': query,
        'zona': zona,
        'zonas': zonas,
        'total_ejercicios': len(ejercicios),
    }
    
    return render(request, 'gym/agregar_ejercicio.html', context)


@login_required
def agregar_ejercicio_detalle(request, rutina_id, ejercicio_id):
    """Agregar ejercicio a rutina con detalles (series, reps, etc.)"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    
    # Verificar que sea entrenador o admin
    if not (request.user.perfil.es_entrenador() or request.user.perfil.es_admin()):
        messages.error(request, '⛔ Solo los entrenadores y administradores pueden modificar rutinas.')
        return redirect('rutina_detail', rutina_id=rutina.id)
    
    # Obtener ejercicio de la API
    ejercicio_data = ExerciseDBService.get_exercise_by_id(ejercicio_id)
    
    if not ejercicio_data:
        messages.error(request, 'Ejercicio no encontrado')
        return redirect('agregar_ejercicio', rutina_id=rutina.id)
    
    # Guardar ejercicio en BD si no existe
    ejercicio, created = Ejercicio.objects.get_or_create(
        ejercicio_id=ejercicio_id,
        defaults={
            'nombre': ejercicio_data['name'],
            'imagen_url': ejercicio_data.get('imageUrl', ''),
            'gif_url': ejercicio_data.get('gifUrl', ''),
            'video_url': ejercicio_data.get('videoUrl', ''),
            'equipamiento': ejercicio_data.get('equipments', ''),
            'partes_cuerpo': ejercicio_data.get('bodyParts', ''),
            'musculos_principales': ejercicio_data.get('targetMuscles', ''),
            'musculos_secundarios': ejercicio_data.get('secondaryMuscles', ''),
            'descripcion': ejercicio_data.get('overview', ''),
        }
    )
    
    if request.method == 'POST':
        # Obtener datos del formulario
        orden = request.POST.get('orden', 1)
        series = request.POST.get('series', 3)
        repeticiones = request.POST.get('repeticiones', 10)
        peso = request.POST.get('peso', '')
        descanso_seg = request.POST.get('descanso_seg', 60)
        notas = request.POST.get('notas', '')
        
        # Crear detalle de rutina
        DetalleRutina.objects.create(
            rutina=rutina,
            ejercicio=ejercicio,
            orden=orden,
            series=series,
            repeticiones=repeticiones,
            peso=peso if peso else None,
            descanso_seg=descanso_seg,
            notas=notas
        )
        
        messages.success(request, f'✅ Ejercicio "{ejercicio.nombre}" agregado a la rutina!')
        return redirect('rutina_detail', rutina_id=rutina.id)
    
    # Calcular siguiente orden
    ultimo_orden = DetalleRutina.objects.filter(rutina=rutina).count() + 1
    
    context = {
        'rutina': rutina,
        'ejercicio': ejercicio,
        'ejercicio_data': ejercicio_data,
        'orden_sugerido': ultimo_orden,
    }
    
    return render(request, 'gym/agregar_ejercicio_detalle.html', context)


# ============ ENTRENAMIENTOS ============

@login_required
def registrar_entrenamiento(request, rutina_id):
    """Registrar entrenamiento completado"""
    rutina = get_object_or_404(Rutina, id=rutina_id, usuario=request.user)
    
    if request.method == 'POST':
        duracion = request.POST.get('duracion')
        esfuerzo = request.POST.get('esfuerzo', 5)
        notas = request.POST.get('notas', '')
        
        RegistroEntrenamiento.objects.create(
            usuario=request.user,
            rutina=rutina,
            duracion_min=duracion if duracion else None,
            nivel_esfuerzo=esfuerzo,
            notas=notas
        )
        
        messages.success(request, '¡Entrenamiento registrado!')
        return redirect('dashboard')
    
    return render(request, 'gym/registrar_entrenamiento.html', {'rutina': rutina})


# ============ PROGRESO ============

@login_required
def progreso_view(request):
    """Ver progreso físico"""
    registros = ProgresoFisico.objects.filter(usuario=request.user).order_by('-fecha')[:10]
    
    context = {
        'registros': registros,
    }
    
    return render(request, 'gym/progreso.html', context)


@login_required
def registrar_progreso(request):
    """Registrar progreso físico"""
    if request.method == 'POST':
        form = ProgresoForm(request.POST)
        if form.is_valid():
            progreso = form.save(commit=False)
            progreso.usuario = request.user
            progreso.save()
            messages.success(request, 'Progreso registrado!')
            return redirect('progreso')
    else:
        form = ProgresoForm()
    
    return render(request, 'gym/registrar_progreso.html', {'form': form})


# ============ FAVORITOS ============

@login_required
def toggle_favorito(request, ejercicio_id):
    """Agregar/quitar favorito"""
    # Obtener o crear ejercicio en BD
    ejercicio_data = ExerciseDBService.get_exercise_by_id(ejercicio_id)
    
    if ejercicio_data:
        ejercicio, _ = Ejercicio.objects.get_or_create(
            ejercicio_id=ejercicio_id,
            defaults={'nombre': ejercicio_data['name']}
        )
        
        favorito = Favorito.objects.filter(usuario=request.user, ejercicio=ejercicio).first()
        
        if favorito:
            favorito.delete()
            messages.info(request, 'Eliminado de favoritos')
        else:
            Favorito.objects.create(usuario=request.user, ejercicio=ejercicio)
            messages.success(request, '¡Agregado a favoritos!')
    
    return redirect('ejercicio_detail', ejercicio_id=ejercicio_id)


@login_required
def favoritos_list(request):
    """Lista de favoritos"""
    favoritos = Favorito.objects.filter(usuario=request.user).select_related('ejercicio', 'rutina')
    
    return render(request, 'gym/favoritos.html', {'favoritos': favoritos})


# ============ ENTRENADORES ============

@login_required
def entrenadores_list(request):
    """Lista de entrenadores disponibles"""
    entrenadores = PerfilUsuario.objects.filter(
        tipo_usuario='entrenador',
        activo=True
    ).select_related('user')
    
    return render(request, 'gym/entrenadores.html', {'entrenadores': entrenadores})


@login_required
def entrenador_detail(request, perfil_id):
    """Detalle de entrenador"""
    entrenador = get_object_or_404(PerfilUsuario, id=perfil_id, tipo_usuario='entrenador')
    
    return render(request, 'gym/entrenador_detail.html', {'entrenador': entrenador})


# ============ PERFIL ============

@login_required
def mi_perfil(request):
    """Ver y editar perfil"""
    perfil = request.user.perfil
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado!')
            return redirect('mi_perfil')
    else:
        form = PerfilForm(instance=perfil)
    
    return render(request, 'gym/perfil.html', {'form': form, 'perfil': perfil})


# ============ ENTRENADOR: ASIGNAR RUTINAS ============

@login_required
def asignar_rutina(request, rutina_id):
    """Asignar rutina a un usuario (solo entrenadores)"""
    rutina = get_object_or_404(Rutina, id=rutina_id)
    
    # Verificar que el usuario sea entrenador
    if not request.user.perfil.es_entrenador():
        messages.error(request, 'Solo los entrenadores pueden asignar rutinas')
        return redirect('dashboard')
    
    # Verificar que la rutina sea del entrenador
    if rutina.usuario != request.user:
        messages.error(request, 'Solo puedes asignar tus propias rutinas')
        return redirect('rutinas_list')
    
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        try:
            usuario_destino = User.objects.get(id=usuario_id)
            
            # Crear copia de la rutina para el usuario
            nueva_rutina = Rutina.objects.create(
                nombre=f"{rutina.nombre} (de {request.user.username})",
                descripcion=rutina.descripcion,
                usuario=usuario_destino,
                entrenador=request.user,
                dificultad=rutina.dificultad,
                duracion_min=rutina.duracion_min,
                objetivo=rutina.objetivo,
                es_publica=False,
                activa=True
            )
            
            # Copiar todos los ejercicios
            for detalle in rutina.detalles.all():
                DetalleRutina.objects.create(
                    rutina=nueva_rutina,
                    ejercicio=detalle.ejercicio,
                    orden=detalle.orden,
                    series=detalle.series,
                    repeticiones=detalle.repeticiones,
                    peso=detalle.peso,
                    descanso_seg=detalle.descanso_seg,
                    notas=detalle.notas
                )
            
            messages.success(request, f'Rutina asignada a {usuario_destino.username} exitosamente!')
            return redirect('rutinas_list')
            
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
    
    # Obtener lista de usuarios (clientes)
    usuarios = User.objects.filter(
        perfil__tipo_usuario='usuario',
        perfil__activo=True
    ).exclude(id=request.user.id)
    
    context = {
        'rutina': rutina,
        'usuarios': usuarios,
    }
    
    return render(request, 'gym/asignar_rutina.html', context)


@login_required
def mis_clientes(request):
    """Ver clientes del entrenador (rutinas asignadas)"""
    if not request.user.perfil.es_entrenador():
        messages.error(request, 'Solo los entrenadores pueden ver esta página')
        return redirect('dashboard')
    
    # Obtener usuarios que tienen rutinas asignadas por este entrenador
    rutinas_asignadas = Rutina.objects.filter(
        entrenador=request.user
    ).select_related('usuario').order_by('-fecha_creacion')
    
    # Agrupar por usuario
    clientes_dict = {}
    for rutina in rutinas_asignadas:
        if rutina.usuario not in clientes_dict:
            clientes_dict[rutina.usuario] = []
        clientes_dict[rutina.usuario].append(rutina)
    
    context = {
        'clientes': clientes_dict,
        'total_clientes': len(clientes_dict),
        'total_rutinas': rutinas_asignadas.count(),
    }
    
    return render(request, 'gym/mis_clientes.html', context)