# 🏋️ GymFlow

**Sistema de Gestión de Entrenamiento para Gimnasios**

GymFlow es una aplicación web desarrollada en Django que permite a gimnasios y entrenadores personales gestionar rutinas de entrenamiento, hacer seguimiento del progreso de sus clientes y mantener una biblioteca completa de ejercicios con demostraciones visuales.

---

## 🎯 Características Principales

### 👥 **Sistema de Roles Multi-Usuario**
- **Administradores**: Control total del sistema
- **Entrenadores**: Creación y asignación de rutinas a clientes
- **Usuarios/Clientes**: Acceso a rutinas personalizadas y seguimiento de progreso

### 💪 **Biblioteca de Ejercicios**
- 42+ ejercicios con GIFs demostrativos
- Filtrado por grupo muscular (Pecho, Espalda, Piernas, etc.)
- Búsqueda instantánea
- Sistema de favoritos
- Descripciones detalladas

### 📋 **Gestión de Rutinas**
- Creación de rutinas personalizadas
- Asignación de rutinas a usuarios específicos
- Configuración de series, repeticiones y descansos
- Registro de entrenamientos realizados

### 📊 **Seguimiento de Progreso**
- Registro de peso, medidas corporales y grasa corporal
- Historial completo de entrenamientos
- Estadísticas de rendimiento

### 🎨 **Interfaz Profesional**
- Diseño minimalista y responsive
- Temática verde profesional
- Optimizado para móvil y desktop

---

## 🔧 Tecnologías Utilizadas

- **Backend**: Django 5.2.5 (Python 3.13)
- **Base de Datos**: MySQL 8.0
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Autenticación**: Sistema integrado de Django
- **API**: ExerciseDB (datos de ejercicios)

---

## 📦 Instalación

### Requisitos Previos

- Python 3.13+
- MySQL 8.0+
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd gymflow
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar Base de Datos**

Crear base de datos en MySQL:
```sql
CREATE DATABASE db_gym CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Actualizar `config/settings.py` si es necesario:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_gym',
        'USER': 'root',
        'PASSWORD': 'tu_password',
        'HOST': 'localhost',
        'PORT': '3308',  # o 3306 si usas el puerto estándar
    }
}
```

4. **Ejecutar migraciones**
```bash
python manage.py migrate
```

5. **Crear superusuario (administrador)**
```bash
python manage.py createsuperuser
```

6. **Iniciar servidor de desarrollo**
```bash
python manage.py runserver
```

7. **Acceder a la aplicación**
- Aplicación: http://localhost:8000
- Panel de administración: http://localhost:8000/admin

---

## 👤 Usuarios de Prueba

Después de las migraciones, puedes crear usuarios con diferentes roles:

### **Administrador**
- Acceso total al sistema
- Gestión de usuarios y permisos
- Panel de administración Django

### **Entrenador**
- Crear y editar rutinas
- Asignar rutinas a clientes
- Ver progreso de clientes

### **Usuario/Cliente**
- Ver rutinas asignadas
- Registrar entrenamientos
- Seguimiento de progreso personal
- Guardar ejercicios favoritos

---

## 📁 Estructura del Proyecto

```
gymflow/
├── config/                 # Configuración de Django
│   ├── settings.py        # Configuración principal
│   ├── urls.py            # URLs raíz
│   └── wsgi.py            # WSGI para producción
│
├── gym/                    # App principal
│   ├── models.py          # Modelos de base de datos
│   ├── views.py           # Lógica de vistas
│   ├── urls.py            # URLs de la app
│   ├── forms.py           # Formularios
│   ├── admin.py           # Configuración admin
│   ├── exercisedb_service.py  # Servicio de ejercicios
│   └── templates/         # Templates HTML
│
├── static/                 # Archivos estáticos
│   ├── css/               # Estilos
│   ├── images/            # Imágenes
│   └── exercisedb/        # GIFs de ejercicios
│
├── manage.py              # Comando principal Django
├── requirements.txt       # Dependencias Python
└── README.md             # Este archivo
```

---

## 🚀 Despliegue en Producción

Para desplegar en producción, se recomienda:

1. **Hosting**: Render.com, Railway.app o PythonAnywhere
2. **Base de Datos**: PostgreSQL o MySQL gestionado
3. **Almacenamiento**: Cloudinary para GIFs/imágenes
4. **Variables de entorno**: Usar `.env` para secretos
5. **Configurar**: `DEBUG = False` en producción

---

## 🔐 Seguridad

GymFlow implementa las mejores prácticas de seguridad:

- ✅ Protección CSRF (Cross-Site Request Forgery)
- ✅ Protección XSS (Cross-Site Scripting)
- ✅ Protección SQL Injection (Django ORM)
- ✅ Contraseñas hasheadas (PBKDF2-SHA256)
- ✅ Autenticación basada en sesiones
- ✅ Control de acceso por roles
- ✅ Validación de datos en formularios

---

## 📝 Licencia

Este proyecto fue desarrollado como parte de un proyecto académico para Ingeniería de Software en INACAP.

---

## 👨‍💻 Autor

Desarrollado para el curso de Ingeniería de Software - INACAP

---

## 📞 Soporte

Para reportar problemas o sugerencias, contactar al desarrollador.

---

**¡Gracias por usar GymFlow! 💪🏋️**
