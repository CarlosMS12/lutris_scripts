import sqlite3
import os
import urllib.request
import urllib.parse
import json
import re
import time
import ssl
import subprocess
import shutil
from io import BytesIO
from PIL import Image # <--- NECESITAS INSTALAR ESTO: pip install Pillow

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
API_KEY = "TU_API_KEY_AQUI"
TARGET_RUNNER = "duckstation" # CAMBIA ESTO (mame, duckstation, libretro...)

# CORRECCIONES MANUALES
MANUAL_FIXES = {
    "BloodyRoarII": "Bloody Roar 2",
    "kof2002": "The King of Fighters 2002",
    "MarvelVsCapcom": "Marvel vs. Capcom: Clash of Super Heroes"
}

# Ruta MAME
MAME_EXE = "/usr/games/mame" # Ajusta según tu distro si usas MAME
# ==========================================

# RUTAS
DB_PATH = os.path.expanduser("~/.local/share/lutris/pga.db")
COVERS_DIR = os.path.expanduser("~/.local/share/lutris/coverart/")
BANNERS_DIR = os.path.expanduser("~/.local/share/lutris/banners/")
LUTRIS_ICONS_DIR = os.path.expanduser("~/.local/share/lutris/icons/")
SYSTEM_ICONS_DIR = os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps/")

# SSL Bypass
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_mame_candidates(slug):
    # (Misma lógica de MAME que antes, la omito para ahorrar espacio pero debe estar aquí)
    candidates = []
    return candidates

def clean_console_name(name):
    # Limpieza inteligente
    clean = name
    clean = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean)
    clean = re.sub(r'(\D)(\d)', r'\1 \2', clean)
    clean = os.path.splitext(clean)[0]
    clean = clean.replace("_", " ").replace(".", " ")
    clean = re.sub(r'\(.*?\)', '', clean)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean

def sgdb_search(query):
    url = f"https://www.steamgriddb.com/api/v2/search/autocomplete/{urllib.parse.quote(query)}"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx) as r:
            return json.loads(r.read().decode())
    except: return None

def sgdb_get_images(game_id):
    base = "https://www.steamgriddb.com/api/v2"
    headers = {'Authorization': f'Bearer {API_KEY}'}
    urls = {}
    try:
        # Cover
        r = urllib.request.Request(f"{base}/grids/game/{game_id}?dimensions=600x900&styles=alternate,material", headers=headers)
        with urllib.request.urlopen(r, context=ctx) as resp:
            d = json.loads(resp.read().decode())
            if d['data']: urls['cover'] = d['data'][0]['url']
        # Banner
        r = urllib.request.Request(f"{base}/heroes/game/{game_id}", headers=headers)
        with urllib.request.urlopen(r, context=ctx) as resp:
            d = json.loads(resp.read().decode())
            if d['data']: urls['banner'] = d['data'][0]['url']
        # Icon
        r = urllib.request.Request(f"{base}/icons/game/{game_id}", headers=headers)
        with urllib.request.urlopen(r, context=ctx) as resp:
            d = json.loads(resp.read().decode())
            if d['data']: urls['icon'] = d['data'][0]['url']
    except: pass
    return urls

def download(url, path):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as r:
            with open(path, 'wb') as f: f.write(r.read())
        return True
    except: return False

def download_and_convert_icon(url, save_path):
    """
    Descarga la imagen y la CONVIERTE a PNG real usando Pillow.
    Esto soluciona el error de iconos invisibles en Linux Mint.
    """
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            # 1. Leer imagen en memoria
            img_data = response.read()
            image = Image.open(BytesIO(img_data))

            # 2. Convertir y guardar como PNG
            image.save(save_path, "PNG")
            return True
    except Exception as e:
        print(f"      ⚠️ Error convirtiendo icono: {e}")
        return False

def run_decorator():
    if API_KEY == "TU_API_KEY_AQUI":
        print("❌ Error: Falta la API KEY.")
        return

    # Crear carpetas
    dirs_to_check = [COVERS_DIR, BANNERS_DIR, LUTRIS_ICONS_DIR, SYSTEM_ICONS_DIR]
    for d in dirs_to_check:
        if not os.path.exists(d):
            try: os.makedirs(d)
            except: pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🎨 Decorador V5 (Mint Fix - Pillow) para: {TARGET_RUNNER}")
    cursor.execute("SELECT id, slug, name FROM games WHERE runner = ? AND installed = 1", (TARGET_RUNNER,))
    games = cursor.fetchall()

    count = 0
    for game_id, slug, raw_name in games:
        p_cover = os.path.join(COVERS_DIR, f"{slug}.jpg")
        p_banner = os.path.join(BANNERS_DIR, f"{slug}.jpg")
        p_icon_lutris = os.path.join(LUTRIS_ICONS_DIR, f"{slug}.png")
        p_icon_system = os.path.join(SYSTEM_ICONS_DIR, f"lutris_{slug}.png")

        # OJO: Quitamos el check de "si ya existe" para forzar la reparación de iconos malos
        # Si quieres velocidad, descomenta las siguientes líneas después de arreglarlo una vez:
        # if os.path.exists(p_cover) and os.path.exists(p_banner) and os.path.exists(p_icon_system):
        #    continue

        print(f"\n🔍 Procesando: {slug}")

        # Búsqueda (simplificada aquí, usa la lógica completa de V4)
        clean = clean_console_name(raw_name)
        candidates = []
        if slug in MANUAL_FIXES: candidates.append(MANUAL_FIXES[slug])
        if clean not in candidates: candidates.append(clean)

        found_id = None
        found_name = None

        for cand in candidates:
            res = sgdb_search(cand)
            if res and res['success'] and res['data']:
                found_id = res['data'][0]['id']
                found_name = res['data'][0]['name']
                print(f"      ✅ ENCONTRADO: {found_name}")
                break
            time.sleep(0.2)

        if found_id:
            images = sgdb_get_images(found_id)
            updated = False

            # Cover y Banner (Descarga normal)
            if images.get('cover') and not os.path.exists(p_cover):
                download(images['cover'], p_cover)
                updated = True
            if images.get('banner') and not os.path.exists(p_banner):
                download(images['banner'], p_banner)
                updated = True

            # --- ICONOS CON CONVERSIÓN ---
            if images.get('icon'):
                print("      🔄 Convirtiendo icono a PNG real...")
                # Usamos la nueva función con Pillow
                if download_and_convert_icon(images['icon'], p_icon_lutris):
                    try:
                        shutil.copy2(p_icon_lutris, p_icon_system)
                        print("      👾 Icono arreglado instalado.")
                        updated = True
                    except: pass

            if updated:
                cursor.execute("""
                    UPDATE games
                    SET name=?, sortname=?, has_custom_banner=1, has_custom_icon=1, has_custom_coverart_big=1
                    WHERE id=?
                """, (found_name, found_name, game_id))
                count += 1
                conn.commit()
        else:
            print("   ❌ No se encontró.")

    conn.close()
    print(f"\n🎉 ¡Hecho! {count} juegos actualizados.")
    print("👉 EJECUTA ESTO EN TERMINAL: gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor")
    print("👉 Y borra caché de Lutris: rm -rf ~/.cache/lutris/coverart/*")

if __name__ == "__main__":
    run_decorator()
