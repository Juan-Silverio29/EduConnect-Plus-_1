# test_funcional.py — Pruebas de regresión de todas las rutas clave
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from dashboard.models import Curso, Inscripcion, MaterialDidactico
from forum.models import Foro
import json

RESULTADOS = []

def check(nombre, fn):
    try:
        r = fn()
        ok = r is True
        RESULTADOS.append((nombre, 'OK' if ok else 'FALLO', str(r) if not ok else ''))
    except Exception as e:
        RESULTADOS.append((nombre, 'ERROR', f'{type(e).__name__}: {e}'))

def client_for(username):
    c = Client()
    u = User.objects.get(username=username)
    u.backend = 'django.contrib.auth.backends.ModelBackend'
    c.force_login(u)
    return c

alu = client_for('estudiante_demo')
pro = client_for('profesor_demo')
adm = client_for('admin')

# ---------- GET páginas estudiante ----------
for url in ['/dashboard/user/', '/dashboard/progreso/', '/dashboard/alumno/cursos-disponibles/',
            '/dashboard/alumno/mis-recursos/', '/resources/', '/resources/subir/', '/resources/cursos/',
            '/resources/logros/', '/forum/', '/forum/crear/', '/ai/stats/', '/ai/history/',
            '/dashboard/api/ai-stats/', '/dashboard/api/ai-recommendations/', '/auth/configuracion/']:
    check(f'GET {url}', lambda u=url: alu.get(u).status_code == 200)

# ---------- GET páginas profesor ----------
for url in ['/dashboard/profesor/', '/dashboard/profesor/cursos/', '/dashboard/profesor/crear-curso/',
            '/dashboard/profesor/evaluaciones/', '/dashboard/profesor/crear-evaluacion/',
            '/dashboard/profesor/material/', '/dashboard/profesor/foros/']:
    check(f'PROF {url}', lambda u=url: pro.get(u).status_code == 200)

# ---------- GET páginas admin ----------
for url in ['/dashboard/admin/', '/dashboard/admin/usuarios/', '/dashboard/admin/cursos/',
            '/dashboard/admin/estadisticas/', '/admin/']:
    check(f'ADM {url}', lambda u=url: adm.get(u).status_code == 200)

# ---------- Flujo completo: profesor crea curso ----------
resp = pro.post('/dashboard/profesor/crear-curso/', {
    'nombre': 'Curso Test QA', 'descripcion': 'Curso de prueba automatizada',
    'categoria': 'Programación', 'grupo': 'QA',
})
check('PROF crea curso', lambda: Curso.objects.filter(nombre='Curso Test QA').exists())

curso = Curso.objects.filter(nombre='Curso Test QA').first()

# ---------- Flujo: alumno se inscribe ----------
def _test_inscribe():
    if not curso:
        return False
    r = alu.get(f'/dashboard/alumno/inscribirse/{curso.id}/')
    return r.status_code in (200, 302) and Inscripcion.objects.filter(alumno=User.objects.get(username='estudiante_demo'), curso=curso).exists()
check('ALU inscribe', _test_inscribe)

# ---------- Profesor sube material ----------
resp = pro.post('/dashboard/profesor/material/', {
    'titulo': 'Material QA', 'descripcion': 'test', 'curso': curso.id,
})
check('PROF sube material', lambda: MaterialDidactico.objects.filter(titulo='Material QA').exists())

# ---------- Foro: crear publicación ----------
def _test_foro():
    r = alu.post('/forum/crear/', {'titulo': 'Foro QA', 'descripcion': 'Prueba automatizada'})
    return Foro.objects.filter(titulo='Foro QA').exists()
check('ALU crea foro', _test_foro)

# ---------- Chat IA responde ----------
resp = alu.post('/dashboard/api/ai-chat/', data=json.dumps({'message': '¿cómo me inscribo a un curso?'}),
                content_type='application/json')
body = resp.json() if resp.status_code == 200 else {}
check('IA chat responde', lambda: resp.status_code == 200 and len(body.get('reply', '')) > 10)

resp = alu.post('/dashboard/api/ai-chat/', data=json.dumps({'message': 'hola'}), content_type='application/json')
check('IA chat hola', lambda: resp.status_code == 200)

# ---------- Inscripciones del alumno visibles ----------
resp = alu.get('/dashboard/alumno/mis-recursos/')
check('ALU mis-recursos muestra material', lambda: 'Material QA' in resp.content.decode('utf-8', 'ignore'))

# ==============================
print('\n===== RESULTADOS =====')
fails = 0
for nombre, estado, detalle in RESULTADOS:
    icon = '✅' if estado == 'OK' else '❌'
    if estado != 'OK':
        fails += 1
        print(f'{icon} {nombre} [{estado}] {detalle}')
    else:
        print(f'{icon} {nombre}')
print(f'\nTotal: {len(RESULTADOS)} | OK: {len(RESULTADOS)-fails} | Fallas: {fails}')
sys.exit(1 if fails else 0)
