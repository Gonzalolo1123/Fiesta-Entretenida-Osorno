from django.contrib import admin
from .models import ItemInventario, Cliente, ImagenReferencia


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "precio_base", "activo", "creado")
    list_filter = ("activo", "categoria")
    search_fields = ("nombre", "descripcion")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "email", "telefono", "fecha_registro")
    search_fields = ("nombre", "email", "telefono")


@admin.register(ImagenReferencia)
class ImagenReferenciaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "producto", "fecha_subida")
    list_filter = ("producto",)
    search_fields = ("titulo", "descripcion")
