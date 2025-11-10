from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Recuperación de contraseña
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='gym/password_reset.html',
        email_template_name='gym/password_reset_email.html',
        subject_template_name='gym/password_reset_subject.txt',
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='gym/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='gym/password_reset_confirm.html',
        success_url='/password-reset-complete/'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='gym/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Dashboard (diferenciados por tipo de usuario)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/entrenador/', views.dashboard_entrenador, name='dashboard_entrenador'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # Ejercicios
    path('ejercicios/', views.ejercicios_list, name='ejercicios_list'),
    path('ejercicios/<str:ejercicio_id>/', views.ejercicio_detail, name='ejercicio_detail'),
    
    # Rutinas
    path('rutinas/', views.rutinas_list, name='rutinas_list'),
    path('rutinas/crear/', views.rutina_create, name='rutina_create'),
    path('rutinas/<int:rutina_id>/', views.rutina_detail, name='rutina_detail'),
    path('rutinas/<int:rutina_id>/editar/', views.rutina_edit, name='rutina_edit'),
    path('rutinas/<int:rutina_id>/eliminar/', views.rutina_delete, name='rutina_delete'),
    path('rutinas/<int:rutina_id>/agregar/', views.agregar_ejercicio, name='agregar_ejercicio'),
    path('rutinas/<int:rutina_id>/agregar/<str:ejercicio_id>/', views.agregar_ejercicio_detalle, name='agregar_ejercicio_detalle'),
    path('rutinas/<int:rutina_id>/registrar/', views.registrar_entrenamiento, name='registrar_entrenamiento'),
    
    # Progreso
    path('progreso/', views.progreso_view, name='progreso'),
    path('progreso/registrar/', views.registrar_progreso, name='registrar_progreso'),
    
    # Favoritos
    path('favoritos/', views.favoritos_list, name='favoritos'),
    path('favoritos/toggle/<str:ejercicio_id>/', views.toggle_favorito, name='toggle_favorito'),
    
    # Entrenadores
    path('entrenadores/', views.entrenadores_list, name='entrenadores_list'),
    path('entrenadores/<int:perfil_id>/', views.entrenador_detail, name='entrenador_detail'),
    
    # Perfil
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    
    # Entrenadores: Asignar rutinas
    path('rutinas/<int:rutina_id>/asignar/', views.asignar_rutina, name='asignar_rutina'),
    path('mis-clientes/', views.mis_clientes, name='mis_clientes'),
]
