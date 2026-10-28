# resources/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Recursos
from .forms import RecursoForm, EntregaAlumnoForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dashboard.models import Curso, MaterialDidactico, Inscripcion, EntregaAlumno
import os  

@login_required
def lista_recursos(request):
    """
    Muestra los materiales del curso y permite al alumno subir entregas.
    """
    cursos_inscritos = Curso.objects.filter(inscritos__alumno=request.user)
    materiales = MaterialDidactico.objects.filter(curso__in=cursos_inscritos).order_by('-fecha_subida')

    # Filtrar por curso si se selecciona
    curso_id = request.GET.get("curso")
    if curso_id:
        materiales = materiales.filter(curso_id=curso_id)

    # ðŸ§© Manejar subida de entrega
    if request.method == 'POST':
        form = EntregaAlumnoForm(request.POST, request.FILES)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.alumno = request.user

            # ðŸ”¹ Detectar tipo automÃ¡ticamente
            archivo = entrega.archivo
            if archivo:
                ext = os.path.splitext(archivo.name)[1].lower()
                if ext in ['.pdf']:
                    entrega.tipo = 'PDF'
                elif ext in ['.ppt', '.pptx']:
                    entrega.tipo = 'PresentaciÃ³n'
                elif ext in ['.mp4', '.mov', '.avi']:
                    entrega.tipo = 'Video'
                elif ext in ['.jpg', '.jpeg', '.png']:
                    entrega.tipo = 'Imagen'
                elif ext in ['.doc', '.docx']:
                    entrega.tipo = 'Documento'
                else:
                    entrega.tipo = 'Otro'

            entrega.save()
            messages.success(request, "âœ… Archivo subido correctamente.")
            return redirect('lista_recursos')
    else:
        form = EntregaAlumnoForm()

    # Obtener entregas del alumno
    entregas = EntregaAlumno.objects.filter(alumno=request.user).order_by('-fecha_subida')

    return render(request, "lista_recursos.html", {
        "materiales": materiales,
        "form": form,
        "entregas": entregas,
        "cursos_inscritos": cursos_inscritos,
    })

@login_required
def lista_cursos(request):
    cursos = Curso.objects.all().select_related("profesor")
    inscritos_ids = Inscripcion.objects.filter(alumno=request.user).values_list("curso_id", flat=True)

    context = {
        "cursos": cursos,
        "inscritos_ids": inscritos_ids,
    }
    return render(request, "lista_cursos.html", context)

@login_required
def inscribirse_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    inscripcion, creada = Inscripcion.objects.get_or_create(alumno=request.user, curso=curso)
    
    if creada:
        messages.success(request, f"âœ… Te has inscrito al curso: {curso.nombre}")
    else:
        messages.info(request, f"Ya estÃ¡s inscrito en el curso: {curso.nombre}")

    return redirect("lista_cursos")

@login_required
def darse_baja_curso(request, curso_id):
    inscripcion = Inscripcion.objects.filter(curso_id=curso_id, alumno=request.user).first()
    if inscripcion:
        inscripcion.delete()
        messages.success(request, "âŒ Te has dado de baja correctamente del curso.")
    else:
        messages.warning(request, "âš ï¸ No estabas inscrito en este curso.")

    return redirect('lista_cursos')

@login_required
def subir_recurso(request):
    if request.method == "POST":
        form = RecursoForm(request.POST, request.FILES)
        if form.is_valid():
            recurso = form.save(commit=False)
            recurso.autor = request.user
            recurso.save()
            messages.success(request, "âœ… Recurso subido correctamente.")
            return redirect("lista_recursos")
    else:
        form = RecursoForm()
    return render(request, "subir_recurso.html", {"form": form})

@login_required
def editar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recursos, id=recurso_id)
    
    if recurso.autor != request.user and not request.user.is_superuser:
        messages.warning(request, "âš ï¸ No tienes permiso para editar este recurso.")
        return redirect("lista_recursos")

    if request.method == "POST":
        form = RecursoForm(request.POST, request.FILES, instance=recurso)
        if form.is_valid():
            form.save()
            messages.success(request, "âœ… Recurso actualizado correctamente.")
            return redirect("lista_recursos")
    else:
        form = RecursoForm(instance=recurso)
    return render(request, "editar_recurso.html", {"form": form, "recurso": recurso})

@login_required
def eliminar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recursos, id=recurso_id)

    if recurso.autor != request.user and not request.user.is_superuser:
        messages.warning(request, "âš ï¸ No puedes eliminar un recurso que no es tuyo.")
        return redirect("lista_recursos")

    if request.method == "POST":
        recurso.delete()
        messages.success(request, "ðŸ—‘ï¸ Recurso eliminado correctamente.")
        return redirect("lista_recursos")
    return render(request, "eliminar_recurso.html", {"recurso": recurso})

@login_required
def logros_recursos_completados(request):
    recursos = Recursos.objects.filter(completado=True)
    total_recursos = Recursos.objects.count()

    progreso = int((recursos.count() / total_recursos) * 100) if total_recursos > 0 else 0

    if progreso < 40:
        progreso_class = "bg-danger"
    elif progreso < 70:
        progreso_class = "bg-warning"
    else:
        progreso_class = "bg-success"

    return render(request, "logros_recursos_completados.html", {
        "recursos": recursos,
        "total_recursos": total_recursos,
        "progreso": progreso,
        "progreso_class": progreso_class
    })

@login_required
def eliminar_entrega(request, entrega_id):
    try:
        entrega = get_object_or_404(EntregaAlumno, id=entrega_id, alumno=request.user)
        
        # Eliminar archivo fÃ­sico
        if entrega.archivo and entrega.archivo.path:
            if os.path.exists(entrega.archivo.path):
                os.remove(entrega.archivo.path)

        entrega.delete()
        messages.success(request, "ðŸ—‘ï¸ Entrega eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"âš ï¸ No se pudo eliminar la entrega: {e}")

    return redirect('lista_recursos')
