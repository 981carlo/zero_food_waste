from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Alimento
from .serializers import AlimentoSerializer
from .forms import AlimentoForm


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
        form = AlimentoForm()

    return render(
        request,
        "despensa/formulario_alimento.html",
        {"form": form}
    )
    

@login_required(login_url="usuarios:login_web")
def editar_alimento_web(request, alimento_id):
    alimento = get_object_or_404(
        Alimento,
        pk=alimento_id,
        usuario=request.user
    )

    if request.method == "POST":
        form = AlimentoForm(request.POST, instance=alimento)

        if form.is_valid():
            form.save()
            
            messages.success(request, "Alimento actualizado correctamente.")
            
            return redirect("despensa:listado_alimentos")
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
    alimento = get_object_or_404(
        Alimento,
        pk=alimento_id,
        usuario=request.user
    )

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

    return render(
        request,
        "despensa/generar_recetas.html",
        {"alimentos": alimentos}
    )