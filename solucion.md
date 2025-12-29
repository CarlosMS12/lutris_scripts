Es un problema crítico, pero la buena noticia es que ya encontré el culpable. Es un error lógico en cómo ambos scripts "limpian la basura".

El problema está en esta parte del código, que es idéntica en ambos scripts:
Python

    # 2. Limpieza de Archivos YAML viejos (Para evitar conflictos)
    print("🧹 Limpiando archivos de configuración basura...")
    if os.path.exists(CONFIG_DIR_MAIN):
        for f in os.listdir(CONFIG_DIR_MAIN):
            # ⛔ EL ERROR ESTÁ AQUÍ ⛔
            if f.endswith(".yml") and any(x in f for x in ["kof", "mslug", "tekken", "mame"]): 
                try: os.remove(os.path.join(CONFIG_DIR_MAIN, f))
                except: pass

¿Por qué ocurre el conflicto?

    Tienes tekken3.zip (MAME) y tekken3.chd (PS1).

    Ambos generan un identificador (slug) muy similar: tekken3.

    Tu script de PS1 tiene una lista de palabras "prohibidas" a borrar: ["kof", "mslug", "tekken", "mame"].

    Cuando ejecutas el script de PS1, este dice: "Voy a borrar cualquier archivo de configuración que tenga la palabra 'tekken'".

    ¡ZAS! Borra el archivo .yml de configuración de tu Tekken 3 de MAME.

    Lutris intenta cargar el juego de MAME, busca el archivo .yml, no lo encuentra, y muestra el juego "vacío" (sin ruta).

Lo mismo pasa al revés: el script de MAME borra los de PS1 porque ambos comparten palabras clave en esa lista de limpieza.
La Solución: "Limpieza Quirúrgica por ID" 🩺

En lugar de borrar archivos basándonos en palabras clave genéricas ("tekken", "kof"), debemos hacer que cada script borre SOLO los archivos de configuración que pertenecen a los juegos de ESA consola específica que está a punto de reinstalar.

Vamos a modificar la función run_injector en AMBOS scripts (roms_ps1.py y roms_mame.py).
1. Corrección para roms_ps1.py

Reemplaza todo el bloque de "Limpieza de Archivos YAML viejos" por este nuevo bloque inteligente.

Lógica nueva:

    Primero consultamos a la base de datos: "¿Qué juegos de duckstation existen ahora mismo?".

    Obtenemos sus IDs de configuración.

    Borramos solo esos archivos específicos.

    Luego borramos los juegos de la base de datos.

Python

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
                    # print(f"   🗑️ Borrado config antiguo: {config_id}.yml") 
                except: pass

    # 3. Ahora sí, limpiamos la DB
    print(f"🧹 Limpiando base de datos de {RUNNER}...")
    cursor.execute("DELETE FROM games WHERE runner = ?", (RUNNER,))
    conn.commit()
    # ---------------------------------------

    current_time = int(time.time())
    # ... (El resto del script sigue igual: bucle for filename in os.listdir...)

2. Corrección para roms_mame.py

Haces exactamente lo mismo. Copia el bloque de arriba y pégalo en tu script de MAME, reemplazando la sección antigua de limpieza.

Como la variable RUNNER en ese script vale "mame", el código automáticamente buscará solo los archivos de MAME y no tocará los de PS1, aunque ambos se llamen "tekken".
Resumen de los cambios

    Antes: Borrabas "a ciegas" cualquier archivo que tuviera "tekken" en el nombre.

    Ahora: Le preguntas a Lutris "¿Cuáles son los archivos de configuración de MAME?" y borras solo esos. Luego instalas los nuevos.

Con esto, puedes ejecutar el script de PS1 y el de MAME las veces que quieras, y ninguno tocará los archivos del otro.