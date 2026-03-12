import os

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render
from .models import ItemInventario, Cliente, ImagenReferencia


def index(request):
    """
    Página principal: historia, catálogo (inventario activo) y actividades.
    """
    items = ItemInventario.objects.filter(activo=True).order_by("categoria", "nombre")
    referencias = ImagenReferencia.objects.select_related("producto").all()[:12]

    context = {
        "items_inventario": items,
        "imagenes_referencia": referencias,
    }
    return render(request, "FiestaEntreOso_app/index.html", context)


def enviar_contacto(request):
    """
    Recibe el formulario de contacto y guarda como Cliente (con mensaje en notas).
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    nombre = request.POST.get("nombre", "").strip()
    email = request.POST.get("email", "").strip()
    telefono = request.POST.get("telefono", "").strip()
    mensaje = request.POST.get("mensaje", "").strip()

    if not nombre or not (email or telefono) or not mensaje:
        return JsonResponse(
            {
                "ok": False,
                "error": "Por favor completa tu nombre, un medio de contacto y el mensaje.",
            },
            status=400,
        )

    Cliente.objects.create(
        nombre=nombre,
        email=email or "",
        telefono=telefono or "",
        notas=mensaje,
    )
    return JsonResponse({"ok": True})


def bootstrap_admin(request):
    """
    Endpoint temporal para crear superusuario en producción sin Shell.
    Protegido por token y variables de entorno.
    """
    token = (request.GET.get("token") or "").strip()
    esperado = (os.environ.get("BOOTSTRAP_ADMIN_TOKEN") or "").strip()
    if not esperado or token != esperado:
        return JsonResponse({"ok": False, "error": "No autorizado"}, status=403)

    username = (os.environ.get("BOOTSTRAP_ADMIN_USERNAME") or "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD") or ""
    email = (os.environ.get("BOOTSTRAP_ADMIN_EMAIL") or "").strip()

    if not username or not password:
        return JsonResponse(
            {"ok": False, "error": "Faltan variables BOOTSTRAP_ADMIN_USERNAME/PASSWORD"},
            status=500,
        )

    User = get_user_model()
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email},
    )

    # Asegura permisos aunque ya exista
    user.is_staff = True
    user.is_superuser = True
    if created or not user.has_usable_password():
        user.set_password(password)
    user.email = email or user.email
    user.save()

    return JsonResponse(
        {
            "ok": True,
            "created": created,
            "username": user.username,
            "admin_url": "/admin/",
            "nota": "Usa este endpoint una vez y luego elimínalo del código.",
        }
    )
