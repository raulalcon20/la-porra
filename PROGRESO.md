# Diario del curso

## Estado actual
- **Clase completada:** 4 · Mi primer Dockerfile (4a y 4b)
- **Entorno:** Windows 11 + WSL2 Ubuntu 22.04, Docker Desktop 4.97, uv 0.13.6, Python 3.13
- **Rutina al empezar:** abrir Docker Desktop → `cd ~/la-porra` → `eval "$(ssh-agent -s)" && ssh-add` → `git pull` → `code .`
- **Rutina al cerrar:** `git add` y `git status` **desde la raíz del repo**.
- **Repo:** `raulalcon20/la-porra` (privado), en `~/la-porra`
- **Hecho:**
  - API FastAPI (`/health`, `/version`) con pydantic-settings, tests (pytest) y ruff
  - `services/api/Dockerfile` **multi-stage**:
    - builder con uv 0.13.6 copiado de `ghcr.io/astral-sh/uv`
    - runtime `python:3.13-slim` con solo el `.venv` (`--no-editable`, bytecode precompilado)
    - usuario `app` (UID 1000), con el código propiedad de root y de solo lectura
  - Imagen `porra-api:0.2.0` (204 MB; con una sola etapa ocupaba 302 MB)
- **Decisiones:**
  - Prefijo `PORRA_` para las variables de entorno.
  - Dependencias de desarrollo en el grupo `dev`.
  - httpx2 para el TestClient.
  - uvicorn en `0.0.0.0:8000`.
  - `COPY` explícitos.
  - Misma imagen base en el builder y en el runtime.
  - Sin `--chown`: la app no puede modificar su propio código.
  - Tags: versión semántica + SHA del commit (desde la CI); nunca se despliega `latest`.
- **Pendiente:** validar la configuración al arrancar (*fail fast*).
- **Ritmo:** el de las clases anteriores es el adecuado.
- **Siguiente paso:** Clase 5 · Postgres, volúmenes y redes

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