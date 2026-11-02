from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Alimento
from .forms import AlimentoForm
from .services import generar_receta_con_llm, modificar_receta_con_llm, ErrorGeneracionReceta
from .recipes import finalizar_receta


@login_required(login_url="usuarios:login_web")
def listado_alimentos_web(request):
    hoy = timezone.localdate()

    alimentos = Alimento.objects.filter(
        usuario=request.user
    ).order_by("fecha_caducidad")

    return render(
        request,
        "despensa/listado_alimentos.html",
        {
            "alimentos": alimentos,
            "hoy": hoy,
        }
    )


@login_required(login_url="usuarios:login_web")
def alta_alimento_web(request):
    if request.method == "POST":
        form = AlimentoForm(request.POST)

        if form.is_valid():
            alimento = form.save(commit=False)
            alimento.usuario = request.user
            alimento.save()

            messages.success(request, "Alimento añadido correctamente.")
            
            return redirect("despensa:listado_alimentos")
        
        else:
            messages.error(
                request,
                "No se ha podido crear el alimento. Revisa los datos introducidos."
            )
            
    else:
        form = AlimentoForm()

    return render(
        request,
        "despensa/formulario_alimento.html",
        {"form": form}
    )
    

@login_required(login_url="usuarios:login_web")
def editar_alimento_web(request, alimento_id):
    try:
        alimento = Alimento.objects.get(
            pk=alimento_id,
            usuario=request.user
        )
    except Alimento.DoesNotExist:
        messages.error(
            request,
            "El alimento solicitado no existe o no pertenece a tu despensa."
        )
        return redirect("despensa:listado_alimentos")

    if request.method == "POST":
        form = AlimentoForm(request.POST, instance=alimento)

        if form.is_valid():
            form.save()
            
            messages.success(request, "Alimento actualizado correctamente.")
            
            return redirect("despensa:listado_alimentos")
        
        else:
            messages.error(
                request,
                "No se ha podido actualizar el alimento. Revisa los datos introducidos."
            )
            
    else:
        form = AlimentoForm(instance=alimento)

    return render(
        request,
        "despensa/formulario_alimento.html",
        {
            "form": form,
            "titulo": "Editar alimento",
            "texto_boton": "Guardar cambios",
        }
    )
    

@login_required(login_url="usuarios:login_web")
def eliminar_alimento_web(request, alimento_id):
    try:
        alimento = Alimento.objects.get(
            pk=alimento_id,
            usuario=request.user
        )
    except Alimento.DoesNotExist:
        messages.error(
            request,
            "El alimento solicitado no existe o no pertenece a tu despensa."
        )
        return redirect("despensa:listado_alimentos")

    if request.method == "POST":
        alimento.delete()
        
        messages.success(request, "Alimento eliminado correctamente.")
        
        return redirect("despensa:listado_alimentos")

    return render(
        request,
        "despensa/eliminar_alimento.html",
        {"alimento": alimento}
    )
    
    
@login_required(login_url="usuarios:login_web")
def alimentos_proximos_web(request):
    hoy = timezone.localdate()
    limite = hoy + timedelta(days=7)

    alimentos = Alimento.objects.filter(
        usuario=request.user,
        fecha_caducidad__gte=hoy,
        fecha_caducidad__lte=limite
    ).order_by("fecha_caducidad")

    return render(
        request,
        "despensa/alimentos_proximos.html",
        {
            "alimentos": alimentos,
            "hoy": hoy,
            "limite": limite,
        }
    )
    

@login_required(login_url="usuarios:login_web")
@login_required(login_url="usuarios:login_web")
def generar_recetas_web(request):
    hoy = timezone.localdate()

    # Excluye los alimentos caducados de la generación de recetas.
    alimentos = Alimento.objects.filter(
        usuario=request.user,
        fecha_caducidad__gte=hoy,
    ).order_by("fecha_caducidad")

    receta_generada = None
    alimentos_seleccionados_ids = []
    alimentos_usados_ids = []
    alimentos_utilizados = []
    indicaciones_usuario = ""
    comentario_usuario = ""

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "generar_receta":
            if not alimentos.exists():
                messages.error(
                    request,
                    "No tienes alimentos disponibles para generar una receta."
                )
            else:
                indicaciones_usuario = request.POST.get("indicaciones_usuario", "").strip()
                alimentos_seleccionados_ids = request.POST.getlist("alimentos_seleccionados")

                # Si el usuario selecciona alimentos, la receta se genera solo con ellos;
                # en caso contrario se utiliza toda la despensa.
                if alimentos_seleccionados_ids:
                    alimentos_para_receta = alimentos.filter(
                        pk__in=alimentos_seleccionados_ids
                    )
                else:
                    alimentos_para_receta = alimentos

                try:
                    resultado_generacion = generar_receta_con_llm(
                        alimentos_para_receta,
                        usar_todos_los_alimentos=bool(alimentos_seleccionados_ids),
                        indicaciones_usuario=indicaciones_usuario,
                    )

                    receta_generada = resultado_generacion["receta"]
                    alimentos_utilizados = resultado_generacion["alimentos_utilizados"]

                    alimentos_usados_ids = [
                        alimento["id"]
                        for alimento in alimentos_utilizados
                    ]

                    # Guarda en la sesión los alimentos realmente utilizados
                    # para poder modificar o finalizar la receta posteriormente.
                    request.session["alimentos_utilizados_receta"] = alimentos_utilizados

                except ErrorGeneracionReceta as error:
                    messages.error(request, str(error))

        elif accion == "modificar_receta":
            receta_generada = request.POST.get("receta_generada", "")
            comentario_usuario = request.POST.get("comentario_usuario", "")

            try:
                resultado_modificacion = modificar_receta_con_llm(
                    receta_generada,
                    alimentos,
                    comentario_usuario,
                )

                receta_generada = resultado_modificacion["receta"]
                alimentos_utilizados = resultado_modificacion["alimentos_utilizados"]

                alimentos_usados_ids = [
                    alimento["id"]
                    for alimento in alimentos_utilizados
                ]

                # Actualiza la sesión con los alimentos utilizados en la receta modificada.
                request.session["alimentos_utilizados_receta"] = alimentos_utilizados

                comentario_usuario = ""

            except ErrorGeneracionReceta as error:
                # Recupera los datos de la receta anterior para mantener disponible su finalización.
                alimentos_utilizados = request.session.get(
                    "alimentos_utilizados_receta",
                    []
                )

                alimentos_usados_ids = []

                for alimento in alimentos_utilizados:
                    alimentos_usados_ids.append(alimento["id"])

                messages.error(request, str(error))

        elif accion == "finalizar_receta":
            receta_generada = request.POST.get("receta_generada", "")
            # Recupera de la sesión los alimentos utilizados en la receta actual.
            alimentos_utilizados = request.session.get(
                "alimentos_utilizados_receta",
                []
            )

            alimentos_usados_ids = [
                alimento["id"]
                for alimento in alimentos_utilizados
            ]

            if not alimentos_utilizados:
                messages.error(
                    request,
                    "No hay una receta pendiente para actualizar la despensa."
                )
            else:
                exito, mensaje = finalizar_receta(
                    request.user,
                    alimentos_utilizados,
                )

                if exito:
                    # Elimina de la sesión los datos de la receta
                    # una vez actualizada correctamente la despensa.
                    request.session.pop(
                        "alimentos_utilizados_receta",
                        None
                    )

                    messages.success(
                        request,
                        mensaje
                    )

                    return redirect("despensa:listado_alimentos")

                messages.error(
                    request,
                    mensaje
                )

    return render(
        request,
        "despensa/generar_recetas.html",
        {
            "alimentos": alimentos,
            "receta_generada": receta_generada,
            "alimentos_seleccionados_ids": alimentos_seleccionados_ids,
            "alimentos_usados_ids": alimentos_usados_ids,
            "alimentos_utilizados": alimentos_utilizados,
            "indicaciones_usuario": indicaciones_usuario,
            "comentario_usuario": comentario_usuario,
        }
    )