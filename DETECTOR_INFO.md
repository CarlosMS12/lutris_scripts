# 🕵️‍♂️ Detector Universal de Lutris - Resumen de Implementación

## ¿Qué se Realizó?

Se implementó un **sistema de detección automática** que hace que todos tus scripts funcionen tanto con **Lutris Nativo** como con **Lutris Flatpak** sin modificar nada manualmente.

## 📁 Archivo Creado

### `lutris_detector.py`

Módulo central que:

- ✅ Detecta automáticamente si tienes Lutris nativo o Flatpak
- ✅ Si ambos están instalados, pregunta cuál usar (opción 1 o 2)
- ✅ Configura las rutas correctamente según el modo detectado
- ✅ Maneja el caso especial de Flatpak donde TODO está en `data/lutris/`

## 🔧 Archivos Actualizados

### Scripts de ROMs (Inyección):

1. ✅ `mame/roms_mame.py`
2. ✅ `ps1/roms_ps1.py`
3. ✅ `ps2/roms_ps2.py`
4. ✅ `3ds/roms_3ds.py`
5. ✅ `wiiu/roms_wiiu.py`

### Scripts de Data (Descarga de imágenes):

1. ✅ `mame/data.py`
2. ✅ `ps1/data.py`
3. ✅ `ps2/data.py`
4. ✅ `3ds/data.py`
5. ✅ `wiiu/data.py`

### Proyecto Visual:

1. ✅ `proyecto_visual/config.py`

## 🎯 Cómo Funciona

### Antes (Manual):

```python
# Tenías que cambiar manualmente según tu instalación
DB_PATH = os.path.expanduser("~/.local/share/lutris/pga.db")  # Nativo
# o
DB_PATH = os.path.expanduser("~/.var/app/net.lutris.Lutris/data/lutris/pga.db")  # Flatpak
```

### Ahora (Automático):

```python
# Importa el detector
from lutris_detector import get_lutris_paths

# Detecta y configura automáticamente
paths = get_lutris_paths()

# Usa las rutas detectadas
DB_PATH = paths['db_path']
COVERS_DIR = paths['covers_dir']
CONFIG_DIR_MAIN = paths['config_dir_main']  # ¡Crucial para Flatpak!
```

## 🔍 Casos que Maneja

### Caso 1: Solo Lutris Nativo

```
🐧 Modo detectado: NATIVO (Estructura dividida)
   📂 Data: ~/.local/share/lutris
   📂 Config: ~/.config/lutris
```

### Caso 2: Solo Lutris Flatpak

```
🤖 Modo detectado: FLATPAK (Todo en 'data')
   📂 Base: ~/.var/app/net.lutris.Lutris/data/lutris
   📂 Configs: ~/.var/app/net.lutris.Lutris/data/lutris/games/
```

### Caso 3: Ambos Instalados

```
🔍 DETECTADAS DOS INSTALACIONES DE LUTRIS
1️⃣  Nativa    → ~/.local/share/lutris/
2️⃣  Flatpak   → ~/.var/app/net.lutris.Lutris/
¿Cuál deseas usar? (1/2): _
```

### Caso 4: Ninguno Encontrado

```
⚠️  ADVERTENCIA: No se detectó ninguna instalación de Lutris.
Usando rutas nativas por defecto...
```

## 📊 Rutas Configuradas Automáticamente

| Variable           | Nativo                            | Flatpak                                |
| ------------------ | --------------------------------- | -------------------------------------- |
| `db_path`          | `~/.local/share/lutris/pga.db`    | `~/.var/app/.../data/lutris/pga.db`    |
| `covers_dir`       | `~/.local/share/lutris/coverart/` | `~/.var/app/.../data/lutris/coverart/` |
| `banners_dir`      | `~/.local/share/lutris/banners/`  | `~/.var/app/.../data/lutris/banners/`  |
| `lutris_icons_dir` | `~/.local/share/lutris/icons/`    | `~/.var/app/.../data/lutris/icons/`    |
| `config_dir_main`  | `~/.config/lutris/games/`         | `~/.var/app/.../data/lutris/games/` ⚠️ |
| `system_icons_dir` | `~/.local/share/icons/...`        | `~/.local/share/icons/...` (igual)     |

⚠️ **CRÍTICO**: En Flatpak, los archivos `.yml` de configuración están en `data/lutris/games/`, NO en `config/`. El detector maneja esto automáticamente.

## ✨ Ventajas

1. **Cero Configuración Manual**: Los scripts detectan automáticamente tu instalación
2. **Compatibilidad Total**: Funciona con ambas versiones sin modificar código
3. **Selección Inteligente**: Si tienes ambos, puedes elegir cuál usar
4. **Rutas Correctas**: Maneja correctamente la diferencia de estructura entre nativo y Flatpak
5. **Futuro-Proof**: Si cambias de nativo a Flatpak (o viceversa), los scripts siguen funcionando

## 🚀 Uso

Simplemente ejecuta tus scripts como siempre:

```bash
# Scripts de ROMs
python3 mame/roms_mame.py
python3 wiiu/roms_wiiu.py

# Scripts de Data
python3 mame/data.py
python3 wiiu/data.py

# Proyecto Visual
cd proyecto_visual
python3 main.py
```

El detector se encarga de todo automáticamente. Si tienes ambas instalaciones, te preguntará al inicio cuál usar.

## 🧪 Probar el Detector

Puedes probar el detector directamente:

```bash
python3 lutris_detector.py
```

Esto mostrará:

- Qué modo fue detectado
- Todas las rutas configuradas
- Si hay conflicto, te permitirá elegir

## 📝 Notas Técnicas

- El detector usa `os.path.exists()` para verificar la presencia de `pga.db`
- Las rutas se derivan dinámicamente de la ubicación de la base de datos
- `system_icons_dir` siempre es la misma (sistema host) incluso con Flatpak
- La función `get_lutris_paths()` puede llamarse con `interactive=False` para modo silencioso
