from django.contrib.auth import login, logout
from django.shortcuts import redirect, render

from .forms import RegistroUsuarioForm

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    InicioSesionSerializer,
    RegistroUsuarioSerializer,
)


class RegistroUsuarioAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistroUsuarioSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        usuario = serializer.save()

        return Response(
            {
                "mensaje": "Usuario registrado correctamente.",
                "usuario": {
                    "username": usuario.username,
                    "email": usuario.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )
    
class InicioSesionAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InicioSesionSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        usuario = serializer.validated_data["usuario"]

        login(request, usuario)

        return Response(
            {
                "mensaje": "Sesión iniciada correctamente.",
                "usuario": {
                    "username": usuario.username,
                    "email": usuario.email,
                },
            },
            status=status.HTTP_200_OK,
        )


class CerrarSesionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)

        return Response(
            {
                "mensaje": "Sesión cerrada correctamente.",
            },
            status=status.HTTP_200_OK,
        )
        
def registro_web(request):
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("inicio")
    else:
        form = RegistroUsuarioForm()

    return render(request, "usuarios/registro.html", {"form": form})