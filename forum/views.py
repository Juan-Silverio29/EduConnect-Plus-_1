# forum/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Foro, Comentario
from .forms import ForoForm, ComentarioForm


# 📄 Listar foros (vista general o del profesor)
@login_required
def foro_lista(request):
    # Limpiamos mensajes anteriores para evitar arrastres entre vistas
    storage = messages.get_messages(request)
    storage.used = True

    foros = Foro.objects.all().order_by("-fecha_creacion")

    # Si el usuario es profesor, cargamos la plantilla especial
    if request.user.is_staff:
        return render(request, "foros_profesor.html", {"foros": foros})
    else:
        return render(request, "foros.html", {"foros": foros})


# ✏️ Crear nuevo foro
@login_required
def crear_foro(request):
    if request.method == "POST":
        form = ForoForm(request.POST, request.FILES)
        if form.is_valid():
            foro = form.save(commit=False)
            foro.autor = request.user
            foro.save()

            messages.success(request, "✅ Foro creado correctamente.")

            # 🔹 Redirige al lugar correcto según el tipo de usuario
            if request.user.is_staff:
                return redirect("/dashboard/profesor/foros/")
            else:
                return redirect("foros")
    else:
        form = ForoForm()

    # 🔹 Cargar plantilla correcta según tipo de usuario
    if request.user.is_staff:
        template = "crear_foro_profesor.html"
    else:
        template = "crear_foro.html"

    return render(request, template, {"form": form})


# 👁️ Ver detalle del foro
@login_required
def foro_detalle(request, foro_id):
    foro = get_object_or_404(Foro, id=foro_id)
    comentarios = foro.comentarios.all().order_by("-fecha")

    if request.method == "POST":
        form = ComentarioForm(request.POST, request.FILES)  # ✅ importante
        if form.is_valid():
            comentario = form.save(commit=False)
            comentario.foro = foro
            comentario.autor = request.user
            comentario.save()
            messages.success(request, "💬 Comentario agregado correctamente.")
            return redirect("foro_detalle", foro_id=foro.id)
    else:
        form = ComentarioForm()

    return render(request, "foro_detalle.html", {"foro": foro, "comentarios": comentarios, "form": form})


# ✏️ Editar foro (solo el autor)
@login_required
def editar_foro(request, foro_id):
    foro = get_object_or_404(Foro, id=foro_id)

    if foro.autor != request.user:
        messages.warning(request, "⚠️ No tienes permiso para editar este foro.")
        return redirect("foros")

    if request.method == "POST":
        form = ForoForm(request.POST, request.FILES, instance=foro)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Foro actualizado correctamente.")

            # 🔹 Redirige al listado del profesor, no al dashboard
            if request.user.is_staff:
                return redirect("/dashboard/profesor/foros/")
            else:
                return redirect("foros")
    else:
        form = ForoForm(instance=foro)

    return render(request, "editar_foro.html", {"form": form, "foro": foro})


# 🗑️ Eliminar foro (solo el autor)
@login_required
def eliminar_foro(request, foro_id):
    foro = get_object_or_404(Foro, id=foro_id)

    if foro.autor != request.user:
        messages.warning(request, "⚠️ No tienes permiso para eliminar este foro.")
        return redirect("foros")

    if request.method == "POST":
        foro.delete()
        messages.success(request, "🗑️ Foro eliminado correctamente.")

        # 🔹 Redirige directamente a los foros del profesor
        if request.user.is_staff:
            return redirect("/dashboard/profesor/foros/")
        else:
            return redirect("foros")

    return render(request, "eliminar_foro.html", {"foro": foro})


# ✏️ Editar comentario
@login_required
def editar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)

    if comentario.autor != request.user:
        messages.warning(request, "⚠️ No tienes permiso para editar este comentario.")
        return redirect("foro_detalle", foro_id=comentario.foro.id)

    if request.method == "POST":
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()
            messages.success(request, "💬 Comentario actualizado correctamente.")
            return redirect("foro_detalle", foro_id=comentario.foro.id)
    else:
        form = ComentarioForm(instance=comentario)

    return render(request, "editar_comentario.html", {"form": form, "comentario": comentario})


# 🗑️ Eliminar comentario
@login_required
def eliminar_comentario(request, comentario_id):
    comentario = get_object_or_404(Comentario, id=comentario_id)

    if comentario.autor != request.user:
        messages.warning(request, "⚠️ No tienes permiso para eliminar este comentario.")
        return redirect("foro_detalle", foro_id=comentario.foro.id)

    if request.method == "POST":
        foro_id = comentario.foro.id
        comentario.delete()
        messages.success(request, "🗑️ Comentario eliminado correctamente.")
        return redirect("foro_detalle", foro_id=foro_id)

    return render(request, "eliminar_comentario.html", {"comentario": comentario})


# 📌 Fijar / Desfijar foro (solo profesor)
@login_required
def fijar_foro(request, foro_id):
    foro = get_object_or_404(Foro, id=foro_id)
    if not request.user.is_staff:
        messages.warning(request, "⚠️ Solo los profesores pueden fijar publicaciones.")
        return redirect("foros")

    foro.fijado = not foro.fijado
    foro.save()
    estado = "fijado" if foro.fijado else "desfijado"
    messages.success(request, f"📌 Foro {estado} correctamente.")
    return redirect("foros")
