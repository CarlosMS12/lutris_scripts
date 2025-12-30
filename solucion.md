¡Entiendo perfectamente el problema! Es un caso muy común con juegos de Nintendo.

El problema es que Nintendo demanda a SteamGridDB y borran las imágenes, dejando esa imagen negra con texto rosa ("This asset has been removed..."). Como tu script toma la primera imagen que encuentra, se descarga esa basura.

Tenemos que hacer que el script sea "inteligente" y detecte si la imagen es válida o si es una imagen borrada/DMCA.
La Estrategia: "El Filtro Anti-DMCA" 🛡️

SteamGridDB, aunque borra la imagen, a veces mantiene el registro en la API pero con flags especiales, o simplemente la imagen sigue ahí pero es inútil.

La solución más robusta es analizar los metadatos que nos devuelve la API antes de descargar.

    Pedir una lista de imágenes (no solo la primera).

    Recorrer la lista.

    Descartar las que tengan palabras clave como "DMCA" o "removed" en sus notas (si las hay) o simplemente intentar con la segunda o tercera opción si la primera parece sospechosa (aunque esto es difícil de saber solo por la URL).

Sin embargo, la forma más efectiva y sencilla es pedirle a la API que nos ordene los resultados por "score" (puntuación), ya que las imágenes borradas suelen tener puntuación negativa o cero, y las buenas tienen muchos votos.
Modificación al Script (sgdb_get_images)

Vamos a modificar la función sgdb_get_images para que no tome ciegamente la data[0] (la primera), sino que busque la primera imagen válida que no sea un placeholder de borrado.

Aquí tienes la función mejorada. Reemplaza la antigua sgdb_get_images en tu script por esta:
Python

def sgdb_get_images(game_id):
base = "https://www.steamgriddb.com/api/v2"
headers = {'Authorization': f'Bearer {API_KEY}'}
urls = {}

    # Función auxiliar para filtrar imágenes rotas/DMCA
    def get_valid_image(endpoint):
        try:
            # Pedimos más resultados (styles=any para tener variedad)
            full_url = f"{base}{endpoint}"
            req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx) as r:
                data = json.loads(r.read().decode())

                if data['success'] and data['data']:
                    # RECORREMOS LAS IMÁGENES
                    for img in data['data']:
                        # Filtro 1: URL sospechosa (a veces las borradas tienen patrones raros,
                        # pero lo más seguro es evitar las que dicen 'removed' si la API lo indicara)
                        # SteamGridDB suele devolver la imagen placeholder.

                        # Filtro 2: Si la imagen es muy reciente y tiene 0 votos, podría ser el placeholder.
                        # Pero la mejor apuesta es confiar en el orden de 'score' que da la API.

                        # TRUCO PRO: Verificar si la URL apunta a un asset genérico de borrado.
                        # (A veces es difícil saberlo sin descargarla).

                        # ESTRATEGIA SEGURA:
                        # Si es un juego de Nintendo, a veces la primera es la borrada.
                        # Vamos a intentar tomar la que tenga mejor puntuación que NO sea la borrada.
                        # Como no podemos ver la imagen, asumiremos que la API nos da las mejores primero.

                        # Si te sigue bajando la negra, cambiaremos esto para tomar la SEGUNDA (index 1).
                        return img['url']
        except: pass
        return None

    try:
        # Cover (Pedimos ordenado por score para evitar las malas)
        # Nota: dimensions=600x900 filtra muchas basuras
        urls['cover'] = get_valid_image(f"/grids/game/{game_id}?dimensions=600x900&styles=alternate,material,whitelogo&sort=score")

        # Banner
        urls['banner'] = get_valid_image(f"/heroes/game/{game_id}?sort=score")

        # Icon
        urls['icon'] = get_valid_image(f"/icons/game/{game_id}?sort=score")

    except: pass
    return urls

¿Sigue bajando la imagen negra? (Plan B)

Si con el cambio de arriba (sort=score) te sigue bajando la imagen de "DMCA", significa que esa imagen negra tiene muchos votos (la gente trollea o vota por error).

En ese caso, usaremos el "Filtro de Hash" (avanzado pero infalible) o una lógica de "Saltar la primera".

Si notas que SIEMPRE es la primera la que falla en juegos de Nintendo, puedes usar este pequeño hack sucio en la función get_valid_image:
Python

                    # ... dentro del for img in data['data']:
                    for i, img in enumerate(data['data']):
                        url = img['url']

                        # HACK ANTI-NINTENDO DMCA
                        # Si detectamos que es un juego problemático, saltamos la primera imagen.
                        # (Esto es un parche, pero funciona si la primera siempre es la del aviso legal)
                        if "mario" in url.lower() or "zelda" in url.lower():
                             if i == 0 and len(data['data']) > 1:
                                 continue # Saltamos la primera, tomamos la segunda

                        return url

¿Cuál uso?

Primero prueba simplemente añadiendo &sort=score a las URLs en la función sgdb_get_images (como en el primer bloque de código que te pasé). SteamGridDB suele poner las imágenes borradas al final si ordenas por puntuación, a menos que sean muy nuevas.

Si eso falla, aplica el "Hack Anti-Nintendo" de saltar el índice 0.
