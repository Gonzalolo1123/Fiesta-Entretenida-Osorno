from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ImagenReferencia, ItemInventario


@receiver(post_save, sender=ImagenReferencia)
def crear_producto_desde_referencia(sender, instance: ImagenReferencia, created: bool, **kwargs):
    """
    Si se sube una ImagenReferencia sin producto asociado, crea automáticamente un
    ItemInventario usando el título/descripcion y usa la misma imagen como foto.
    """
    if not created:
        return
    if instance.producto_id:
        return

    nombre = (instance.titulo or "").strip() or "Producto sin nombre"
    descripcion = (instance.descripcion or "").strip()

    producto = ItemInventario.objects.create(
        nombre=nombre,
        descripcion=descripcion,
        foto=instance.imagen,
        activo=True,
    )

    # Evita loop: usamos update para no disparar lógica de create nuevamente.
    ImagenReferencia.objects.filter(pk=instance.pk).update(producto=producto)
