# Diario del curso

## Estado actual
- **Clase completada:** 2 · Qué es de verdad un contenedor (Módulo 0 terminado)
- **Entorno:** igual que en la Clase 1 (Windows 11 + WSL2 Ubuntu 22.04, Docker Desktop 4.97, uv 0.13.6, Python 3.13)
- **Repo:** `raulalcon20/la-porra` (privado), en `~/la-porra`. Solo hay README y PROGRESO.md; todavía no hay código.
- **Decisiones nuevas:** en los Dockerfiles se fijarán siempre las versiones de las imágenes (nada de `latest`).
- **Pendiente:** responder 2 preguntas rápidas de repaso de la Clase 2 al empezar la siguiente sesión.
- **Siguiente paso:** Clase 3 · Esqueleto de la API (FastAPI + uv + pytest)

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