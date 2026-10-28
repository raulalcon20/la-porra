# Diario del curso

## Estado actual
- **Clase completada:** 3 · Esqueleto de la API
- **Entorno:** Windows 11 + WSL2 Ubuntu 22.04, Docker Desktop 4.97, uv 0.13.6, Python 3.13
- **Rutina al empezar:** abrir Docker Desktop (desde la Clase 4) → `cd ~/la-porra` → `eval "$(ssh-agent -s)" && ssh-add` → `git pull` → `code .`
- **Repo:** `raulalcon20/la-porra` (privado), en `~/la-porra`
- **Hecho:**
  - `services/api`, creado con uv (paquete `porra_api`, estructura `src/`)
  - FastAPI con `/health` y `/version`
  - Configuración con pydantic-settings (prefijo `PORRA_`, `get_settings()` con `lru_cache`)
  - 3 tests con pytest, con `conftest.py` que vacía la caché de settings
  - ruff configurado (E, W, F, I, UP, B)
- **Decisiones:**
  - Las variables de entorno llevan el prefijo `PORRA_`.
  - Las dependencias de desarrollo van en el grupo `dev` (pytest, ruff, httpx2); no irán en la imagen de producción.
  - Se usa httpx2 para el TestClient (Starlette marca httpx como obsoleto).
  - En VS Code, el intérprete es el `.venv` de cada servicio.
- **Pendiente:** validar la configuración al arrancar la API (*fail fast*), en vez de en la primera petición.
- **Ritmo:** el de las Clases 1 a 3 es el adecuado (pasos cortos, predicciones y explicación de cada línea).
- **Siguiente paso:** Clase 4 · Mi primer Dockerfile

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