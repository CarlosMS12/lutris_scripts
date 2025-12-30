import os
import sqlite3
import time
import textwrap
import sys

# Importar el detector universal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lutris_detector import get_lutris_paths

# ==========================================
# ⚡ CONFIGURACIÓN (CAMBIA ESTO SEGÚN LA CONSOLA)
# ==========================================
ROM_FOLDER = "/home/carlos/Descargas/Moon/Roms/wiiu/"
EXTENSION = ".wud"
RUNNER = "cemu"       # Ej: mame, libretro, pcsx2
PLATFORM = "Nintendo WII U"   # Ej: Arcade, Sony PlayStation, Nintendo 64
# ==========================================

# 🕵️‍♂️ DETECCIÓN AUTOMÁTICA DE LUTRIS (NATIVO/FLATPAK)
print("🔍 Detectando instalación de Lutris...")
paths = get_lutris_paths()

DB_PATH = paths['db_path']
CONFIG_DIR_MAIN = paths['config_dir_main']

def create_lutris_yaml(game_slug, rom_path, timestamp):
    # Nombre base: slug + timestamp
    base_name = f"{game_slug}-{timestamp}"
    filename_real = f"{base_name}.yml"
    
    # Guardamos en .config (CRÍTICO: Esto es lo que hizo que funcionara)
    full_yaml_path = os.path.join(CONFIG_DIR_MAIN, filename_real)

    yaml_content = f"""
game:
  main_file: {rom_path}
system:
  disable_runtime: true
  prefer_system_libs: true
"""
    if not os.path.exists(CONFIG_DIR_MAIN):
        os.makedirs(CONFIG_DIR_MAIN)

    with open(full_yaml_path, "w") as f:
        f.write(yaml_content.strip())
    
    return base_name

def run_injector():
    if not os.path.exists(ROM_FOLDER):
        print(f"❌ Error: No existe la carpeta: {ROM_FOLDER}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- NUEVA LÓGICA DE LIMPIEZA SEGURA ---
    print(f"🧹 Identificando archivos de configuración de {RUNNER} para borrar...")
    
    # 1. Obtenemos los 'configpath' de los juegos que vamos a reemplazar (SOLO de esta consola)
    cursor.execute("SELECT configpath FROM games WHERE runner = ?", (RUNNER,))
    old_configs = cursor.fetchall()
    
    # 2. Borramos físicamente esos archivos .yml específicos
    for row in old_configs:
        config_id = row[0]
        if config_id:
            yaml_path = os.path.join(CONFIG_DIR_MAIN, f"{config_id}.yml")
            if os.path.exists(yaml_path):
                try:
                    os.remove(yaml_path)
                except: pass

    # 3. Ahora sí, limpiamos la DB
    print(f"🧹 Limpiando base de datos de {RUNNER}...")
    cursor.execute("DELETE FROM games WHERE runner = ?", (RUNNER,))
    conn.commit()
    # ---------------------------------------

    current_time = int(time.time())
    count = 0
    print(f"🚀 Inyectando juegos desde: {ROM_FOLDER}")

    for filename in os.listdir(ROM_FOLDER):
        if filename.lower().endswith(EXTENSION):
            game_slug = os.path.splitext(filename)[0]
            game_name = game_slug 
            full_rom_path = os.path.join(ROM_FOLDER, filename)
            
            unique_time = current_time + count 
            
            # Crear YAML en .config
            config_id = create_lutris_yaml(game_slug, full_rom_path, unique_time)

            try:
                # Insertar en DB
                # directory y executable en NULL (como descubrimos en el CSV)
                cursor.execute("""
                    INSERT INTO games (
                        name, slug, runner, executable, directory, configpath, 
                        installed, installed_at, platform, lastplayed,
                        has_custom_banner, has_custom_icon, has_custom_coverart_big, playtime
                    )
                    VALUES (?, ?, ?, NULL, NULL, ?, 1, ?, ?, 0, 0, 0, 0, 0)
                """, (game_name, game_slug, RUNNER, config_id, unique_time, PLATFORM))
                
                count += 1
                print(f"✅ Agregado: {game_name}")
            except sqlite3.Error as e:
                print(f"⚠️ Error SQL con {game_name}: {e}")

    conn.commit()
    conn.close()
    print(f"\n🎉 ¡Inyección Completa! {count} juegos agregados.")
    print("👉 IMPORTANTE: Cierra Lutris y vuélvelo a abrir para verificar que salen.")

if __name__ == "__main__":
    run_injector()