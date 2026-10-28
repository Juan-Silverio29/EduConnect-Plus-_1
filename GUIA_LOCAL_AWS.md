# EduConnect+ — Guía local y migración a AWS

## ✅ Estado actual (probado en local)

| Ruta | Estado |
|---|---|
| `/` (landing) | 200 OK |
| `/auth/login/` | 200 OK — login funcional |
| `/dashboard/` (estudiante y profesor) | 200 OK |
| `/resources/` | 200 OK |
| `/forum/` | 200 OK |
| `/admin/` (Jazzmin) | 200 OK |

### Usuarios de prueba (creados localmente)
| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123!` | Superusuario (redirige a /admin/) |
| `profesor_demo` | `Profe123!` | Profesor |
| `estudiante_demo` | `Estudio123!` | Estudiante |

## 🚀 Cómo ejecutar en local

```powershell
cd C:\Users\saul.arechiga\Analista\EduConnect-Plus-main\EduConnect-Plus-main
.\RUN_LOCAL.ps1          # inicia el servidor en http://127.0.0.1:8000
```
o manualmente:
```powershell
.\venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

## 🔧 Correcciones que hice para que funcione localmente

1. **`requirements.txt`** estaba en UTF-16 corrupto y con paquetes duplicados → reescrito en UTF-8 limpio, y agregados los paquetes faltantes que estaban en INSTALLED_APPS pero no en el archivo (`django-jazzmin`, `django-axes`, `django-cors-headers`, `requests`).
2. **`core/settings.py`**: claves de reCAPTCHA y credenciales de RDS ya no están hardcodeadas (van por variables de entorno). En DEBUG, `ALLOWED_HOSTS = ['*']` para desarrollo local.
3. **`auth_app/views.py`**: Django lanzaba `ValueError: You have multiple authentication backends configured` al hacer login (Axes + ModelBackend). Se especifica el backend explícitamente en cada `login()`.
4. **`ai/views.py`**: la llamada a OpenAI usaba la API vieja `openai.ChatCompletion.create` (eliminada en openai>=1.0) → migrada al cliente nuevo `OpenAI().chat.completions.create`.
5. **Fixture `fixtures/initial_data.json`**: tenía campo `usuario` que ya no existe en el modelo (ahora es `user`); en su lugar creé los usuarios demo directamente en la BD.

## 🤖 Módulo IA — cómo activarlo y recomendaciones

El chat IA (`/ai/`) ya funciona con **fallback local sin clave** (FAQ + coincidencias simples). Para activar el modo con LLM:

```powershell
$env:OPENAI_API_KEY = "sk-..."     # tu clave
$env:OPENAI_MODEL = "gpt-4o-mini"  # opcional
```

⚠️ Importante: en `replacements.txt` del proyecto hay una **clave de OpenAI expuesta**. Revócala en https://platform.openai.com/api-keys y no la uses más.

Recomendaciones para hacer la IA más útil y funcional:
1. **Darle contexto real (RAG)**: en vez de un FAQ de 3 líneas, indexar los títulos/descripciones de `resources.Recurso` y los cursos. Con `sentence-transformers` + cosine similarity ya tienes búsqueda semántica de recursos — el modelo `all-MiniLM-L6-v2` descarga ~90MB la primera vez.
2. **Contexto por rol**: si el usuario es estudiante, responder con "tus cursos pendientes"; si es profesor, "tus alumnos". Ya tienes `request.user.perfilusuario`.
3. **Acciones, no solo chat**: que la IA pueda responder con datos reales ("¿qué recursos hay de X?") consultando la BD antes de llamar al LLM — así gasta menos tokens.
4. **Persistir conversaciones**: ahora van en cache LocMem y se pierden al reiniciar. Un modelo `ChatMessage(user, role, text)` en `ai/models.py` y tabla en el perfil.

## ☁️ Migración a AWS

El proyecto ya tiene modo producción (`DJANGO_PRODUCTION=True`). Pasos:

1. **EC2** (ya conoces la IP 3.146.150.176): Ubuntu + `python3-venv`, clonar código, `pip install -r requirements.txt`.
2. **RDS PostgreSQL**: ya existe la instancia `db-educonect-free...`. Configura:
   ```bash
   export DJANGO_PRODUCTION=True DJANGO_DEBUG=False
   export DB_HOST=<endpoint-rds> DB_NAME=postgres DB_USER=postgres DB_PASSWORD=<pass>
   export DJANGO_SECRET_KEY=<clave-larga-aleatoria>
   ```
   ⚠️ Cambia la contraseña por variables de entorno, nunca en el código (antes estaba `admin404` en texto plano).
3. **Migrar y arrancar**:
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   gunicorn core.wsgi:application --bind 0.0.0.0:8000
   ```
4. **Nginx** delante de gunicorn (estáticos + HTTPS con certbot para `educonnect.duckdns.org`).
5. **Security Group**: abrir 80/443; SSH solo desde tu IP. La BD RDS solo accesible desde el SG de la EC2.
6. **Media files**: para múltiples instancias usa S3 (`django-storages`); con una sola EC2, volume EBS basta.

### Problemas conocidos pendientes para producción
- `django-ratelimit` y `sentence-transformers` están en comentarios del requirements original — instalar solo si los necesitas.
- El warning `axes.W006` sugiere añadir `'ip_address'` a `AXES_LOCKOUT_PARAMETERS` (hoy bloquea solo por username; un atacante podría rotar IPs... en realidad es al revés: conviene `[["username","ip_address"]]`).
