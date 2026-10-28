# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_perfil')
    institucion = models.CharField(max_length=255)
    foto_perfil = models.ImageField(upload_to='perfil/', null=True, blank=True)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# 🧑‍🏫 Modelo de Curso COMBINADO
class Curso(models.Model):
    CATEGORIAS = [
        ("Ciencias", "Ciencias"),
        ("Matemáticas", "Matemáticas"),
        ("Programación", "Programación"),
        ("Idiomas", "Idiomas"),
        ("Física", "Física"),
        ("Música", "Música"),
    ]

    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default="Ciencias")
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cursos')
    grupo = models.CharField(max_length=50, blank=True, null=True)
    alumnos = models.ManyToManyField(User, blank=True, related_name='cursos_inscritos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre

# 👨‍🎓 Modelo de Inscripción (relación alumno-curso)
class Inscripcion(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name="inscripciones")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="inscritos")
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('alumno', 'curso')

    def __str__(self):
        return f"{self.alumno.username} → {self.curso.nombre}"

# 📚 MaterialDidactico COMBINADO
class MaterialDidactico(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="materiales", null=True, blank=True)
    profesor = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=50, blank=True, null=True)
    archivo = models.FileField(upload_to='materiales/', blank=True, null=True)
    enlace = models.URLField(blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

# 📘 Modelo de Evaluaciones
class Evaluacion(models.Model):
    profesor = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='evaluaciones')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateField()
    creada_en = models.DateTimeField(auto_now_add=True)
    
    # 👇 NUEVO CAMPO: relación directa con MaterialDidactico
    materiales = models.ManyToManyField('MaterialDidactico', blank=True, related_name='evaluaciones_asignadas')

    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"
class UserActivity(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    actividad = models.CharField(max_length=255)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)  # ✅ agregado
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.actividad}"



from django.db import models
from django.contrib.auth.models import User

class LearningSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    inicio = models.DateTimeField(auto_now_add=True)
    fin = models.DateTimeField(null=True, blank=True)
    duracion_minutos = models.FloatField(default=0)

    def __str__(self):
        return f"Sesión de {self.user.username} - {self.duracion_minutos} min"

 #📝 Modelo para entregas de alumnos
"""class EntregaAlumno(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE, related_name="entregas")
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="entregas_alumnos")
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    archivo = models.FileField(upload_to='entregas_alumnos/')
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    comentario_profesor = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_entrega']

    def __str__(self):
        return f"{self.titulo} - {self.alumno.username}"""

# 📝 Modelo para entregas de alumnos - AGREGA ESTO AL FINAL
class EntregaAlumno(models.Model):
    alumno = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='entregas/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Actividad(models.Model):
    TIPOS = [
        ("video", "Video"),
        ("lectura", "Lectura"),
        ("tarea", "Tarea"),
        ("examen", "Examen"),
    ]

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="actividades")
    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.curso.nombre})"

class Tarea(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    puntos = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.titulo} ({self.curso.nombre})"


class EntregaTarea(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas')
    alumno = models.ForeignKey(User, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='entregas_tareas/', blank=True, null=True)
    texto = models.TextField(blank=True, null=True)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    calificacion = models.FloatField(null=True, blank=True)
    retroalimentacion = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('tarea', 'alumno')  # Un alumno solo una entrega

    def __str__(self):
        return f"Entrega de {self.alumno.username} para {self.tarea.titulo}"