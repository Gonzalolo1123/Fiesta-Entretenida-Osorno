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
