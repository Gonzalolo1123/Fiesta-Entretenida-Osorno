"""
Modelos sencillos para Fiesta Entre Oso:
- Inventario: productos/juegos que la empresa ofrece en arriendo
- Cliente: personas que contactan o han contratado
- ImagenReferencia: fotos de referencia (productos, eventos)
"""
from django.db import models


class ItemInventario(models.Model):
    """Producto o juego inflable que la empresa tiene para arriendo."""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True)  # ej: inflable, juego, decoración
    dimensiones = models.CharField(max_length=100, blank=True)
    capacidad_personas = models.PositiveIntegerField(null=True, blank=True)
    precio_base = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    foto = models.ImageField(upload_to="inventario/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "item de inventario"
        verbose_name_plural = "inventario"
        ordering = ["categoria", "nombre"]

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    """Cliente o contacto que escribe por el formulario o con quien se ha trabajado."""
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    direccion = models.CharField(max_length=300, blank=True)
    notas = models.TextField(blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return self.nombre or self.email or self.telefono or "Sin nombre"


class ImagenReferencia(models.Model):
    """Foto de referencia: puede ser de un producto o evento genérico."""
    titulo = models.CharField(max_length=200, blank=True)
    imagen = models.ImageField(upload_to="referencias/")
    descripcion = models.TextField(blank=True)
    producto = models.ForeignKey(
        ItemInventario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="imagenes_referencia",
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "imagen de referencia"
        verbose_name_plural = "imágenes de referencia"
        ordering = ["-fecha_subida"]

    def __str__(self):
        return self.titulo or self.imagen.name
