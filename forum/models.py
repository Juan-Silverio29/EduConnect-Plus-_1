from django.db import models
from django.contrib.auth.models import User

class Foro(models.Model):
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to="foros/", blank=True, null=True)
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="foros")
    fijado = models.BooleanField(default=False)

    def __str__(self):
        return self.titulo


class Comentario(models.Model):
    foro = models.ForeignKey(Foro, related_name="comentarios", on_delete=models.CASCADE)
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    archivo = models.FileField(upload_to="comentarios_archivos/", null=True, blank=True)  # ✅ nuevo campo
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comentario de {self.autor.username} en {self.foro.titulo}"

