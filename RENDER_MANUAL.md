# Desplegar en Render sin Blueprint (sin tarjeta)

En lugar de **Blueprint**, crea un **Web Service** a mano y copia estos valores.

## Pasos

1. Entra en [dashboard.render.com](https://dashboard.render.com) e inicia sesión con GitHub.

2. **New +** → **Web Service** (no elijas Blueprint).

3. Conecta el repo **Fiesta-Entretenida-Osorno** (autoriza si pide).

4. Rellena:

   | Campo | Valor |
   |-------|--------|
   | **Name** | `fiesta-entre-oso` (o el que quieras) |
   | **Region** | Oregon (US West) o el más cercano |
   | **Branch** | `main` |
   | **Runtime** | Python 3 |
   | **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput` |
   | **Start Command** | `gunicorn JIO.wsgi:application --bind 0.0.0.0:$PORT` |

5. **Environment** (Environment Variables):

   - **Key:** `DJANGO_SETTINGS_MODULE` → **Value:** `JIO.settings`
   - **Key:** `SECRET_KEY` → **Value:** (usa **Generate** o inventa una clave larga)
   - **Key:** `DEBUG` → **Value:** `False`

   **Para producción (datos persistentes):** añade `DATABASE_URL` con una base PostgreSQL — ver sección "PostgreSQL" más abajo.
   **Para imágenes en la nube:** añade `CLOUDINARY_URL` — ver sección "Configurar Cloudinary".

6. **Create Web Service**. Render hará el primer deploy.

7. Cuando termine, entra a la URL que te den (ej. `https://fiesta-entre-oso.onrender.com`). Para crear el usuario del admin: en el servicio → **Shell** → ejecuta `python manage.py createsuperuser`.

---

## PostgreSQL en producción

El sitio usa **PostgreSQL** en producción cuando existe la variable `DATABASE_URL`. Sin ella, en Render se usa SQLite y **todos los datos se pierden en cada deploy**.

1. En Render: **New +** → **PostgreSQL**.
2. Crea la base (plan Free está bien), espera a que esté lista.
3. En la base → **Info** → copia **Internal Database URL**.
4. En tu **Web Service** → **Environment** → **Add Environment Variable**:
   - **Key:** `DATABASE_URL`
   - **Value:** la URL que copiaste (Internal Database URL).
5. Guarda y haz **Manual Deploy** (o un push). En el build se ejecutará `migrate` y las tablas se crearán en Postgres. Luego en **Shell** ejecuta `python manage.py createsuperuser` para el admin.

---

## Configurar Cloudinary (respaldo de imágenes)

Para que las fotos del inventario y de referencia se suban y sirvan desde Cloudinary en tu Web Service:

1. **Cuenta en Cloudinary**  
   Entra en [cloudinary.com](https://cloudinary.com), crea cuenta y en el **Dashboard** anota: **Cloud name**, **API Key** y **API Secret**.

2. **Variable en Render**  
   En tu Web Service → **Environment** → **Add Environment Variable**:
   - **Key:** `CLOUDINARY_URL`
   - **Value:** `cloudinary://TU_API_KEY:TU_API_SECRET@TU_CLOUD_NAME` (reemplaza por tus valores, sin espacios).  
   Ejemplo: `cloudinary://123456789012345:AbCdEfGhIjKlMnOpQrStUvWxYz@mi-cloud`

3. **Guardar y redesplegar**  
   Guarda la variable y haz **Manual Deploy** → **Deploy latest commit** (o un push). En el siguiente deploy el sitio usará Cloudinary para las imágenes del admin. Sin `CLOUDINARY_URL`, las imágenes subidas en Render se pierden en cada deploy porque el disco es efímero.

---

**Plan Free:** el servicio se “duerme” tras ~15 min sin visitas; la primera visita puede tardar unos 50 segundos en responder.
