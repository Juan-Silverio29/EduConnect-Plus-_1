# ai/views.py
import os
import time
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

from django.utils import timezone
import json

# Opcional: si quieres usar sentence-transformers local:
try:
    from sentence_transformers import SentenceTransformer, util
    MODEL_LOCAL = SentenceTransformer(os.environ.get("LOCAL_AI_MODEL", "all-MiniLM-L6-v2"))
except Exception:
    MODEL_LOCAL = None

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

# Rate-limit simple por usuario (cache en memoria)
RATE_LIMIT_KEY = "ai_rl_{}"  # user.id
RATE_LIMIT_SEC = int(os.environ.get("AI_RATE_LIMIT_SEC", 2))  # 2 seg default

# Guardamos conversaciones simples en cache por usuario: "ai_hist_{user_id}" -> list
HISTORY_KEY = "ai_hist_{}"
HISTORY_MAX = 50

def _append_history(user_id, role, text):
    k = HISTORY_KEY.format(user_id)
    hist = cache.get(k, [])
    hist.append({"role": role, "text": text, "ts": timezone.now().isoformat()})
    if len(hist) > HISTORY_MAX:
        hist = hist[-HISTORY_MAX:]
    cache.set(k, hist, 3600*24)  # 24h

@login_required
@require_GET
def get_history(request):
    k = HISTORY_KEY.format(request.user.id)
    return JsonResponse({"history": cache.get(k, [])})

@login_required
@require_GET
def ai_stats(request):
    """
    Devuelve métricas para Plotly: ejemplo dummy o reales desde la base de datos.
    Aquí extraemos algunas métricas desde models (resources, foro, users).
    """
    # ejemplo simple (puedes reemplazar por consultas reales)
    from django.contrib.auth.models import User
    total_users = User.objects.count()
    total_profesores = User.objects.filter(is_staff=True).count()
    total_estudiantes = total_users - total_profesores
    # datos de recomendador (ejemplo)
    data = {
        "total_users": total_users,
        "total_profesores": total_profesores,
        "total_estudiantes": total_estudiantes,
        "rec_precision": 0.72,  # placeholder
        "rec_recall": 0.68,
        "cluster_sizes": [10, 15, 25]  # ejemplo
    }
    return JsonResponse(data)

@login_required
@require_POST
def api_chat(request):
    # Rate limit
    rl_key = RATE_LIMIT_KEY.format(request.user.id)
    last = cache.get(rl_key)
    now = time.time()
    if last and now - last < RATE_LIMIT_SEC:
        return JsonResponse({"error": "Rate limit: espera un momento."}, status=429)
    cache.set(rl_key, now, RATE_LIMIT_SEC)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST.dict()
    message = data.get("message", "").strip()
    if not message:
        return JsonResponse({"error": "Sin mensaje"}, status=400)

    user = request.user

    # Guarda pregunta en historial
    _append_history(user.id, "user", message)

    # Preferir OpenAI si KEY disponible
    response_text = None
    if OPENAI_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_KEY)
            resp = client.chat.completions.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Eres el tutor virtual de EduConnect, responde conciso y con pasos."},
                    {"role": "user", "content": message}
                ],
                max_tokens=400,
                temperature=0.2,
            )
            response_text = resp.choices[0].message.content.strip()
        except Exception as e:
            # si falla OpenAI, cae al fallback local
            response_text = None

    if not response_text:
        # Fallback local: si tienes sentence-transformers intenta similaridad con FAQ,
        # si no, devuelve respuestas básicas
        FAQ = [
            ("¿cómo hago login?", "Ve a /auth/login/, introduce usuario y contraseña. Si olvidaste contraseña, usa cambiar contraseña."),
            ("¿cómo subo un recurso?", "Entra a Recursos -> Subir recurso y completa título, descripción y archivo."),
            ("¿qué es EduConnect?", "Plataforma para organizar y recomendar recursos educativos, con modo offline y IA.")
        ]
        if MODEL_LOCAL:
            # compara similaridades entre message y FAQ
            try:
                q_emb = MODEL_LOCAL.encode(message, convert_to_tensor=True)
                faqs = [f[0] for f in FAQ]
                faq_emb = MODEL_LOCAL.encode(faqs, convert_to_tensor=True)
                sims = util.cos_sim(q_emb, faq_emb)[0].cpu().tolist()  # lista
                best_idx = int(max(range(len(sims)), key=lambda i: sims[i]))
                if sims[best_idx] > 0.45:
                    response_text = FAQ[best_idx][1]
                else:
                    # respuesta generica
                    response_text = "Puedo ayudarte con eso. ¿Puedes darme más detalles o decirme el nombre del curso/recurso?"
            except Exception:
                response_text = "Lo siento, no pude procesar la pregunta localmente. Intenta nuevamente o usa la versión en la nube."
        else:
            # respuesta simple
            lowered = message.lower()
            if "login" in lowered or "entrar" in lowered:
                response_text = "Para iniciar sesión ve a /auth/login/ e introduce tus credenciales. Si eres admin verás el panel de administración."
            elif "recurso" in lowered or "subir" in lowered:
                response_text = "En Recursos -> Subir recurso puedes adjuntar un archivo y establecer título/descr."
            else:
                response_text = "¿Puedes dar más contexto? Por ejemplo, '¿cómo subo mi tarea en el curso X?'"

    # Guarda respuesta en historial
    _append_history(user.id, "assistant", response_text)

    return JsonResponse({"reply": response_text})
