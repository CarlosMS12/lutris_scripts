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

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
API_KEY = "4e712a33643639391ac4f80886ace444" 
TARGET_RUNNER = "mame" # CAMBIA ESTO (mame, duckstation, libretro...)

# CORRECCIONES MANUALES (Por si algún juego se resiste)
MANUAL_FIXES = {
    "BloodyRoarII": "Bloody Roar 2",
    "kof2002": "The King of Fighters 2002",
    "MarvelVsCapcom": "Marvel vs. Capcom: Clash of Super Heroes"
}

# Ruta MAME (Solo si usas MAME)
MAME_EXE = "/home/carlos/Descargas/MAME/MAME-0.283-1-anylinux-x86_64.AppImage"
# ==========================================

# --- RUTAS DE LUTRIS ---
DB_PATH = os.path.expanduser("~/.local/share/lutris/pga.db")
COVERS_DIR = os.path.expanduser("~/.local/share/lutris/coverart/")
BANNERS_DIR = os.path.expanduser("~/.local/share/lutris/banners/")
LUTRIS_ICONS_DIR = os.path.expanduser("~/.local/share/lutris/icons/")

# --- RUTA DEL SISTEMA (EL HALLAZGO) ---
SYSTEM_ICONS_DIR = os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps/")

# SSL Bypass
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def get_mame_candidates(slug):
    """Genera lista de nombres para MAME"""
    candidates = []
    if not os.path.exists(MAME_EXE): return []
    try:
        result = subprocess.run([MAME_EXE, "-listfull", slug], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if line.startswith(slug):
                match = re.search(r'"([^"]+)"', line)
                if match: 
                    full_text = match.group(1)
                    primary_name = full_text.split("/")[0].strip()
                    primary_name = re.sub(r'\s*\(.*?\)', '', primary_name).strip()
                    if primary_name: candidates.append(primary_name)
                    for sep in [" - ", ": "]:
                        if sep in primary_name:
                            short = primary_name.split(sep)[0].strip()
                            if len(short) > 2 and short not in candidates:
                                candidates.append(short)
                                break 
    except: pass
    return candidates

def clean_console_name(name):
    """Limpieza inteligente (CamelCase y caracteres raros)"""
    clean = name
    # BloodyRoar -> Bloody Roar
    clean = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean)
    # Tekken3 -> Tekken 3
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
        # Icon (IMPORTANTE: Endpoint de iconos)
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

def run_decorator():
    if API_KEY == "TU_API_KEY_AQUI":
        print("❌ Error: Falta la API KEY.")
        return

    # Crear TODAS las carpetas necesarias
    dirs_to_check = [COVERS_DIR, BANNERS_DIR, LUTRIS_ICONS_DIR, SYSTEM_ICONS_DIR]
    for d in dirs_to_check:
        if not os.path.exists(d): 
            try:
                os.makedirs(d)
                print(f"📁 Carpeta creada: {d}")
            except: pass

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🎨 Decorador V4 (Sistema + Lutris) para: {TARGET_RUNNER}")
    cursor.execute("SELECT id, slug, name FROM games WHERE runner = ? AND installed = 1", (TARGET_RUNNER,))
    games = cursor.fetchall()

    count = 0
    for game_id, slug, raw_name in games:
        # Rutas de destino
        # Nota: Usamos .png para los iconos por estándar de Linux, aunque la fuente sea jpg
        p_cover = os.path.join(COVERS_DIR, f"{slug}.jpg")
        p_banner = os.path.join(BANNERS_DIR, f"{slug}.jpg")
        p_icon_lutris = os.path.join(LUTRIS_ICONS_DIR, f"{slug}.png")
        p_icon_system = os.path.join(SYSTEM_ICONS_DIR, f"lutris_{slug}.png") # EL FORMATO CORRECTO
        
        # Si ya existe TODO, saltamos
        if os.path.exists(p_cover) and os.path.exists(p_banner) and os.path.exists(p_icon_system):
            continue

        print(f"\n🔍 Procesando: {slug}")
        
        # 1. Buscar Nombre
        candidates = []
        if slug in MANUAL_FIXES: candidates.append(MANUAL_FIXES[slug])
        if TARGET_RUNNER == "mame": candidates.extend(get_mame_candidates(slug))
        
        clean = clean_console_name(raw_name)
        if clean not in candidates: candidates.append(clean)
            
        found_id = None
        found_name = None
        
        for cand in candidates:
            print(f"   👉 Buscando: '{cand}'...")
            res = sgdb_search(cand)
            if res and res['success'] and res['data']:
                found_id = res['data'][0]['id']
                found_name = res['data'][0]['name']
                print(f"      ✅ ENCONTRADO: {found_name}")
                break 
            else:
                time.sleep(0.2)
        
        # 3. Descargar
        if found_id:
            images = sgdb_get_images(found_id)
            updated = False
            
            if images.get('cover') and download(images['cover'], p_cover): updated = True
            if images.get('banner') and download(images['banner'], p_banner): updated = True
            
            # --- MAGIA DE ICONOS ---
            if images.get('icon'):
                # 1. Descargar para Lutris Interno
                if download(images['icon'], p_icon_lutris):
                    # 2. Copiar para el Sistema (lutris_slug.png)
                    try:
                        shutil.copy2(p_icon_lutris, p_icon_system)
                        print("      👾 Icono instalado en Sistema y Lutris.")
                        updated = True
                    except Exception as e:
                        print(f"      ⚠️ Error copiando icono al sistema: {e}")
                        updated = True # Al menos se bajó el de Lutris

            if updated:
                cursor.execute("""
                    UPDATE games 
                    SET name=?, sortname=?, has_custom_banner=1, has_custom_icon=1, has_custom_coverart_big=1
                    WHERE id=?
                """, (found_name, found_name, game_id))
                count += 1
                conn.commit()
            else:
                print("      ⚠️ Juego encontrado pero faltan imágenes.")
        else:
            print("   ❌ No se encontró.")

    conn.close()
    print(f"\n🎉 ¡Hecho! {count} juegos actualizados.")
    print("👉 Reinicia Lutris para ver los cambios.")

if __name__ == "__main__":
    run_decorator()