from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from FiestaEntreOso_app.models import ImagenReferencia


class Command(BaseCommand):
    help = "Importa archivos existentes en media/referencias/ creando ImagenReferencia (y producto automático)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            dest="dir",
            default=None,
            help="Ruta a la carpeta de referencias (por defecto MEDIA_ROOT/referencias).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base_dir = options.get("dir")
        carpeta = Path(base_dir) if base_dir else (Path(settings.MEDIA_ROOT) / "referencias")

        if not carpeta.exists() or not carpeta.is_dir():
            self.stdout.write(self.style.ERROR(f"No existe la carpeta: {carpeta}"))
            return

        extensiones = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        archivos = [p for p in carpeta.iterdir() if p.is_file() and p.suffix.lower() in extensiones]
        if not archivos:
            self.stdout.write(self.style.WARNING(f"No hay imágenes para importar en: {carpeta}"))
            return

        creadas = 0
        for path in sorted(archivos):
            # Evita duplicados por nombre de archivo ya importado
            ya = ImagenReferencia.objects.filter(imagen__endswith=f"/{path.name}").exists()
            if ya:
                continue

            titulo = path.stem.replace("_", " ").replace("-", " ").strip().title()
            with path.open("rb") as f:
                ref = ImagenReferencia(titulo=titulo, descripcion="")
                ref.imagen.save(path.name, File(f), save=True)
                creadas += 1

        self.stdout.write(self.style.SUCCESS(f"Importadas {creadas} imágenes."))
