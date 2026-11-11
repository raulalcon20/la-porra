# Diario del curso

## Estado actual
- **Clase completada:** 6 · Docker Compose (6a y 6b)
- **Entorno:** Windows 11 + WSL2 Ubuntu 22.04, Docker Desktop 4.97, uv 0.13.6, Python 3.13, Postgres 18
- **Rutina al empezar:** abrir Docker Desktop → `cd ~/la-porra` → `eval "$(ssh-agent -s)" && ssh-add` → `git pull` → `code .` → `docker compose up -d`
- **Rutina al cerrar:** `git add` y `git status` desde la raíz → commit y push → `docker compose down` (**nunca** `-v`, salvo para empezar de cero a propósito)
- **Repo:** `raulalcon20/la-porra` (privado), en `~/la-porra`. Nombre de producto pendiente: "La Porra" es el nombre en clave; la marca se cambiará sin tocar los nombres internos (dominio).
- **Hecho:**
  - API FastAPI (`/health`, `/version`) con pydantic-settings, tests y ruff
  - Modelo SQLAlchemy (7 tablas) y migración inicial de Alembic
  - Imagen multi-stage sin privilegios, que ahora incluye `alembic.ini` y `migrations/`
  - `compose.yaml` en la raíz: `db` (postgres:18, volumen `pgdata`, healthcheck con `pg_isready`, puerto 5432) y `api` (build, `PORRA_DATABASE_URL` por interpolación con el host `db`, `depends_on` con `service_healthy`, puerto 8000)
  - `.env` (fuera de Git) y `.env.example` (en Git)
    - Etapa `dev` en el Dockerfile (dependencias de desarrollo y paquete en modo editable)
  - `compose.override.yaml` para desarrollo: build `target: dev` (imagen `porra-api:dev`), bind mounts de `src/` y `tests/`, `--reload` y puerto 5432 de `db`. La base `compose.yaml` usa la imagen final (`porra-api:local`) sin el puerto de Postgres.
  - Tests y ruff dentro de Compose: `docker compose run --rm --no-deps api pytest -v`
- **Decisiones:**
  - Prefijo `PORRA_`; `PORRA_DATABASE_URL` obligatoria.
  - Postgres 18 con el volumen en `/var/lib/postgresql`.
  - Las credenciales de la base de datos tienen una sola fuente de verdad: el `.env`, interpolado en `compose.yaml`.
  - Las migraciones se ejecutan como un paso aparte (`docker compose run --rm api alembic upgrade head`), nunca en el `CMD`.
  - Tags: versión semántica + SHA; nunca se despliega `latest`.
- **Pendiente:** validar la configuración al arrancar (*fail fast*).
- **Ritmo:** el de las clases anteriores es el adecuado.
- **Siguiente paso:** Clase 7 · El ingestor: datos reales de LaLiga

## Cambios de alcance (decididos en la Clase 5b)
- **Plataforma de porras multicompetición**: un jugador puede estar en varias porras; cada porra pertenece a una competición y una temporada. El pronóstico es por jugador y partido, compartido entre porras.
- **La Máquina** solo puede unirse a porras de competiciones de tipo liga (empezamos con LaLiga, `PD`).
- **Champions League**: fases (fase de liga + eliminatorias). Cuenta el resultado de los 90 minutos. Se añade después de tener el flujo completo funcionando con LaLiga.
- **Interfaz**: el bot de Telegram (no WhatsApp: su API de grupos exige una cuenta verificada, está limitada a 8 participantes y no funciona con grupos ya existentes). El bot solo habla con la API, así que se pueden añadir otros canales como adaptadores.
- **Roadmap ajustado:**
  - Clase 7: ingestor parametrizado por código de competición (`PD` primero).
  - Clase 8 → **8a** (jugadores, pronósticos, puntuación) y **8b** (porras: crear, unirse con código de invitación, clasificación por porra, regla de La Máquina).
  - Clase 11: cada grupo de Telegram se asocia a una porra.
  - **Extensiones** (al final): Champions (eliminatorias + migración "¿quién pasa?" con punto extra) y una web sencilla con FastAPI + HTMX.

---

## Clase 1 · Instalación y repositorio

### Teoría

**Máquina virtual frente a contenedor**
- Una **VM** emula hardware mediante un hipervisor. Encima arranca un sistema operativo completo, con su propio kernel. Es pesada: tarda minutos en arrancar, ocupa gigas y reserva RAM aunque no la use.
- Un **contenedor** es un proceso normal del anfitrión, aislado por el kernel. **Comparte el kernel del anfitrión**, así que arranca en milisegundos y ocupa megas.
  - **Namespaces** limitan lo que el proceso **ve**: sus propios procesos, su red, su sistema de ficheros, su hostname...
  - **cgroups** limitan lo que el proceso **consume**: CPU, memoria...
- **Analogía:** una VM es una casa independiente con sus propios cimientos. Un contenedor es un piso en un edificio: cada uno tiene su puerta, pero todos comparten la estructura (el kernel).
- **Problema que resuelve Docker:** "en mi máquina funciona". La app se empaqueta con exactamente sus dependencias en una imagen, que se ejecuta igual en cualquier sitio.

**Docker en Windows**
- Los contenedores de Linux necesitan un kernel Linux. Windows no tiene, pero **WSL2** sí: es una VM ligera con un kernel Linux real (`uname -r` → `...microsoft-standard-WSL2`).
- Docker Desktop ejecuta su motor dentro de WSL2. Con la integración WSL, el comando `docker` funciona dentro de Ubuntu.

**Arquitectura de Docker y conceptos básicos**
- Docker es **cliente-servidor**. El *client* (el comando `docker`) habla con el *daemon* o *engine*, que es quien gestiona imágenes y contenedores. Por eso `docker version` muestra dos bloques.
- **Imagen**: plantilla de solo lectura, formada por **capas** apiladas.
- **Contenedor**: una instancia en ejecución de una imagen.
- **Registry**: almacén de imágenes. El de por defecto es Docker Hub, y `library/` contiene las imágenes oficiales. Funciona como apt o PyPI, pero para imágenes.
- **Tag**: etiqueta de versión (`hello-world:latest`). Si no se indica, se usa `latest`. Un tag puede cambiar con el tiempo.
- **Digest** (`sha256:...`): huella del contenido exacto. Siempre identifica la misma imagen byte a byte.
- Lo que hace `docker run hello-world` sin la imagen local:
  1. Busca la imagen en local.
  2. Como no está, hace pull de Docker Hub.
  3. Crea un contenedor a partir de la imagen.
  4. Lo ejecuta.
  5. Envía la salida a la terminal.
  6. El contenedor termina.

**uv y Python**
- **uv** sustituye a pip, venv y pyenv: instala versiones de Python, crea entornos virtuales y gestiona dependencias con un fichero de bloqueo (`uv.lock`) para tener instalaciones reproducibles.
- Pueden convivir varios Pythons: el de uv (`~/.local/share/uv/...`) y el del sistema (`/usr/bin/python3`). **El del sistema no se toca**, porque Ubuntu lo usa para sus propias herramientas.
- Ejecutar `curl ... | sh` implica confiar en el origen. Ante la duda, descargar el script y leerlo antes.

**SSH**
- Criptografía asimétrica:
  - La clave **privada** (`id_ed25519`, permisos `600`) no sale nunca de la máquina.
  - La **pública** (`.pub`) se le da a GitHub. GitHub te reta y tú demuestras que tienes la privada sin enviarla.
- Si roban la `.pub`, no pasa nada. Si roban la privada, pueden suplantarte. La **passphrase** la cifra en disco: es la última defensa. Si hay sospecha de robo, hay que borrarla en GitHub y generar otra.
- **known_hosts** guarda las huellas (*fingerprints*) de los servidores conocidos, para protegerte de ataques *man-in-the-middle*. La primera conexión hay que verificarla contra la huella oficial.
- La passphrase es **local**: no es la contraseña de GitHub. **ssh-agent** guarda la clave descifrada en memoria durante la sesión.

**Git**
- **`.git`** es el repositorio de verdad: historial, ramas y remotes. Los ficheros visibles son solo el directorio de trabajo.
- **Las tres zonas:**
  ```
  directorio de trabajo --add--> staging --commit--> repo local (.git) --push--> GitHub
  ```
- En `git status`:
  - *modified*: un fichero que Git ya seguía y que ha cambiado.
  - *untracked*: un fichero que Git nunca ha seguido.
- `origin` es el nombre convencional del remote. `origin/main` es la última posición de main que conoces de GitHub.
- **`.gitignore`** lista los ficheros que Git ignora (`.venv/`, `__pycache__/`, `.env`). Los secretos nunca van a Git: el historial es para siempre, aunque borres el fichero en un commit posterior.
- **Licencia MIT**: permisiva. Cualquiera puede reutilizar el código si mantiene el aviso de autoría. Sin licencia, nadie puede reutilizarlo legalmente.
- **Conventional Commits**: `tipo: descripción en imperativo`. Los tipos habituales son `feat`, `fix`, `docs` y `chore`. Permite generar changelogs automáticamente y deja un historial legible.

### Comandos clave
| Comando | Para qué |
|---|---|
| `wsl -l -v` | Listar distros de WSL y su versión (en PowerShell) |
| `uname -r` | Ver la versión del kernel |
| `docker version` | Ver las versiones del cliente y del servidor (engine) |
| `docker run hello-world` | Primer contenedor de prueba |
| `uv python install 3.13` | Instalar Python gestionado por uv |
| `uv python list --only-installed` | Ver los Pythons instalados |
| `ssh-keygen -t ed25519 -C "email"` | Generar un par de claves SSH |
| `ssh -T git@github.com` | Probar la autenticación con GitHub |
| `eval "$(ssh-agent -s)"` + `ssh-add` | Cargar la clave en el agente para la sesión |
| `git clone <url-ssh>` | Clonar un repo |
| `git status` / `git log --oneline` / `git remote -v` | Ver el estado, el historial y los remotes |
| `code .` | Abrir la carpeta actual en VS Code conectado a WSL |

### Lecciones de depuración
- Un "Failed to fetch" en VS Code fue un fallo puntual: lo primero es **reintentar**, que es lo más barato.
- Si persiste, mirar **View → Output → Extensions** y probar la red fuera de VS Code (`curl -I` en Ubuntu, `Test-NetConnection` en PowerShell) para aislar si el fallo está en Windows, en WSL o en la red.



## Clase 2 · Qué es de verdad un contenedor

### Teoría

**Imagen frente a contenedor**
- Imagen = **clase** (una plantilla de solo lectura). Contenedor = **objeto** (una instancia con su propio estado). De una misma imagen pueden salir muchos contenedores.
- **Capas**: una imagen es una pila de capas de solo lectura, superpuestas con **OverlayFS**. Cada contenedor añade encima su propia **capa escribible**.
- **Copy-on-write**: si un contenedor modifica un fichero de la imagen, lo copia a su capa escribible y lo cambia ahí. La imagen nunca cambia.
- Varios contenedores de la misma imagen comparten sus capas, así que no ocupan N veces el espacio.

**Ciclo de vida**
- Un contenedor vive mientras vive su **proceso principal (PID 1)**. Si el PID 1 termina, el contenedor se para, aunque haya otras shells abiertas con `exec`.
- Un contenedor parado **no desaparece**: conserva su capa escribible y se puede resucitar con `docker start`. Para no acumular contenedores muertos, se usa `--rm`.
- `docker run` **siempre crea un contenedor nuevo** a partir de la imagen. `docker start` reutiliza uno que ya existe.
- **Los contenedores son efímeros**: lo que se escribe en ellos muere con `docker rm`. Los datos que deben persistir, como la base de datos, van en **volúmenes** (Clase 5).
- No se puede borrar una imagen si algún contenedor la usa, aunque esté parado (marca `U` en `docker images`).

**Un contenedor = el kernel del anfitrión + los ficheros de la imagen**
- Dentro del contenedor, `uname -r` muestra el mismo kernel que en WSL, pero `/etc/os-release` decía Ubuntu 26.04 (en WSL es 22.04). Una distro, aparte del kernel, no es más que un conjunto de ficheros.
- El tag `latest` cambia con el tiempo (por ejemplo, `ubuntu:latest` pasa a la LTS nueva cuando sale). En proyectos reales se fija la versión.
- Las imágenes traen lo mínimo por **tamaño**, **seguridad** (menos superficie de ataque) y **previsibilidad**. Las variantes `-slim` y `alpine` son aún más pequeñas, y en Alpine no hay `bash`, solo `sh`.

**Namespaces (lo que el proceso VE)**
- **PID**: dentro, bash era el PID 1. Desde fuera (`docker top`), el mismo proceso era el 670. El aislamiento funciona en una sola dirección: el anfitrión ve todo, el contenedor solo lo suyo.
- **UTS**: el contenedor tiene su propio hostname, que coincide con el ID del contenedor.
- **Red**: el contenedor tiene su propia pila de red. Su puerto 80 no es tu puerto 80; con `-p 8080:80` se publica y Docker reenvía el tráfico, al estilo NAT.
- Por defecto, dentro del contenedor se es **root**, lo cual es un riesgo. En la Clase 4 usaremos un usuario sin privilegios.

**cgroups (lo que el proceso CONSUME)**
- `--memory 100m` crea un cgroup con un límite. Si el contenedor lo supera, **el kernel** (no Docker) activa el **OOM killer** y mata el proceso con SIGKILL. Docker solo configura el límite y anota `OOMKilled=true`.
- El límite cuenta todo lo que hay en el contenedor, incluido el propio runtime: Python ya ocupa varios MB antes de reservar nada. Al poner límites hay que tenerlo en cuenta.

**Códigos de salida**
- `0` = todo fue bien.
- Muerte por señal = **128 + número de señal**:
  - **137** = SIGKILL (9): lo mataron, por OOM o porque un `stop` agotó el tiempo de espera.
  - **143** = SIGTERM (15).
- `docker stop` envía SIGTERM y, si en 10 segundos el proceso no ha terminado, SIGKILL.

**Configuración por variables de entorno**
- `-e VAR=valor` pasa una variable al contenedor, y el código la lee con `os.environ`. Así el valor no está escrito en el código y se puede configurar desde fuera (enfoque *12-factor*).

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker ps` / `docker ps -a` | Contenedores en ejecución / todos |
| `docker images` / `docker rmi <img>` | Listar / borrar imágenes |
| `docker run -it --name X img cmd` | Contenedor interactivo con nombre y comando propio |
| `docker run -d -p 8080:80 img` | En segundo plano y con el puerto publicado |
| `docker run --rm ...` | Borrar el contenedor al terminar |
| `docker run -e VAR=valor ...` | Pasar una variable de entorno |
| `docker run --memory 100m --memory-swap 100m ...` | Limitar la memoria sin swap |
| `docker start [-ai] X` / `docker stop X` | Resucitar / parar un contenedor |
| `docker rm [-f] X` | Borrar un contenedor (`-f` aunque esté corriendo) |
| `docker exec -it X sh` | Abrir otra shell en un contenedor que está corriendo |
| `docker exec X sh -c 'cmd > fichero'` | Ejecutar un comando con redirección **dentro** del contenedor |
| `docker cp origen X:/ruta` | Copiar ficheros entre tu máquina y un contenedor |
| `docker logs [-f] X` | Ver la salida (stdout/stderr) del contenedor, o seguirla en directo |
| `docker top X` | Procesos del contenedor vistos desde el anfitrión |
| `docker inspect -f '{{.State.X}}' X` | Consultar un campo concreto de la configuración |
| `docker stats` | Consumo de CPU y memoria en tiempo real |

### Lecciones de depuración
- Ante un contenedor caído, lo primero es mirar el **STATUS y el código de salida** en `docker ps -a`, y después `docker inspect` (`OOMKilled`, `ExitCode`).
- 137 con `OOMKilled=true` = se pasó de memoria.
- Si una petición no aparece en los logs de nginx, el problema está **antes** del servidor: en el puerto, la red o la URL.
- Leer los mensajes de error con calma antes de forzar nada. Por ejemplo, `rmi` falla porque un contenedor usa la imagen; la solución es borrar el contenedor, no `rmi -f` a ciegas.



## Clase 3 · Esqueleto de la API

### Teoría

**Anatomía de un proyecto Python con uv**
- **`pyproject.toml`**: configuración estándar del proyecto (PEP 621): nombre, versión, `requires-python`, dependencias y configuración de herramientas (`[tool.ruff]`...). Declara rangos aceptables (`fastapi>=0.162`).
- **`uv.lock`**: versiones **exactas** y hashes de todo el árbol de dependencias. **Se sube a Git**: garantiza que el portátil, la CI y Docker instalen exactamente lo mismo.
- **`.venv/`**: el entorno virtual, con un Python y las librerías aisladas para este proyecto. **No se sube a Git**: se regenera a partir de `uv.lock`.
- **`.python-version`**: la versión de Python que usa uv en esta carpeta.
- **Estructura `src/`**: el código va en `src/<paquete>/`. Los tests importan el paquete **instalado**, igual que en producción, y no el fichero que haya en la carpeta actual. Por eso los imports son absolutos (`from porra_api.config import ...`).
- `__init__.py` marca una carpeta como paquete de Python.
- `[build-system]` (uv_build) es lo que permite instalar el paquete en el `.venv`.
- **Dependencias de desarrollo** (`uv add --dev`, grupo `[dependency-groups] dev`): solo para programar y testear. No van a producción.
- `uv run <cmd>` ejecuta un comando dentro del `.venv` sin activarlo.

**FastAPI y uvicorn**
- FastAPI asocia rutas a funciones con decoradores (`@app.get("/ruta")`). Lo que devuelve la función se convierte a JSON.
- Las anotaciones de tipos se usan para validar y para generar la documentación: `/docs` (Swagger UI) se genera desde `/openapi.json` (estándar OpenAPI).
- uvicorn es el servidor: escucha en el puerto y pasa las peticiones a la app mediante **ASGI**. Se arranca con `módulo:objeto` (`porra_api.main:app`).
- `--reload` solo se usa en desarrollo.
- Los errores también se devuelven en JSON (`404 {"detail": "Not Found"}`).
- Un **500** significa que hubo una excepción. El detalle no se envía al cliente, por seguridad: **está en los logs del servidor**.
- Parámetros *keyword-only*: un `*` en la firma obliga a pasar por nombre todo lo que viene después (`FastAPI(title=...)`).

**Configuración (12-factor) con pydantic-settings**
- La configuración va en **variables de entorno**, no en el código. Así la misma imagen sirve para desarrollo y producción, y los secretos quedan fuera de Git.
- `BaseSettings` lee cada campo de su variable de entorno y **lo convierte al tipo declarado**. Si falta un campo obligatorio o el tipo es incorrecto, lanza `ValidationError`.
- `env_prefix="PORRA_"`: el campo `environment` se lee de `PORRA_ENVIRONMENT`.
- ⚠️ **Si el nombre de la variable no coincide con el del campo, se ignora en silencio** y se usa el valor por defecto. Una errata en el nombre del campo no da error.
- `@lru_cache` en `get_settings()`: `Settings()` se crea una sola vez. En las siguientes llamadas **no se ejecuta el cuerpo de la función**, así que si cambias una variable de entorno con el proceso en marcha, no se entera.
- Si `Settings()` se crea en la primera petición, una configuración inválida da un 500 en lugar de impedir el arranque. Lo ideal es **fallar rápido** (*fail fast*) al arrancar.
- `VAR=valor comando` define la variable solo para ese comando.

**Python: trampas vistas**
- Una coma al final convierte un valor en tupla: `x = "0.1.0",` → `("0.1.0",)`.
- Un traceback se lee **de abajo arriba**: la última línea es el error, y encima hay que buscar la última línea de **tu** código.

**pytest**
- Encuentra solo los ficheros `test_*.py` y las funciones `test_*`. Las comprobaciones se hacen con `assert`.
- `TestClient(app)` llama a la app dentro del mismo proceso, sin servidor ni red.
- **Fixtures**: preparación y limpieza alrededor de cada test. Lo que va después del `yield` se ejecuta **siempre**, aunque el test falle (como `try/finally`). En cambio, el código que va detrás de un `assert` que falla no se ejecuta.
- `monkeypatch.setenv` cambia una variable de entorno solo durante el test.
- `autouse=True` aplica la fixture a todos los tests.
- `conftest.py` contiene fixtures compartidas. Tiene que estar en la carpeta de los tests (o por encima).
- Las limpiezas se hacen en **orden inverso** a las preparaciones (pila, LIFO).
- `--setup-show` muestra qué fixtures se ejecutan en cada test.
- Los tests deben cambiar solo lo que quieren probar.
- Hay que mantener la salida sin warnings, para que los avisos nuevos destaquen.

**ruff**
- **Linter** (`ruff check`, `--fix`) + **formateador** (`ruff format`), configurados en `[tool.ruff]`.
- Reglas: E/W (PEP 8), F (errores lógicos), I (orden de imports), UP (sintaxis moderna), B (*bugbear*).
- Orden de los imports: librería estándar → terceros → propios, separados por una línea en blanco.
- Después de cualquier herramienta que modifique código, hay que volver a ejecutar los tests.

### Comandos clave
| Comando | Para qué |
|---|---|
| `uv init --package --name X --python 3.13 ruta` | Crear un proyecto con estructura `src/` |
| `uv add pkg` / `uv add --dev pkg` | Añadir una dependencia de producción / de desarrollo |
| `uv run uvicorn porra_api.main:app --reload` | Arrancar la API en desarrollo (puerto 8000) |
| `PORRA_ENVIRONMENT=x uv run ...` | Lanzar un comando con una variable de entorno |
| `curl -v url` | Petición HTTP con todo el detalle (sin `-s`, que oculta los errores) |
| `uv run pytest -v` | Ejecutar los tests con detalle |
| `uv run pytest --setup-show` | Ver qué fixtures se ejecutan en cada test |
| `uv run ruff check [--fix]` | Revisar el código (y arreglar lo que se pueda automáticamente) |
| `uv run ruff format` | Formatear el código |
| `git status -u` | Listar todos los ficheros sin seguimiento, sin resumir carpetas |

### Lecciones de depuración
- **Un 500**: ir a los logs del servidor y leer el traceback de abajo arriba.
- **Un `curl -s` que no devuelve nada**: quitar `-s` y usar `-v`.
- **Alertas amarillas en los imports de VS Code**: el intérprete no es el del `.venv` (*Python: Select Interpreter*).
- **Una variable de entorno que no tiene efecto**: comprobar el prefijo y el nombre del campo letra a letra. Y tener en cuenta la caché.
- **Una fixture que "no hace nada"**: usar `--setup-show`. Si no aparece, comprobar el nombre y la ubicación de `conftest.py`.
- **Renombrar en VS Code con F2**, para cambiar un nombre en todos los sitios a la vez



## Clase 4a · Mi primer Dockerfile (parte 1)

### Teoría

**Dockerfile y capas**
- El Dockerfile es la receta de una imagen: instrucciones que se ejecutan en orden. **Cada instrucción que modifica ficheros (`COPY`, `RUN`) crea una capa.** `ENV`, `EXPOSE` y `CMD` solo guardan metadatos y no aparecen como pasos del build.
- Instrucciones:
  - **`FROM`**: imagen base (siempre la primera). Hay que fijar la versión (`python:3.13-slim`).
  - **`WORKDIR`**: directorio de trabajo dentro de la imagen (lo crea si no existe).
  - **`COPY`**: copia ficheros del build context a la imagen. Con varios orígenes, el destino termina en `/`.
  - **`RUN`**: ejecuta un comando **durante el build** y guarda el resultado como capa.
  - **`ENV`**: variable de entorno que tendrán todos los contenedores de la imagen. Con `PATH="/app/.venv/bin:$PATH"` se "activa" el `.venv`.
  - **`EXPOSE`**: solo **documenta** el puerto; no publica nada (eso lo hace `-p`).
  - **`CMD`**: el comando que se ejecuta **al arrancar el contenedor** (su PID 1). En formato lista (*exec form*), el proceso es el PID 1 directamente y recibe bien las señales.
- `uv sync --frozen --no-dev`: instala exactamente lo que dice `uv.lock`, sin dependencias de desarrollo.
- `--no-install-project`: instala solo las dependencias, no el paquete propio.
- Si `pyproject.toml` tiene `readme = "README.md"`, ese fichero es necesario para construir el paquete.

**Build context y `.dockerignore`**
- `docker build .`: el `.` es el **build context**, la carpeta que se envía al motor. El motor no lee tu disco: los `COPY` solo pueden coger lo que esté en el contexto.
- `.dockerignore` excluye ficheros del contexto: `.venv` (pesado, y con enlaces a un Python que no existe en la imagen), las cachés, `tests/` y `.env` (los secretos nunca deben acabar en una imagen).
- Un contexto bien filtrado: 58 KB, casi todo `uv.lock`.

**Caché de capas**
- Docker reutiliza una capa si la instrucción y la capa anterior son iguales. En los `COPY`, además, si los ficheros copiados no han cambiado.
- ⚠️ **Cuando un paso se invalida, se invalidan todos los que vienen detrás** (efecto cascada).
- Hay que ordenar **de lo que cambia menos a lo que cambia más**: primero `pyproject.toml` + `uv.lock` y la instalación de dependencias, y después el código. Así, un cambio en el código solo reconstruye las últimas capas.
- `COPY . .` copia también el propio `Dockerfile`: cambiar el `CMD` invalidaba el `COPY` y obligaba a reinstalar todo. Es mejor usar `COPY` explícitos.
- Cada build mueve el tag a la imagen nueva y deja la antigua como `<none>` (*dangling*). Se limpian con `docker image prune`.
- Un contenedor que ya está corriendo **no se actualiza** al reconstruir la imagen: hay que pararlo y lanzar uno nuevo.

**Redes: `--host 0.0.0.0`**
- `127.0.0.1` dentro del contenedor es el loopback **del contenedor**: solo lo pueden usar sus propios procesos.
- El tráfico que llega desde fuera con `-p` entra por la interfaz `eth0` del contenedor (red `bridge`; el cliente aparece como `172.17.0.1`, la puerta de enlace de Docker).
- Si el servidor escucha solo en `127.0.0.1`, desde fuera da *connection reset*. Con **`0.0.0.0`** escucha en todas las interfaces.
- En una conexión TCP, el servidor usa un puerto fijo (8000) y el cliente un **puerto efímero** que asigna el sistema operativo al azar (el `:50350` de los logs).

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker build -t nombre:tag .` | Construir una imagen con nombre y versión |
| `docker run -d --rm --name api -p 8000:8000 porra-api:0.1.0` | Ejecutar la API en un contenedor |
| `docker exec api python -c "..."` | Probar algo desde dentro (la imagen slim no trae curl) |
| `docker images <nombre>` | Ver las imágenes con ese nombre |
| `docker image prune` | Borrar las imágenes `<none>` que no usa nadie |

### Lecciones de depuración
- *Connection reset* con `-p` publicado: mirar en `docker logs` **dónde escucha** el servidor. Si dice `127.0.0.1`, falta `--host 0.0.0.0`.
- Si una prueba **desde dentro** (`docker exec`) funciona y desde fuera no, el problema no está en el código, sino en la red o la publicación del puerto.
- En la salida del build, mirar qué pasos salen como `CACHED` y cuál es el **primero que no**: a partir de ahí se reconstruye todo.



## Clase 4b · Imágenes de producción

### Teoría

**Medir imágenes**
- `docker images`: **DISK USAGE** es lo que ocupa descomprimida en disco; **CONTENT SIZE**, lo que ocupa comprimida, que es lo que se descarga.
- `docker history <img>`: cada capa, con la instrucción que la creó y su tamaño. Arriba están las capas propias y abajo las de la base. `<missing>` no indica ningún error: son capas sin un ID de imagen propio.
- En la versión de una sola etapa, `pip install uv` ocupaba 67 MB: cinco veces más que todas las dependencias (13 MB). Las herramientas de build no deben ir en la imagen final.

**Build multi-stage**
- Varios `FROM` en un Dockerfile; **solo la última etapa es la imagen final**, y las demás se descartan. Es como compilar en C: necesitas `gcc` para compilar, pero solo distribuyes el binario.
- `FROM ... AS builder` le pone nombre a una etapa. `COPY --from=builder` copia ficheros de esa etapa, y `COPY --from=<imagen>` los copia de otra imagen (así se trae el binario de uv de `ghcr.io/astral-sh/uv:0.13.6`).
- La etapa final empieza **limpia**: no hereda nada de las anteriores.
- **Misma imagen base en el builder y en el runtime**: el `.venv` tiene enlaces a `/usr/local/bin/python`, que tiene que existir, en la misma versión, en la imagen final.
- `--no-editable`: el paquete se copia **dentro** del `.venv`. En modo editable (el de por defecto), el `.venv` solo tiene un enlace a `/app/src`, que en la etapa final no existe → `ModuleNotFoundError`.
- `UV_COMPILE_BYTECODE=1`: precompila los `.pyc` en el build, para que la API arranque más rápido (y porque el usuario de la app no puede escribirlos).
- `UV_PYTHON_DOWNLOADS=0`: prohíbe a uv descargar otro Python.
- BuildKit construye en **paralelo** las etapas que no dependen entre sí.
- Resultado: de 302 MB a 204 MB (comprimida, de 85,7 a 49,1 MB). Por encima de la base (181 MB) solo se añaden unos 20 MB.

**Usuario sin privilegios (mínimo privilegio)**
- Por defecto se es root en el contenedor: si alguien explota la app, actúa como root. Muchos clústeres de Kubernetes rechazan directamente los pods que se ejecutan como root.
- `RUN useradd --system --uid 1000 --no-create-home app` + `USER app`. Se usa un **UID fijo**, porque Kubernetes trabaja con números.
- Los puertos por debajo de 1024 requieren privilegios; el 8000 no.
- ⚠️ **El código debe ser de root y de solo lectura.** Con `--chown=app:app`, la app podía modificar su propio `.venv` (comprobado con `touch`), lo que permitiría a un atacante meter una puerta trasera en las librerías. Sin `--chown`, los ficheros pertenecen a root y son legibles por todos: la API funciona y no puede modificarlos.
- El usuario de la app solo debe poder escribir donde lo necesite. Más adelante: `readOnlyRootFilesystem` en Kubernetes (Clase 17).

**Etiquetas (tags)**
- Un tag es un **puntero con nombre** a una imagen (como una rama de Git a un commit). Una imagen puede tener varios: `docker tag porra-api:0.2.0 porra-api:latest` (mismo IMAGE ID).
- **Versión semántica** MAYOR.MENOR.PARCHE + **SHA del commit** (desde la CI).
- **Nunca se despliega `latest`**: cambia sin avisar, no sabes qué versión está corriendo y no puedes volver atrás de forma fiable.

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker history <img>` | Ver las capas de una imagen y lo que ocupa cada una |
| `docker tag <img:tag> <img:otro>` | Añadir otro tag a la misma imagen |
| `docker exec api id` | Comprobar con qué usuario se ejecuta el contenedor |
| `docker exec api ls -ld <ruta>` | Ver los permisos y el propietario de una carpeta |
| `docker rmi <img:tag>` | Borrar una imagen |

### Lecciones de depuración
- Si `docker images` no muestra la imagen nueva, revisar la salida del build y **en qué carpeta se ejecutó** (el build context).
- Comprobar la seguridad **probándola**: intentar escribir donde no se debería poder (`touch`) y verificar que falla.



## Clase 5a · Postgres, volúmenes y redes (parte 1)

### Teoría

**Volúmenes**
- La capa escribible muere con el contenedor. Los datos que deben persistir van **fuera**:
  - **Volumen con nombre** (`-v nombre:/ruta`): lo gestiona Docker. Es lo adecuado para los **datos** de servicios.
  - **Bind mount** (`-v /ruta/host:/ruta`): una carpeta tuya. Se usa en **desarrollo** (*hot reload*).
- **Un volumen tiene un ciclo de vida independiente del contenedor**: se borra el contenedor, el volumen sigue, y se puede montar en otro contenedor nuevo.
- El `Mountpoint` está dentro de la máquina virtual de Docker Desktop, no en tu Ubuntu. Los volúmenes se gestionan con `docker volume`.
- ⚠️ **Postgres 18+**: el volumen se monta en **`/var/lib/postgresql`** (los datos van en `18/docker`). Si se monta en la ruta antigua, `/var/lib/postgresql/data`, Postgres arranca una base de datos vacía sin avisar.

**La imagen oficial de Postgres**
- `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` **solo se usan en la inicialización** (con el volumen vacío): `initdb` + un servidor temporal (que solo escucha en un socket Unix, no en la red) + `CREATE DATABASE` + scripts de `/docker-entrypoint-initdb.d/` → se apaga → arranca el servidor definitivo como PID 1, escuchando en `0.0.0.0:5432`.
- Con el volumen ya inicializado: `Skipping initialization`.
- ⚠️ **Cambiar `POSTGRES_PASSWORD` con un volumen existente no cambia la contraseña.** Los usuarios viven en la base de datos, y la base de datos vive en el volumen. Para cambiarla: `ALTER USER`, o borrar el volumen (perdiendo los datos).
- Las conexiones locales (`docker exec ... psql`) usan autenticación *trust* y no piden contraseña. Las conexiones por red, sí.
- **WAL** (*Write-Ahead Log*): después de un `rm -f` (SIGKILL), Postgres se recupera reaplicando el WAL (*redo*). Aun así, con las bases de datos se usa **`docker stop`** (SIGTERM, cierre ordenado).

**Redes**
- **`localhost` dentro de un contenedor es el propio contenedor.**
- La red `bridge` por defecto (172.17.x): los contenedores tienen IP, pero **no hay DNS por nombre**.
- Las **redes creadas por el usuario** (`docker network create`) tienen DNS: cada contenedor es accesible por su **nombre**. Cada red tiene su propio rango de IPs (172.18.x...).
- `docker network connect red contenedor` conecta un contenedor que ya está corriendo; `--network red` lo conecta al crearlo.

**Diagnóstico por capas**
| Error | Capa | Qué comprobar |
|---|---|---|
| `could not translate host name` | DNS | ¿Están los dos contenedores en la misma red de usuario? ¿El nombre es correcto? |
| `Connection refused` | TCP | ¿Es el host correcto? (`localhost` = el propio contenedor) ¿El servicio escucha en ese puerto y en `0.0.0.0`? |
| `password authentication failed` | Aplicación | La red funciona; revisar las credenciales (¿se cambiaron solo en las variables, con el volumen ya existente?) |

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker run -d --name db -e POSTGRES_... -v vol:/var/lib/postgresql postgres:18` | Postgres con un volumen con nombre |
| `docker exec -it db psql -U usuario -d bd` | Abrir psql dentro del contenedor |
| `psql ... -c "SQL"` | Ejecutar una consulta y salir |
| `docker volume ls` / `inspect` / `rm` | Gestionar volúmenes |
| `docker network create` / `connect` / `rm` | Gestionar redes |
| `docker run --rm --network red -e PGPASSWORD=... postgres:18 psql -h db ...` | Conectarse a Postgres desde otro contenedor, por red |



## Clase 5b · SQLAlchemy 2, Alembic y modelo de dominio

### Teoría

**Diseño del modelo**
- **N:M** (jugadores ↔ partidos, porras ↔ jugadores) → **tabla intermedia** (`pronosticos`, `miembros`). La tabla intermedia puede tener sus propios datos (los goles y los puntos de un pronóstico).
- **Datos derivados** (puntos totales, clasificación) **no se guardan**: se calculan. Cada dato tiene una única fuente de verdad. Los `puntos` de cada pronóstico sí se guardan (`NULL` = sin puntuar ≠ 0).
- **Clave primaria propia** + **ID externo `UNIQUE`** (`football_data_id`): no se depende del proveedor, y el `UNIQUE` permite el **upsert idempotente** del ingestor.
- Las columnas que aún no tienen valor (los goles de un partido sin jugar, los equipos de una eliminatoria antes del sorteo) son **nulas**.
- **Las restricciones de integridad van en la base de datos** (`UNIQUE`, `FK`): evitan las **condiciones de carrera** que una comprobación en Python no evita. Las **reglas de negocio** (horario de los pronósticos, La Máquina solo en ligas) van en la API: son más fáciles de leer, testear y cambiar.
- "¿Ha empezado el partido?" se comprueba en el momento de escribir (ahora frente a `inicio`). No hace falta ningún trigger ni aviso programado.
- `ON DELETE CASCADE` (un jugador se lleva sus pronósticos y sus membresías; RGPD) frente a `RESTRICT` (no se borra un partido con pronósticos ni una competición con porras).
- **Clave primaria compuesta** en `miembros` (`porra_id`, `jugador_id`): ya garantiza la unicidad.
- `UNIQUE ... NULLS NOT DISTINCT` (Postgres 15+): por defecto, dos `NULL` se consideran distintos en un `UNIQUE`.
- **YAGNI**, pero distinguiendo: lo que es barato ahora y caro de cambiar después (la competición, en la identidad de cada jornada) se hace ya; lo que es caro ahora y barato después (eliminatorias, "¿quién pasa?") se deja para más adelante.

**SQLAlchemy 2**
- **ORM**: clases ↔ tablas, atributos ↔ columnas. Se escribe Python y el ORM genera el SQL.
- `Mapped[T]` → `NOT NULL`; `Mapped[T | None]` → admite `NULL`. `mapped_column(...)` para claves primarias, foráneas, `unique`, `String(n)`, `DateTime(timezone=True)`, `server_default`...
- `server_default` lo aplica **Postgres** (también a las filas insertadas fuera de la API); `default` lo aplica Python.
- Restricciones de varias columnas: `__table_args__ = (UniqueConstraint(...),)`. Es una tupla: la coma final es necesaria.
- `DeclarativeBase` + `MetaData(naming_convention=...)`: nombres de restricciones predecibles (`fk_tabla_columna_referida`...), que Alembic necesita para modificarlas en el futuro.
- **Driver**: `psycopg` habla el protocolo de Postgres. `[binary]` incluye libpq compilada (no hace falta tenerla en el sistema).
- URL: `postgresql+psycopg://usuario:contraseña@host:puerto/bd` (dialecto+driver).

**Alembic (migraciones)**
- **Control de versiones del esquema**: cada cambio es un fichero con `upgrade()` y `downgrade()`. La tabla `alembic_version` guarda la última migración aplicada en cada base de datos.
- `alembic init migrations`: crea `alembic.ini`, `env.py`, `script.py.mako` y `versions/`.
- En `env.py`: la URL se toma de `Settings` (no hay credenciales en `alembic.ini`), y `target_metadata = Base.metadata`.
- `revision --autogenerate`: compara los modelos con la base de datos. **Siempre se revisa** antes de aplicarla.
- El orden de creación y borrado sigue las claves foráneas (**orden topológico**): primero lo referenciado, y se borra en orden inverso.
- `upgrade head`, `downgrade base`, `current`. **Hay que probar que el `downgrade` funciona.**
- Desplegar código nuevo **no cambia el esquema**: hay que aplicar las migraciones.

### Comandos clave
| Comando | Para qué |
|---|---|
| `uv add sqlalchemy "psycopg[binary]" alembic` | ORM + driver + migraciones |
| `export VAR=valor` | Definir una variable para toda la sesión de la terminal |
| `uv run alembic init migrations` | Inicializar Alembic |
| `uv run alembic revision --autogenerate -m "..."` | Generar una migración comparando con los modelos |
| `uv run alembic upgrade head` / `downgrade base` / `current` | Aplicar / deshacer todas / ver la versión actual |
| `psql -c "\dt"` / `"\d tabla"` | Listar tablas / ver la estructura de una tabla |
| `uv run ruff check --fix --unsafe-fixes` | Aplicar también arreglos que podrían cambiar el comportamiento (revisar después) |

### Lecciones de depuración
- `E402` (import fuera del principio del fichero): ruff no lo arregla solo; hay que mover los imports a mano.
- Un campo obligatorio nuevo en `Settings` rompe los tests que crean la configuración: se define en una fixture `autouse` de `conftest.py`.



## Clase 6a · Docker Compose (parte 1)

### Teoría

**Compose**
- **Declarativo**: se describe el estado deseado en YAML (`compose.yaml`) y Compose crea, recrea o deja como está lo necesario. Es la antesala de Kubernetes. Lo contrario es imperativo: dar órdenes paso a paso con `docker run`.
- Crea automáticamente una red propia con **DNS**: cada **servicio** es accesible por su nombre (`db:5432`).
- Prefijo del **nombre del proyecto** (la carpeta): `la-porra_pgdata`, `la-porra_default`.
- Campos: `image`, `build` (carpeta con el Dockerfile; con `build`, `image` es el nombre que recibe la imagen construida), `environment`, `volumes`, `ports` (entre comillas), `healthcheck`, `depends_on`, y `volumes:` en el nivel superior para declarar los volúmenes con nombre.

**Secretos e interpolación**
- Compose lee el `.env` de la carpeta del proyecto y sustituye cada `${VAR}` en `compose.yaml`. Los secretos no se escriben en ficheros que van a Git.
- **`.env`**: valores reales, **fuera de Git**. **`.env.example`**: la estructura, sin secretos, **en Git** (`cp .env.example .env`).
- Una sola fuente de verdad: la URL de la API se construye por interpolación con las mismas credenciales que usa Postgres.

**Arranque ordenado**
- **Running ≠ healthy.** Postgres está *running* desde el primer segundo, pero solo está listo al final de la inicialización.
- `healthcheck`: `test` (`pg_isready`), `interval`, `timeout`, `retries`, `start_period` (periodo de gracia). Estado: `health: starting` → `healthy` / `unhealthy`.
- `depends_on` a secas: espera a que el contenedor **arranque**. Con `condition: service_healthy`: espera a que esté **sano**.

**Dos caminos hacia Postgres**
- Desde **otro contenedor** de la red de Compose: `db:5432`, gracias al DNS de Docker. Ahí, `localhost` es el propio contenedor.
- Desde **WSL** (fuera de la red): `localhost:5432`, gracias al puerto publicado con `ports`.

**Migraciones como paso aparte, no en el `CMD`**
- Con varias réplicas, todas migrarían a la vez (condiciones de carrera y bloqueos).
- Si una migración falla, la API entra en un bucle de reinicios. Siendo un paso aparte, se detiene el despliegue y la versión anterior sigue funcionando.
- El PID 1 de la API sirve peticiones; migrar es una tarea **puntual de despliegue** (en Kubernetes: un Job o un initContainer, Clase 15).
- **Mínimo privilegio**: la API puede usar un usuario de base de datos sin permisos de DDL (`CREATE`/`ALTER`/`DROP`).

**Ciclo de vida**
- `down` borra los contenedores y la red, y **conserva los volúmenes**. **`down -v` borra también los volúmenes, y con ellos los datos.**

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker compose up -d [servicio]` | Levantar todo (o un servicio) en segundo plano |
| `docker compose up -d --build` | Reconstruir las imágenes antes de levantar |
| `docker compose ps [-a]` | Ver los contenedores del proyecto y su estado de salud |
| `docker compose logs [-f] servicio` | Ver los logs de un servicio |
| `docker compose exec servicio cmd` | Ejecutar un comando en un contenedor que está corriendo |
| `docker compose run --rm servicio cmd` | Contenedor nuevo y puntual, con la configuración del servicio (migraciones) |
| `docker compose down` | Parar y borrar los contenedores y la red (los volúmenes se conservan) |
| `docker compose down -v` | ⚠️ Lo mismo, y además borra los volúmenes |



## Clase 6b · Desarrollo frente a producción

### Teoría

**Hot reload con bind mounts**
- Un bind mount de `src/` deja ver en el contenedor los cambios de tu carpeta al instante. Con el repo en el sistema de ficheros de Linux (no en `/mnt/c`), los cambios llegan rápido y uvicorn los detecta.
- ⚠️ Con `--no-editable` (imagen de producción), el paquete está **copiado** en el `.venv`: uvicorn se recarga, pero Python importa la copia antigua. Se diagnostica con `python -c "import paquete; print(paquete.__file__)"`.
- Para desarrollo hace falta el modo **editable**: el `.venv` apunta a `/app/src`.

**Etapa `dev` en el Dockerfile**
- `FROM builder AS dev` + `uv sync --frozen` (con el grupo `dev` y en modo editable).
- Va **antes** de la etapa final: si no se indica `target`, Docker construye **la última etapa**, así que `docker build` a secas sigue produciendo la imagen de producción.
- Se ejecuta como root: aceptable porque **solo se usa en local**. Lo que se despliega es la etapa final, sin privilegios.

**Desarrollo frente a producción en Compose**
- **`compose.override.yaml`** se combina **automáticamente** con `compose.yaml` en `up`, `run`, `config`...
- La base (`compose.yaml`) se parece a producción: imagen final y **Postgres sin publicar**. El override añade lo de desarrollo: `target: dev`, bind mounts, `--reload` y el puerto de Postgres.
- `docker compose -f compose.yaml ...` usa solo la base e ignora el override.
- `docker compose config` muestra la configuración final, combinada e interpolada. ⚠️ Incluye los secretos ya sustituidos.
- Las imágenes de desarrollo y de producción llevan tags distintos (`:dev` y `:local`), para que no se pisen.

**Tests en Compose**
- `docker compose run --rm api pytest`: el mismo entorno que la API, con el código y los tests montados.
- `run` arranca las dependencias (`depends_on`); `--no-deps` se las salta si no hacen falta.
- **Los tests no deben depender del entorno en el que se ejecutan**: con `monkeypatch.delenv(..., raising=False)` se aíslan de las variables que defina Compose.

### Comandos clave
| Comando | Para qué |
|---|---|
| `docker compose config` | Ver la configuración final (base + override, interpolada) |
| `docker compose -f compose.yaml up -d` | Levantar solo con la base (parecido a producción) |
| `docker compose run --rm --no-deps api pytest -v` | Tests dentro de Compose, sin arrancar las dependencias |
| `docker compose run --rm api ruff check` | Linter dentro de Compose |
| `docker compose exec api python -c "import x; print(x.__file__)"` | Ver de dónde se importa un paquete |

### Lecciones de depuración
- Si uvicorn se recarga (los logs lo muestran) pero la respuesta no cambia, **comprobar de dónde se importa el código** (`__file__`).
- Si un `curl -s` sale vacío justo después de guardar, probablemente pilló el servidor reiniciándose: repetirlo sin `-s`, o mirar los logs.
- Si un test pasa "por casualidad" gracias a una variable de entorno, hay que aislarlo.