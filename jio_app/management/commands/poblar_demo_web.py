from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from jio_app.models import (
    Cliente,
    DetalleReserva,
    GastoOperativo,
    Instalacion,
    Juego,
    Material,
    PrecioTemporada,
    Promocion,
    Proveedor,
    Repartidor,
    Reserva,
    Retiro,
    Usuario,
    Vehiculo,
)


@dataclass(frozen=True)
class RangoFechas:
    inicio: date
    fin: date

    def random_date(self) -> date:
        if self.fin < self.inicio:
            raise ValueError("RangoFechas inválido")
        dias = (self.fin - self.inicio).days
        return self.inicio + timedelta(days=random.randint(0, dias))


class Command(BaseCommand):
    help = (
        "Puebla la BD con datos demo (marzo/abril): arriendos (reservas), repartos "
        "(instalación/retiro), gastos operativos, promociones, precios por temporadas y materiales."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--arriendos",
            type=int,
            default=12,
            help="Cantidad de arriendos a crear (10-15 recomendado). Default: 12",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Año para las fechas de marzo/abril. Default: año actual",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=202603,
            help="Seed para aleatoriedad reproducible. Default: 202603",
        )

    def handle(self, *args, **options):
        arriendos = int(options["arriendos"])
        year = options["year"] or timezone.now().date().year
        seed = int(options["seed"])

        if arriendos <= 0:
            self.stdout.write(self.style.ERROR("El parámetro --arriendos debe ser > 0"))
            return

        random.seed(seed)

        juegos = list(Juego.objects.filter(estado__iexact="habilitado"))
        if not juegos:
            self.stdout.write(self.style.ERROR("No hay juegos habilitados. Ejecuta primero poblar_juegos/agregar_juegos."))
            return

        self.stdout.write(self.style.SUCCESS("Iniciando poblamiento demo (marzo/abril)..."))

        with transaction.atomic():
            admin = self._get_or_create_admin()
            clientes = self._get_or_create_clientes(min_count=8)
            repartidores = self._get_or_create_repartidores(min_count=2)
            vehiculos = self._get_or_create_vehiculos(min_count=2)
            proveedores = self._get_or_create_proveedores(min_count=3)
            self._get_or_create_materiales(proveedores, min_count=12)
            self._get_or_create_precios_temporada(juegos, year=year)
            promos = self._get_or_create_promociones(juegos, year=year)

            rango = RangoFechas(date(year, 3, 1), date(year, 4, 30))
            reservas = self._crear_arriendos(
                cantidad=arriendos,
                rango=rango,
                clientes=clientes,
                juegos=juegos,
                repartidores=repartidores,
                promos=promos,
            )
            self._crear_gastos_operativos(
                admin=admin,
                vehiculos=vehiculos,
                reservas=reservas,
                rango=rango,
            )

        self.stdout.write(self.style.SUCCESS("Listo. Datos demo creados."))
        self.stdout.write(self.style.SUCCESS(f"- Arriendos (reservas): {arriendos} (marzo/abril {year})"))
        self.stdout.write(self.style.SUCCESS("- Repartos: 1 instalación + 1 retiro por reserva"))
        self.stdout.write(self.style.SUCCESS("- Promociones / Temporadas / Materiales / Gastos: creados/asegurados"))

    def _get_or_create_admin(self) -> Usuario:
        admin = Usuario.objects.filter(tipo_usuario="administrador").first()
        if admin:
            return admin
        admin, _ = Usuario.objects.get_or_create(
            username="demo_admin",
            defaults={
                "email": "demo_admin@jio.local",
                "tipo_usuario": "administrador",
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
                "first_name": "Demo",
                "last_name": "Admin",
            },
        )
        if not admin.has_usable_password():
            admin.set_password("demo12345")
            admin.save(update_fields=["password"])
        return admin

    def _get_or_create_clientes(self, min_count: int) -> list[Cliente]:
        clientes = list(Cliente.objects.select_related("usuario").all())
        if len(clientes) >= min_count:
            return clientes

        nombres = [
            ("Camila", "Muñoz"),
            ("Diego", "González"),
            ("Valentina", "Rojas"),
            ("Benjamín", "Soto"),
            ("Ignacia", "Silva"),
            ("Joaquín", "Torres"),
            ("Florencia", "Díaz"),
            ("Matías", "Pérez"),
            ("Antonia", "Reyes"),
            ("Tomás", "Contreras"),
        ]

        while len(clientes) < min_count:
            nombre, apellido = random.choice(nombres)
            base = f"demo_{self._slug(nombre)}_{self._slug(apellido)}"
            username = base
            i = 1
            while Usuario.objects.filter(username=username).exists():
                username = f"{base}{i}"
                i += 1

            rut = f"{random.randint(10000000, 25999999)}-{random.randint(0, 9)}"
            while Cliente.objects.filter(rut=rut).exists():
                rut = f"{random.randint(10000000, 25999999)}-{random.randint(0, 9)}"

            u = Usuario.objects.create_user(
                username=username,
                email=f"{username}@demo.local",
                password="demo12345",
                first_name=nombre,
                last_name=apellido,
                tipo_usuario="cliente",
                telefono=f"+569{random.randint(10000000, 99999999)}",
                is_active=True,
            )
            c = Cliente.objects.create(
                usuario=u,
                rut=rut,
                tipo_cliente=random.choice(["particular", "empresa"]),
            )
            clientes.append(c)

        return clientes

    def _get_or_create_repartidores(self, min_count: int) -> list[Repartidor]:
        repartidores = list(Repartidor.objects.select_related("usuario").all())
        if len(repartidores) >= min_count:
            return repartidores

        nombres = [
            ("Sergio", "Vera"),
            ("Paula", "Gutiérrez"),
            ("Nicolás", "Ramírez"),
            ("Fernanda", "Castro"),
        ]
        while len(repartidores) < min_count:
            nombre, apellido = random.choice(nombres)
            base = f"demo_delivery_{self._slug(nombre)}_{self._slug(apellido)}"
            username = base
            i = 1
            while Usuario.objects.filter(username=username).exists():
                username = f"{base}{i}"
                i += 1

            u = Usuario.objects.create_user(
                username=username,
                email=f"{username}@demo.local",
                password="demo12345",
                first_name=nombre,
                last_name=apellido,
                tipo_usuario="repartidor",
                telefono=f"+569{random.randint(10000000, 99999999)}",
                is_active=True,
            )
            r = Repartidor.objects.create(
                usuario=u,
                licencia_conducir=f"B{random.randint(100000, 999999)}",
                vehiculo=random.choice(["Camioneta", "Furgón", "Camión liviano"]),
                estado="Habilitado",
            )
            repartidores.append(r)

        return repartidores

    def _get_or_create_vehiculos(self, min_count: int) -> list[Vehiculo]:
        vehiculos = list(Vehiculo.objects.all())
        if len(vehiculos) >= min_count:
            return vehiculos

        marcas = [("Toyota", "Hilux"), ("Nissan", "NP300"), ("Hyundai", "H1"), ("Kia", "Frontier")]
        while len(vehiculos) < min_count:
            patente = self._patente_demo()
            if Vehiculo.objects.filter(patente=patente).exists():
                continue
            marca, modelo = random.choice(marcas)
            v = Vehiculo.objects.create(
                patente=patente,
                tipo=random.choice(["camioneta", "furgon"]),
                marca=marca,
                modelo=modelo,
                año=random.randint(2015, 2024),
                color=random.choice(["Blanco", "Gris", "Azul", "Rojo"]),
                kilometraje_actual=random.randint(20000, 180000),
                estado="disponible",
            )
            vehiculos.append(v)
        return vehiculos

    def _get_or_create_proveedores(self, min_count: int) -> list[Proveedor]:
        proveedores = list(Proveedor.objects.all())
        if len(proveedores) >= min_count:
            return proveedores

        catalogo = [
            ("Ferretería Osorno", "materiales"),
            ("Bencinera Ruta 5", "combustible"),
            ("Taller Don Luis", "mantenimiento"),
            ("Servicios Andinos", "servicios"),
        ]
        while len(proveedores) < min_count:
            nombre, tipo = random.choice(catalogo)
            base = nombre
            if Proveedor.objects.filter(nombre=base).exists():
                base = f"{nombre} {random.randint(2, 99)}"
            p = Proveedor.objects.create(
                nombre=base,
                tipo_proveedor=tipo,
                rut=f"{random.randint(76000000, 79999999)}-{random.randint(0, 9)}",
                contacto_nombre=random.choice(["Andrea", "Marcelo", "Carolina", "Luis"]),
                telefono=f"+569{random.randint(10000000, 99999999)}",
                email=f"contacto_{self._slug(base)}@proveedor.local",
                direccion="Osorno, Chile",
                servicios_ofrecidos="Proveedor demo generado automáticamente",
                activo=True,
            )
            proveedores.append(p)
        return proveedores

    def _get_or_create_materiales(self, proveedores: list[Proveedor], min_count: int) -> list[Material]:
        materiales = list(Material.objects.all())
        if len(materiales) >= min_count:
            return materiales

        nombres = [
            ("Bomba eléctrica 2000W", "bomba", "unidad"),
            ("Extensión 10m", "extension", "unidad"),
            ("Cinta americana", "accesorio", "unidad"),
            ("Kit parches PVC", "repuesto", "caja"),
            ("Desinfectante", "limpieza", "litro"),
            ("Guantes nitrilo", "limpieza", "caja"),
            ("Martillo", "herramienta", "unidad"),
            ("Destornillador", "herramienta", "unidad"),
            ("Cuerda 20m", "accesorio", "metro"),
            ("Amarras plásticas", "accesorio", "caja"),
            ("Lubricante", "otro", "litro"),
        ]

        while len(materiales) < min_count:
            nombre, categoria, unidad = random.choice(nombres)
            if Material.objects.filter(nombre=nombre).exists():
                nombre = f"{nombre} {random.randint(2, 50)}"
            m = Material.objects.create(
                nombre=nombre,
                categoria=categoria,
                descripcion="Material demo",
                stock_actual=random.randint(2, 25),
                stock_minimo=random.randint(1, 5),
                unidad_medida=unidad,
                precio_unitario=Decimal(str(random.randint(1500, 45000))),
                estado="disponible",
                ubicacion=random.choice(["Bodega 1", "Bodega 2", "Camión", "Taller"]),
                proveedor=random.choice(proveedores) if proveedores and random.random() < 0.7 else None,
                fecha_ultima_compra=timezone.now().date() - timedelta(days=random.randint(1, 60)),
            )
            materiales.append(m)
        return materiales

    def _get_or_create_precios_temporada(self, juegos: list[Juego], year: int) -> None:
        # Temporada Alta: Mar-Abr, Temporada Baja: May-Ago (simple para demo)
        for juego in juegos:
            base = int(juego.precio_base)
            # Alta (Mar-Abr)
            PrecioTemporada.objects.get_or_create(
                juego=juego,
                temporada="Alta",
                mes_inicio=3,
                defaults={
                    "mes_fin": 4,
                    "precio_arriendo": int(base * 1.2),
                    "descuento_porcentaje": 0,
                },
            )
            # Baja (May-Ago)
            PrecioTemporada.objects.get_or_create(
                juego=juego,
                temporada="Baja",
                mes_inicio=5,
                defaults={
                    "mes_fin": 8,
                    "precio_arriendo": int(base * 0.95),
                    "descuento_porcentaje": 5,
                },
            )

    def _get_or_create_promociones(self, juegos: list[Juego], year: int) -> list[Promocion]:
        inicio = date(year, 3, 1)
        fin = date(year, 4, 30)
        promos = list(Promocion.objects.filter(fecha_inicio__lte=fin, fecha_fin__gte=inicio))
        if len(promos) >= 3:
            return promos

        def codigo_unico(prefijo: str) -> str:
            while True:
                code = f"{prefijo}{random.randint(100, 9999)}"
                if not Promocion.objects.filter(codigo=code).exists():
                    return code

        creadas: list[Promocion] = []

        p1 = Promocion.objects.create(
            codigo=codigo_unico("MAR"),
            nombre="Marzo Feliz",
            descripcion="10% de descuento en marzo/abril",
            tipo_descuento="porcentaje",
            valor_descuento=Decimal("10"),
            fecha_inicio=inicio,
            fecha_fin=fin,
            monto_minimo=Decimal("0"),
            limite_usos=0,
            usos_actuales=0,
            estado="activa",
        )
        # Aplica a todos (juegos vacío)
        creadas.append(p1)

        # Cupón monto fijo, a juegos específicos
        p2 = Promocion.objects.create(
            codigo=codigo_unico("ABR"),
            nombre="Cupón Abril",
            descripcion="$15.000 de descuento (selección de juegos)",
            tipo_descuento="monto_fijo",
            valor_descuento=Decimal("15000"),
            fecha_inicio=date(year, 4, 1),
            fecha_fin=date(year, 4, 30),
            monto_minimo=Decimal("60000"),
            limite_usos=50,
            usos_actuales=random.randint(0, 10),
            estado="activa",
        )
        if juegos:
            p2.juegos.set(random.sample(juegos, k=min(4, len(juegos))))
        creadas.append(p2)

        # Envío gratis (demo)
        p3 = Promocion.objects.create(
            codigo=codigo_unico("ENV"),
            nombre="Envío Gratis",
            descripcion="Descuento equivalente al costo de distancia (hasta $20.000)",
            tipo_descuento="envio_gratis",
            valor_descuento=Decimal("0"),
            fecha_inicio=inicio,
            fecha_fin=fin,
            monto_minimo=Decimal("50000"),
            limite_usos=0,
            usos_actuales=random.randint(0, 20),
            estado="activa",
        )
        creadas.append(p3)

        return promos + creadas

    def _crear_arriendos(
        self,
        cantidad: int,
        rango: RangoFechas,
        clientes: list[Cliente],
        juegos: list[Juego],
        repartidores: list[Repartidor],
        promos: list[Promocion],
    ) -> list[Reserva]:
        direcciones = [
            "Av. Mackenna 1200, Osorno, Chile",
            "Calle Arturo Prat 450, Osorno, Chile",
            "Av. O'Higgins 980, Osorno, Chile",
            "Calle Los Carrera 210, Osorno, Chile",
            "Av. República 150, Osorno, Chile",
        ]

        estados_reserva = ["Pendiente", "Confirmada", "completada"]
        estados_inst = ["programada", "realizada", "pendiente"]
        estados_ret = ["programado", "realizado", "pendiente"]
        metodos_pago = ["efectivo", "transferencia", "otro"]

        reservas_creadas: list[Reserva] = []
        juegos_habilitados = juegos

        for i in range(cantidad):
            fecha_evento = rango.random_date()
            cliente = random.choice(clientes)

            hora_instalacion = time(random.choice([9, 10, 11, 12, 13]), random.choice([0, 30]))
            hora_retiro = time(random.choice([17, 18, 19, 20]), random.choice([0, 30]))

            distancia_km = random.choice([0, 0, 3, 5, 8, 10, 15, 20, 25])
            precio_distancia = Decimal(str(distancia_km * 1000))
            horas_extra = random.choice([0, 0, 0, 1, 2])
            precio_horas_extra = Decimal(str(horas_extra * 10000))

            reserva = Reserva.objects.create(
                cliente=cliente,
                fecha_evento=fecha_evento,
                hora_instalacion=hora_instalacion,
                hora_retiro=hora_retiro,
                direccion_evento=random.choice(direcciones),
                estado=random.choice(estados_reserva),
                observaciones=f"DEMO marzo/abril #{i+1}",
                distancia_km=distancia_km,
                precio_distancia=precio_distancia,
                horas_extra=horas_extra,
                precio_horas_extra=precio_horas_extra,
                total_reserva=Decimal("0"),
            )

            # 1-2 juegos por reserva
            selected = random.sample(juegos_habilitados, k=min(len(juegos_habilitados), random.choice([1, 1, 2])))
            total_juegos = Decimal("0")
            for juego in selected:
                precio_unitario = Decimal(str(juego.precio_base))
                DetalleReserva.objects.create(
                    reserva=reserva,
                    juego=juego,
                    cantidad=1,
                    precio_unitario=precio_unitario,
                    subtotal=precio_unitario,
                )
                total_juegos += precio_unitario

            # Promoción (40% de probabilidad)
            promocion = None
            if promos and random.random() < 0.4:
                promocion = random.choice([p for p in promos if p.estado == "activa"] or promos)

            descuento = Decimal("0")
            if promocion and self._promocion_aplica(promocion, fecha_evento, total_juegos):
                if promocion.tipo_descuento == "porcentaje":
                    descuento = (total_juegos * promocion.valor_descuento / Decimal("100")).quantize(Decimal("1.00"))
                elif promocion.tipo_descuento == "monto_fijo":
                    descuento = min(Decimal(promocion.valor_descuento), total_juegos)
                elif promocion.tipo_descuento == "envio_gratis":
                    descuento = min(precio_distancia, Decimal("20000"))
                elif promocion.tipo_descuento == "2x1":
                    descuento = Decimal("0")

            subtotal = total_juegos + precio_distancia + precio_horas_extra
            total_final = max(Decimal("0"), subtotal - descuento)

            reserva.promocion = promocion
            reserva.monto_descuento = descuento
            reserva.total_reserva = total_final
            reserva.save(update_fields=["promocion", "monto_descuento", "total_reserva"])

            # Repartos: instalación + retiro
            rep_inst = random.choice(repartidores) if repartidores else None
            rep_ret = random.choice(repartidores) if repartidores else None

            Instalacion.objects.create(
                reserva=reserva,
                repartidor=rep_inst,
                fecha_instalacion=fecha_evento,
                hora_instalacion=hora_instalacion,
                direccion_instalacion=reserva.direccion_evento,
                telefono_cliente=cliente.usuario.telefono or "+56900000000",
                estado_instalacion=random.choice(estados_inst),
                observaciones_instalacion="Entrega demo",
                metodo_pago=random.choice(metodos_pago) if random.random() < 0.5 else None,
            )

            Retiro.objects.create(
                reserva=reserva,
                repartidor=rep_ret,
                fecha_retiro=fecha_evento,
                hora_retiro=hora_retiro,
                estado_retiro=random.choice(estados_ret),
                observaciones_retiro="Retiro demo",
            )

            reservas_creadas.append(reserva)

        return reservas_creadas

    def _promocion_aplica(self, promocion: Promocion, fecha_evento: date, total_juegos: Decimal) -> bool:
        if promocion.estado != "activa":
            return False
        if not (promocion.fecha_inicio <= fecha_evento <= promocion.fecha_fin):
            return False
        if total_juegos < (promocion.monto_minimo or Decimal("0")):
            return False
        if promocion.limite_usos and promocion.usos_actuales >= promocion.limite_usos:
            return False
        return True

    def _crear_gastos_operativos(
        self,
        admin: Usuario,
        vehiculos: list[Vehiculo],
        reservas: list[Reserva],
        rango: RangoFechas,
    ) -> None:
        categorias = [choice[0] for choice in GastoOperativo.CATEGORIA_CHOICES]
        metodos_pago = [choice[0] for choice in GastoOperativo.METODO_PAGO_CHOICES]

        descripciones = {
            "combustible": ["Bencina reparto", "Diesel furgón", "Carga combustible"],
            "mantenimiento": ["Cambio de aceite", "Revisión frenos", "Alineación y balanceo"],
            "publicidad": ["Campaña redes sociales", "Impresión flyers"],
            "servicios": ["Internet oficina", "Luz bodega", "Agua"],
            "materiales": ["Compra insumos", "Repuestos menores", "Productos limpieza"],
            "otros": ["Gasto administrativo", "Imprevistos"],
        }

        # Creamos pocos gastos (demo) dentro del rango marzo/abril.
        cantidad = min(30, max(10, len(reservas) * 2))
        for _ in range(cantidad):
            categoria = random.choice(categorias)
            descripcion = random.choice(descripciones.get(categoria, ["Gasto operativo"]))
            fecha_gasto = rango.random_date()
            monto = Decimal(str(random.randint(5000, 180000)))
            vehiculo = random.choice(vehiculos) if vehiculos and random.random() < 0.35 else None
            reserva = random.choice(reservas) if reservas and random.random() < 0.25 else None

            GastoOperativo.objects.create(
                categoria=categoria,
                descripcion=descripcion,
                monto=monto,
                fecha_gasto=fecha_gasto,
                metodo_pago=random.choice(metodos_pago),
                vehiculo=vehiculo,
                reserva=reserva,
                observaciones="DEMO marzo/abril",
                registrado_por=admin,
            )

    def _slug(self, s: str) -> str:
        s = s.strip().lower()
        repl = {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u",
            "ñ": "n",
            "ü": "u",
            " ": "_",
            "'": "",
        }
        for k, v in repl.items():
            s = s.replace(k, v)
        s = "".join(ch for ch in s if ch.isalnum() or ch == "_")
        return s

    def _patente_demo(self) -> str:
        letras = "".join(random.choices(string.ascii_uppercase, k=4))
        numeros = "".join(random.choices(string.digits, k=2))
        return f"{letras}{numeros}"
