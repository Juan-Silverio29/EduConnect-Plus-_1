from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from resources.models import Recursos  # ajusta al modelo real

def recommend_for_user(user, top_k=5):
    # Extrae recursos y descripciones
    recursos = list(Recursos.objects.all())
    docs = [r.titulo + " " + (r.descripcion or "") for r in recursos]
    if not docs:
        return []

    vec = TfidfVectorizer(stop_words='spanish').fit_transform(docs)
    # LM: puedes usar perfil del usuario por recursos vistos - aquí ejemplo simple
    # usamos último recurso visto si existe
    vistos = user.recursos_set.all()[:1]
    if vistos:
        query = vistos[0].titulo + " " + (vistos[0].descripcion or "")
    else:
        query = "curso inicio"

    q_vec = TfidfVectorizer(stop_words='spanish').fit(docs).transform([query])
    cosine_similarities = linear_kernel(q_vec, vec).flatten()
    related_docs_indices = cosine_similarities.argsort()[:-top_k-1:-1]
    return [recursos[i] for i in related_docs_indices]
