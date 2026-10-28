# crear_cursos_demo.py — Crea cursos, materiales, tareas y evaluaciones realistas para probar la plataforma
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from dashboard.models import Curso, Inscripcion, MaterialDidactico, Tarea, Evaluacion, Actividad
from django.utils import timezone
from datetime import timedelta

profe, _ = User.objects.get_or_create(username='profesor_demo', defaults={'email': 'profe@educonnect.com'})
alu, _ = User.objects.get_or_create(username='estudiante_demo', defaults={'email': 'estudiante@educonnect.com'})

CREADOS = []

def crear_curso(nombre, desc, categoria, grupo):
    c, created = Curso.objects.get_or_create(
        nombre=nombre,
        defaults={'descripcion': desc, 'categoria': categoria, 'profesor': profe, 'grupo': grupo}
    )
    if created:
        CREADOS.append(nombre)
    return c

# ============ CURSOS REALES ============
c1 = crear_curso(
    'Introducción a Python',
    'Aprende a programar desde cero con Python: variables, condicionales, ciclos, funciones y tus primeros proyectos. Ideal si nunca has programado.',
    'Programación', '2026-A'
)
c2 = crear_curso(
    'Matemáticas Aplicadas',
    'Álgebra, funciones y estadística básica con ejemplos prácticos de la vida real: finanzas personales, mediciones y análisis de datos.',
    'Matemáticas', '2026-A'
)
c3 = crear_curso(
    'Inglés para Principiantes A1',
    'Inglés nivel A1: saludos, presentaciones, vocabulario diario y gramática esencial. Con práctica de listening y ejercicios interactivos.',
    'Idiomas', '2026-B'
)
c4 = crear_curso(
    'Física: Mecánica Básica',
    'Cinemática, leyes de Newton, trabajo y energía explicados con experimentos caseros y simulaciones.',
    'Física', '2026-B'
)
c5 = crear_curso(
    'Química General',
    'Tabla periódica, enlaces químicos, reacciones y laboratorio virtual. Preparación para exámenes de admisión.',
    'Ciencias', '2026-A'
)
c6 = crear_curso(
    'Habilidades Digitales ofimáticas',
    'Word, Excel y PowerPoint desde cero hasta nivel intermedio. Certificado de participación al completar todas las actividades.',
    'Ciencias', '2026-B'
)

MATERIALES = {
    c1: [
        ('Clase 1: Instalación y Hola Mundo', 'Instalación de Python, primer programa y uso de print(). Incluye guía paso a paso con capturas.'),
        ('Clase 2: Variables y Tipos de Datos', 'Números, strings, booleanos y conversión de tipos con ejemplos resueltos.'),
    ],
    c2: [
        ('Unidad 1: Ecuaciones Lineales', 'Método de despeje, sustitución y gráficas. 20 ejercicios resueltos paso a paso.'),
    ],
    c3: [
        ('Unit 1: Greetings & Introductions', 'Vocabulario de saludos, verb to be, y diálogo de presentación personal.'),
    ],
    c4: [
        ('Tema 1: Movimiento Rectilíneo', 'Velocidad, aceleración y las 3 leyes de Newton con ejemplos cotidianos.'),
    ],
    c5: [
        ('Práctica 1: La Tabla Periódica', 'Grupos, periodos y propiedades de los elementos. Tabla interactiva incluida.'),
    ],
    c6: [
        ('Módulo Excel 1: Fórmulas Básicas', 'SUMA, PROMEDIO, MAX, MIN y referencias absolutas con plantilla de práctica.'),
    ],
}

TAREAS = {
    c1: [('Ejercicio: Tu primer programa', 'Escribe un programa que pida tu nombre y edad, y los imprima en un mensaje personalizado. Entrega el archivo .py o captura de pantalla.', 10)],
    c2: [('Tarea: Resolver 10 ecuaciones', 'Resuelve la hoja de ejercicios de ecuaciones lineales. Muestra todo el procedimiento.', 15)],
    c3: [('Homework: Introduce yourself', 'Escribe un párrafo de 5 líneas presentándote en inglés y grábalo o envíalo por escrito.', 10)],
}

EVALUACIONES = {
    c1: [('Quiz 1: Fundamentos de Python', 'Quiz de 10 preguntas sobre variables, tipos de datos y print().', 7)],
    c2: [('Examen Parcial 1', 'Examen de la primera unidad: ecuaciones, despejes y gráficas.', 14)],
}

ACTIVIDADES = {
    c1: [('Ver video: Qué es programar', 'video'), ('Leer guía de instalación', 'lectura')],
    c2: [('Ver clase grabada: despejes', 'video')],
    c3: [('Listening practice Unit 1', 'lectura')],
}

# ============ POBLAR ============
for curso, mats in MATERIALES.items():
    for titulo, desc in mats:
        MaterialDidactico.objects.get_or_create(
            titulo=titulo, curso=curso, profesor=profe,
            defaults={'descripcion': desc, 'tipo': 'pdf'}
        )

for curso, tareas in TAREAS.items():
    for titulo, desc, puntos in tareas:
        Tarea.objects.get_or_create(
            titulo=titulo, curso=curso,
            defaults={'descripcion': desc, 'puntos': puntos, 'fecha_entrega': timezone.now() + timedelta(days=7)}
        )

for curso, evals in EVALUACIONES.items():
    for nombre, desc, dias in evals:
        Evaluacion.objects.get_or_create(
            nombre=nombre, curso=curso, profesor=profe,
            defaults={'descripcion': desc, 'fecha': timezone.now().date() + timedelta(days=dias)}
        )

for curso, acts in ACTIVIDADES.items():
    for titulo, tipo in acts:
        Actividad.objects.get_or_create(
            titulo=titulo, curso=curso, tipo=tipo,
            defaults={'descripcion': f'Actividad de {tipo} para {curso.nombre}'}
        )

# Inscribir al estudiante demo en 2 cursos para que vea datos
for curso in [c1, c2]:
    Inscripcion.objects.get_or_create(alumno=alu, curso=curso)

print(f'✅ Cursos creados nuevos: {CREADOS if CREADOS else "(ya existían)"}')
print(f'📚 Total cursos en plataforma: {Curso.objects.count()}')
print(f'📦 Materiales: {MaterialDidactico.objects.count()} | Tareas: {Tarea.objects.count()} | Evaluaciones: {Evaluacion.objects.count()}')
print(f'👤 estudiante_demo inscrito en: ' + ', '.join(Inscripcion.objects.filter(alumno=alu).values_list('curso__nombre', flat=True)))
