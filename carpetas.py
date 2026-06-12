"""
╔══════════════════════════════════════════════════════════════════════════╗
║         NEXTVISION — ARQUITECTO DE HERENCIA v2.0                       ║
║         Organizador inteligente de archivos para EOBARD ecosystem       ║
╚══════════════════════════════════════════════════════════════════════════╝

CÓMO USAR:
  1. Modo simulación (recomendado primero):
     python carpetas.py --simulate

  2. Modo real:
     python carpetas.py

  3. Ver log de la última ejecución:
     cat nextvision_organizer.log
"""

import os
import shutil
import hashlib
import logging
import argparse
import sys
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIGURACIÓN CENTRAL — edita solo esta sección
# ═══════════════════════════════════════════════════════════

CARPETA_RAIZ = Path(r"C:\Users\gabow\NextVision")

# Carpetas que el script NUNCA tocará (ni sus contenidos internos)
CARPETAS_BLINDADAS = {
    # Carpetas de organización ya creadas
    "Repositorios_GitHub", "SYSTEM", "Modelos_IA", "scripts",
    "audio", "video", "Bases_de_Datos", "Modelos_3D", "Imagenes",
    "documentos", "Otros",
    # Entornos de desarrollo — tocarlos rompe dependencias
    ".vscode", "node_modules", ".git", "__pycache__",
    ".google_profile", ".wwebjs_auth",
    # Módulos activos con rutas relativas internas
    "automation-cinnamon",
}

# Marcadores que indican que una carpeta es un ecosistema completo (repo, proyecto)
# Si una carpeta contiene alguno de estos archivos → se mueve entera a Repositorios_GitHub
MARCADORES_DE_PROYECTO = {"package.json", "Cargo.toml", "pyproject.toml", ".git", ".gitignore"}

# Archivos en la RAÍZ que jamás se moverán (por nombre exacto, case-insensitive)
ARCHIVOS_INTOCABLES_RAIZ = {
    "readme.md", ".gitignore", "requirements.txt",
    "carpetas.py", "dockerfile", "docker-compose.yml",
    "nextvision_organizer.log",
}

# Archivos sin extensión que deben ir a SYSTEM (case-insensitive)
ARCHIVOS_SISTEMA_SIN_EXTENSION = {"modelfile", "dockerfile", "geminifile"}

# Palabras clave en el nombre de archivos .md → van a SYSTEM (no a documentos)
PALABRAS_CLAVE_SISTEMA = {
    "ARCHITECTURE", "CORE", "DIRECTIVES", "MEMORY",
    "CONFIG", "DOCKERFILE", "INTELLIGENCE", "OFFENSIVE",
    "TRANSFER", "T-OS", "TRAINED",
}

# Umbral en MB para clasificar algo como modelo de IA pesado → Modelos_IA
UMBRAL_MODELO_PESADO_MB = 500

# Umbral en MB para NO calcular hash MD5 (demasiado costoso en tiempo)
UMBRAL_HASH_MB = 100

# ═══════════════════════════════════════════════════════════
# DICCIONARIO DE REGLAS POR EXTENSIÓN
# Orden de prioridad: las heurísticas de arriba siempre ganan
# ═══════════════════════════════════════════════════════════

REGLAS_POR_EXTENSION = {
    # Documentación e informes
    ".pdf": "documentos",
    ".docx": "documentos",
    ".doc": "documentos",
    ".txt": "documentos",
    ".pptx": "documentos",
    ".md": "documentos",       # override si contiene palabra clave → SYSTEM
    ".org": "documentos",

    # Scripts y código fuente
    ".py": "scripts",
    ".js": "scripts",
    ".ts": "scripts",
    ".bat": "scripts",
    ".sh": "scripts",
    ".cpp": "scripts",
    ".c": "scripts",
    ".h": "scripts",
    ".java": "scripts",
    ".cs": "scripts",
    ".html": "scripts",
    ".css": "scripts",
    ".rb": "scripts",
    ".php": "scripts",
    ".go": "scripts",
    ".rs": "scripts",
    ".swift": "scripts",
    ".lua": "scripts",
    ".r": "scripts",
    ".pl": "scripts",
    ".kt": "scripts",
    ".scala": "scripts",
    ".dart": "scripts",

    # Audio y bioseñales
    ".mp3": "audio",
    ".wav": "audio",           # override si contiene 'stark' → audio/STARK_VOICE_CLONES
    ".flac": "audio",
    ".ogg": "audio",
    ".aac": "audio",
    ".m4a": "audio",

    # Video
    ".mp4": "video",
    ".avi": "video",
    ".mkv": "video",
    ".mov": "video",
    ".flv": "video",
    ".webm": "video",

    # Bases de datos y datasets
    ".xlsx": "Bases_de_Datos",
    ".csv": "Bases_de_Datos",
    ".jsonl": "Bases_de_Datos",
    ".json": "Bases_de_Datos",
    ".xml": "Bases_de_Datos",
    ".sql": "Bases_de_Datos",
    ".db": "Bases_de_Datos",
    ".sqlite": "Bases_de_Datos",
    ".parquet": "Bases_de_Datos",

    # Modelos 3D
    ".ply": "Modelos_3D",
    ".obj": "Modelos_3D",
    ".stl": "Modelos_3D",
    ".fbx": "Modelos_3D",
    ".glb": "Modelos_3D",
    ".gltf": "Modelos_3D",
    ".3ds": "Modelos_3D",
    ".blend": "Modelos_3D",
    ".dae": "Modelos_3D",
    ".usdz": "Modelos_3D",

    # Modelos de IA — siempre a Modelos_IA sin importar tamaño
    ".safetensors": "Modelos_IA",
    ".gguf": "Modelos_IA",
    ".ggml": "Modelos_IA",
    ".bin": "Modelos_IA",       # en contexto EOBARD casi siempre son pesos
    ".pt": "Modelos_IA",
    ".pth": "Modelos_IA",
    ".onnx": "Modelos_IA",
    ".pkl": "Modelos_IA",

    # Sistema e infraestructura
    ".pem": "SYSTEM",
    ".key": "SYSTEM",
    ".crt": "SYSTEM",
    ".env": "SYSTEM",

    # Imágenes
    ".jpg": "Imagenes",
    ".jpeg": "Imagenes",
    ".png": "Imagenes",
    ".gif": "Imagenes",
    ".bmp": "Imagenes",
    ".webp": "Imagenes",
    ".svg": "Imagenes",
    ".ico": "Imagenes",
    ".tiff": "Imagenes",
}

# ═══════════════════════════════════════════════════════════
# SETUP DE LOGGING
# ═══════════════════════════════════════════════════════════

def configurar_logging(simular: bool) -> logging.Logger:
    log_path = CARPETA_RAIZ / "nextvision_organizer.log"
    modo = "SIMULACIÓN" if simular else "PRODUCCIÓN"

    logger = logging.getLogger("nextvision")
    logger.setLevel(logging.DEBUG)

    # Handler para archivo (siempre)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Handler para consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(f"{'═'*60}")
    logger.info(f"  NEXTVISION ARQUITECTO DE HERENCIA v2.0 — Modo: {modo}")
    logger.info(f"  Raíz: {CARPETA_RAIZ}")
    logger.info(f"  Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'═'*60}")

    return logger

# ═══════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════

def calcular_hash_md5(ruta: Path) -> str | None:
    """
    Calcula MD5 del archivo para detectar duplicados exactos.
    Devuelve None si el archivo es muy grande o hay error.
    'heavy_file_skip' si supera el umbral (para tratarlo diferente).
    """
    try:
        tamano_mb = ruta.stat().st_size / (1024 * 1024)
        if tamano_mb > UMBRAL_HASH_MB:
            return "heavy_file_skip"
        h = hashlib.md5()
        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def obtener_destino_sin_colision(carpeta_destino: Path, nombre_base: str, extension: str) -> Path:
    """
    Devuelve una ruta libre de colisiones.
    Si ya existe 'config.json', devuelve 'config_v1.json', 'config_v2.json', etc.
    """
    candidato = carpeta_destino / f"{nombre_base}{extension}"
    if not candidato.exists():
        return candidato

    contador = 1
    while True:
        candidato = carpeta_destino / f"{nombre_base}_v{contador}{extension}"
        if not candidato.exists():
            return candidato
        contador += 1


def es_duplicado_exacto(origen: Path, destino: Path) -> bool:
    """
    Compara dos archivos usando MD5. Si alguno es 'heavy_file_skip',
    compara por tamaño como fallback conservador.
    """
    h_origen = calcular_hash_md5(origen)
    h_destino = calcular_hash_md5(destino)

    if h_origen is None or h_destino is None:
        return False

    if h_origen == "heavy_file_skip" or h_destino == "heavy_file_skip":
        # Para archivos pesados: si el tamaño es idéntico, asumimos duplicado
        return origen.stat().st_size == destino.stat().st_size

    return h_origen == h_destino


def enriquecer_nombre_con_procedencia(raiz_actual: Path, nombre_base: str) -> str:
    """
    Si el archivo viene de una subcarpeta significativa, le añade el nombre
    de esa carpeta como prefijo para preservar el contexto de origen.
    Ejemplo: config.json de la carpeta eobard_adapter → eobard_adapter_config.json
    """
    if raiz_actual == CARPETA_RAIZ:
        return nombre_base  # Está en la raíz, no necesita prefijo

    carpeta_padre = raiz_actual.name

    # Evita redundancia tipo "stark_stark_0"
    if carpeta_padre.lower() in nombre_base.lower():
        return nombre_base

    return f"{carpeta_padre}_{nombre_base}"


def esta_en_zona_blindada(ruta_relativa: Path) -> bool:
    """
    Verifica si alguna parte de la ruta relativa es una carpeta blindada.
    Cubre tanto el directorio mismo como sus subdirectorios.
    """
    for parte in ruta_relativa.parts:
        if parte in CARPETAS_BLINDADAS:
            return True
    return False

# ═══════════════════════════════════════════════════════════
# LÓGICA DE CLASIFICACIÓN
# ═══════════════════════════════════════════════════════════

def clasificar_archivo(ruta_archivo: Path, raiz_actual: Path) -> tuple[str, str]:
    """
    Determina a qué carpeta va el archivo y por qué razón.
    Retorna (carpeta_destino, razón).

    Prioridades (de mayor a menor):
      1. ¿Supera el umbral de peso? → Modelos_IA
      2. ¿Es audio Stark? → audio/STARK_VOICE_CLONES
      3. ¿Es extensión directa de modelo IA? → Modelos_IA
      4. ¿Es archivo de sistema sin extensión? → SYSTEM
      5. ¿Es .md con palabra clave de arquitectura? → SYSTEM
      6. Regla estándar por extensión → lo que diga REGLAS_POR_EXTENSION
      7. Sin regla → Otros
    """
    nombre_base = ruta_archivo.stem          # sin extensión
    extension = ruta_archivo.suffix.lower()  # .py, .json, etc.
    nombre_bajo = nombre_base.lower()

    # 1. Modelos pesados (cualquier extensión)
    try:
        tamano_mb = ruta_archivo.stat().st_size / (1024 * 1024)
    except OSError:
        tamano_mb = 0

    if tamano_mb > UMBRAL_MODELO_PESADO_MB:
        return "Modelos_IA", f"Archivo pesado ({tamano_mb:.1f} MB)"

    # 2. Audio de clones de voz Stark
    if extension == ".wav" and "stark" in nombre_bajo:
        return os.path.join("audio", "STARK_VOICE_CLONES"), "Voz Stark detectada"

    # 3. Extensiones directas de modelos de IA (antes del check genérico)
    if extension in {".safetensors", ".gguf", ".ggml", ".pt", ".pth", ".onnx", ".pkl"}:
        return "Modelos_IA", f"Modelo IA (extensión {extension})"

    # 4. Sin extensión → revisar si es archivo de sistema conocido
    if not extension:
        if nombre_bajo in ARCHIVOS_SISTEMA_SIN_EXTENSION:
            return "SYSTEM", "Archivo de sistema sin extensión"
        return "", "Sin extensión y sin regla — ignorado"

    # 5. Archivos .md con palabras clave de arquitectura → SYSTEM
    if extension == ".md":
        nombre_upper = nombre_base.upper()
        if any(clave in nombre_upper for clave in PALABRAS_CLAVE_SISTEMA):
            return "SYSTEM", "Documento de arquitectura EOBARD"

    # 6. Regla estándar por extensión
    if extension in REGLAS_POR_EXTENSION:
        return REGLAS_POR_EXTENSION[extension], f"Extensión {extension}"

    # 7. Sin regla conocida
    return "Otros", f"Extensión desconocida {extension}"

# ═══════════════════════════════════════════════════════════
# MOTOR PRINCIPAL
# ═══════════════════════════════════════════════════════════

def procesar_carpeta(simular: bool, logger: logging.Logger) -> dict:
    stats = {
        "archivos_movidos": 0,
        "archivos_ignorados": 0,
        "archivos_duplicados": 0,
        "archivos_protegidos": 0,
        "carpetas_eliminadas": 0,
        "proyectos_aislados": 0,
        "errores": [],
    }

    # Pre-crear la bóveda de repositorios si es necesario
    boveda_repos = CARPETA_RAIZ / "Repositorios_GitHub"
    if not simular:
        boveda_repos.mkdir(exist_ok=True)

    # topdown=False: procesa de las hojas hacia la raíz
    # Esto permite borrar carpetas vacías al subir
    for raiz_str, directorios, archivos in os.walk(CARPETA_RAIZ, topdown=False):
        raiz_actual = Path(raiz_str)
        ruta_relativa = raiz_actual.relative_to(CARPETA_RAIZ)

        # ── Saltar zonas blindadas ────────────────────────────────────
        if raiz_actual != CARPETA_RAIZ and esta_en_zona_blindada(ruta_relativa):
            logger.debug(f"🛡  ZONA BLINDADA — omitiendo: {ruta_relativa}")
            continue

        # ── Detección de ecosistemas completos (no en la raíz) ───────
        if raiz_actual != CARPETA_RAIZ:
            archivos_set = set(archivos)
            es_ecosistema = any(m in archivos_set for m in MARCADORES_DE_PROYECTO)

            if es_ecosistema:
                destino_repo = boveda_repos / raiz_actual.name
                if destino_repo.exists():
                    destino_repo = obtener_destino_sin_colision(boveda_repos, raiz_actual.name, "")

                logger.info(f"📦 ECOSISTEMA — {'simularía mover' if simular else 'moviendo'}: "
                            f"'{ruta_relativa}' → Repositorios_GitHub/")
                stats["proyectos_aislados"] += 1

                if not simular:
                    try:
                        shutil.move(str(raiz_actual), str(destino_repo))
                    except Exception as e:
                        msg = f"Error al mover ecosistema '{raiz_actual.name}': {e}"
                        logger.error(f"⚠️  {msg}")
                        stats["errores"].append(msg)
                continue

        # ── Procesar archivos en esta carpeta ────────────────────────
        for nombre_archivo in archivos:
            ruta_archivo = raiz_actual / nombre_archivo
            nombre_bajo = Path(nombre_archivo).stem.lower()

            # Proteger intocables de la raíz
            if raiz_actual == CARPETA_RAIZ and nombre_archivo.lower() in ARCHIVOS_INTOCABLES_RAIZ:
                logger.debug(f"🔒 INTOCABLE — protegido en raíz: {nombre_archivo}")
                stats["archivos_protegidos"] += 1
                continue

            # Clasificar el archivo
            carpeta_destino_rel, razon = clasificar_archivo(ruta_archivo, raiz_actual)

            # Si la clasificación devuelve vacío → ignorar
            if not carpeta_destino_rel:
                logger.debug(f"⏭  IGNORADO — {nombre_archivo}: {razon}")
                stats["archivos_ignorados"] += 1
                continue

            carpeta_destino_abs = CARPETA_RAIZ / carpeta_destino_rel

            # Verificar si ya está donde debe estar
            if raiz_actual == carpeta_destino_abs:
                logger.debug(f"✅ YA ORGANIZADO — {nombre_archivo} ya está en '{carpeta_destino_rel}'")
                stats["archivos_ignorados"] += 1
                continue

            # También verificar por ruta relativa (cubre subcarpetas como audio/STARK_VOICE_CLONES)
            if str(ruta_relativa).startswith(str(Path(carpeta_destino_rel))):
                logger.debug(f"✅ YA ORGANIZADO — {nombre_archivo} en subdirectorio de '{carpeta_destino_rel}'")
                stats["archivos_ignorados"] += 1
                continue

            # Enriquecer nombre con procedencia
            nombre_enriquecido = enriquecer_nombre_con_procedencia(raiz_actual, Path(nombre_archivo).stem)
            extension = Path(nombre_archivo).suffix

            # Obtener ruta de destino libre de colisiones
            ruta_destino_final = obtener_destino_sin_colision(
                carpeta_destino_abs, nombre_enriquecido, extension
            )
            nombre_final = ruta_destino_final.name

            # Si la ruta destino ya existe (obtener_destino_sin_colision devolvió la ruta original)
            # → revisar si es duplicado exacto
            if ruta_destino_final.exists():
                if es_duplicado_exacto(ruta_archivo, ruta_destino_final):
                    logger.info(f"♻️  DUPLICADO — '{nombre_archivo}' idéntico al destino, omitido")
                    stats["archivos_duplicados"] += 1
                    continue

            # Log de la acción
            cambio_nombre = f" → renombrado a '{nombre_final}'" if nombre_final != nombre_archivo else ""
            logger.info(
                f"🚚 {'SIMULARÍA MOVER' if simular else 'MOVIENDO'} "
                f"'{nombre_archivo}'{cambio_nombre}\n"
                f"   Origen:  {ruta_relativa}\n"
                f"   Destino: {carpeta_destino_rel}/\n"
                f"   Razón:   {razon}"
            )

            stats["archivos_movidos"] += 1

            if not simular:
                try:
                    carpeta_destino_abs.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(ruta_archivo), str(ruta_destino_final))
                except PermissionError as e:
                    msg = f"Permiso denegado al mover '{nombre_archivo}': {e}"
                    logger.error(f"⚠️  {msg}")
                    stats["errores"].append(msg)
                    stats["archivos_movidos"] -= 1
                except Exception as e:
                    msg = f"Error al mover '{nombre_archivo}': {e}"
                    logger.error(f"⚠️  {msg}")
                    stats["errores"].append(msg)
                    stats["archivos_movidos"] -= 1

        # ── Higiene: eliminar carpetas vacías al subir ────────────────
        if raiz_actual != CARPETA_RAIZ and not esta_en_zona_blindada(ruta_relativa):
            try:
                contenido = list(raiz_actual.iterdir())
                if not contenido:
                    logger.info(f"🧹 VACÍA — {'simularía eliminar' if simular else 'eliminando'}: '{ruta_relativa}'")
                    stats["carpetas_eliminadas"] += 1
                    if not simular:
                        raiz_actual.rmdir()
            except (OSError, PermissionError):
                pass

    return stats


# ═══════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="NextVision — Arquitecto de Herencia v2.0"
    )
    parser.add_argument(
        "--simulate", "-s",
        action="store_true",
        help="Modo simulación: reporta acciones sin ejecutarlas"
    )
    args = parser.parse_args()

    simular = args.simulate

    if not CARPETA_RAIZ.exists():
        print(f"❌ ERROR: La carpeta raíz no existe: {CARPETA_RAIZ}")
        sys.exit(1)

    logger = configurar_logging(simular)

    if not simular:
        logger.warning("⚡ MODO PRODUCCIÓN ACTIVO — los archivos serán movidos realmente")
        logger.warning("   Presiona Ctrl+C en los próximos 5 segundos para cancelar...")
        import time
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Cancelado por el usuario.")
            sys.exit(0)

    stats = procesar_carpeta(simular, logger)

    # ── Reporte final ─────────────────────────────────────────────────
    logger.info(f"\n{'═'*60}")
    logger.info("  REPORTE FINAL")
    logger.info(f"{'═'*60}")
    logger.info(f"  📦 Ecosistemas aislados:    {stats['proyectos_aislados']}")
    logger.info(f"  🚚 Archivos movidos:        {stats['archivos_movidos']}")
    logger.info(f"  ✅ Ya organizados/ignorados:{stats['archivos_ignorados']}")
    logger.info(f"  ♻️  Duplicados omitidos:     {stats['archivos_duplicados']}")
    logger.info(f"  🔒 Archivos protegidos:     {stats['archivos_protegidos']}")
    logger.info(f"  🧹 Carpetas eliminadas:     {stats['carpetas_eliminadas']}")

    if stats["errores"]:
        logger.info(f"\n  ⚠️  ERRORES ({len(stats['errores'])}):")
        for err in stats["errores"]:
            logger.error(f"    - {err}")
    else:
        logger.info("  ✅ Sin errores")

    if simular:
        logger.info("\n  ℹ️  Esto fue una simulación. Para ejecutar de verdad:")
        logger.info("     python carpetas.py")

    logger.info(f"{'═'*60}")
    logger.info(f"  Log guardado en: {CARPETA_RAIZ / 'nextvision_organizer.log'}")


if __name__ == "__main__":
    main()