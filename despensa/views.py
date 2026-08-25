from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Alimento
from .serializers import AlimentoSerializer
from .forms import AlimentoForm
from .services import generar_receta_con_llm, modificar_receta_con_llm, ErrorGeneracionReceta


class AlimentoViewSet(viewsets.ModelViewSet):
    serializer_class = AlimentoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alimento.objects.filter(
            usuario=self.request.user
        ).order_by("fecha_caducidad")

    def perform_create(self, serializer):
        serializer.save(
            usuario=self.request.user
        )

    @action(detail=False, methods=["get"], url_path="proximos")
    def proximos(self, request):
        hoy = timezone.localdate()
        limite = hoy + timedelta(days=7)

        alimentos = self.get_queryset().filter(
            fecha_caducidad__gte=hoy,
            fecha_caducidad__lte=limite
        )

        serializer = self.get_serializer(alimentos, many=True)
        return Response(serializer.data)


@login_required(login_url="usuarios:login_web")
def listado_alimentos_web(request):
    alimentos = Alimento.objects.filter(
        usuario=request.user
    ).order_by("fecha_caducidad")

    return render(
        request,
        "despensa/listado_alimentos.html",
        {"alimentos": alimentos}
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
def generar_recetas_web(request):
    alimentos = Alimento.objects.filter(
        usuario=request.user
    ).order_by("fecha_caducidad")

    receta_generada = None
    alimentos_seleccionados_ids = []
    alimentos_usados_ids = []
    comentario_usuario = ""

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "modificar_receta":
            receta_generada = request.POST.get("receta_generada", "")
            comentario_usuario = request.POST.get("comentario_usuario", "")
            alimentos_usados_ids = request.POST.getlist("alimentos_usados")
            alimentos_usados = alimentos.filter(pk__in=alimentos_usados_ids)

            try:
                receta_generada = modificar_receta_con_llm(
                    receta_generada,
                    alimentos_usados,
                    comentario_usuario,
                )
                comentario_usuario = ""
            except ErrorGeneracionReceta as error:
                messages.error(request, str(error))

        else:
            if not alimentos.exists():
                messages.error(
                    request,
                    "No puedes generar una receta porque todavía no tienes alimentos registrados."
                )
            else:
                alimentos_seleccionados_ids = request.POST.getlist("alimentos_seleccionados")

                if alimentos_seleccionados_ids:
                    alimentos_para_receta = alimentos.filter(
                        pk__in=alimentos_seleccionados_ids
                    )
                else:
                    alimentos_para_receta = alimentos
                
                alimentos_usados_ids = [
                    str(alimento.id)
                    for alimento in alimentos_para_receta
                ]

                try:
                    receta_generada = generar_receta_con_llm(
                        alimentos_para_receta,
                        usar_todos_los_alimentos=bool(alimentos_seleccionados_ids),
                    )
                except ErrorGeneracionReceta as error:
                    messages.error(request, str(error))

    return render(
        request,
        "despensa/generar_recetas.html",
        {
            "alimentos": alimentos,
            "receta_generada": receta_generada,
            "alimentos_seleccionados_ids": alimentos_seleccionados_ids,
            "alimentos_usados_ids": alimentos_usados_ids,
            "comentario_usuario": comentario_usuario,
        }
    )