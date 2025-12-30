"""
🕵️‍♂️ Detector Universal de Lutris
Detecta automáticamente si Lutris es Nativo o Flatpak y configura las rutas
"""
import os
import sys

class LutrisDetector:
    """Clase para detectar y configurar rutas de Lutris"""
    
    # Rutas potenciales de la base de datos
    PATH_NATIVE_DB = os.path.expanduser("~/.local/share/lutris/pga.db")
    PATH_FLATPAK_DB = os.path.expanduser("~/.var/app/net.lutris.Lutris/data/lutris/pga.db")
    
    def __init__(self):
        self.mode = None
        self.db_path = None
        self.covers_dir = None
        self.banners_dir = None
        self.lutris_icons_dir = None
        self.config_dir_main = None
        self.system_icons_dir = None  # Se configurará según el modo detectado
        
        self._detect_and_configure()
    
    def _detect_and_configure(self):
        """Detecta el modo de Lutris y configura las rutas"""
        native_exists = os.path.exists(self.PATH_NATIVE_DB)
        flatpak_exists = os.path.exists(self.PATH_FLATPAK_DB)
        
        # CASO 1: Ambos existen - Preguntar al usuario
        if native_exists and flatpak_exists:
            print("\n" + "="*60)
            print("🔍 DETECTADAS DOS INSTALACIONES DE LUTRIS")
            print("="*60)
            print("1️⃣  Nativa    → ~/.local/share/lutris/")
            print("2️⃣  Flatpak   → ~/.var/app/net.lutris.Lutris/")
            print("="*60)
            
            while True:
                choice = input("\n¿Cuál deseas usar? (1/2): ").strip()
                if choice == "1":
                    self._configure_native()
                    break
                elif choice == "2":
                    self._configure_flatpak()
                    break
                else:
                    print("❌ Opción inválida. Elige 1 o 2.")
        
        # CASO 2: Solo Flatpak
        elif flatpak_exists:
            self._configure_flatpak()
        
        # CASO 3: Solo Nativo
        elif native_exists:
            self._configure_native()
        
        # CASO 4: Ninguno encontrado
        else:
            print("\n⚠️  ADVERTENCIA: No se detectó ninguna instalación de Lutris.")
            print("Usando rutas nativas por defecto...")
            self._configure_native_default()
    
    def _configure_flatpak(self):
        """Configura rutas para Lutris Flatpak"""
        self.mode = "FLATPAK"
        print("\n🤖 Modo detectado: FLATPAK (Todo en 'data')")
        
        # En Flatpak, TODO vive en .../data/lutris
        base_lutris = os.path.dirname(self.PATH_FLATPAK_DB)
        # Base de la app Flatpak (un nivel arriba de data/lutris)
        base_flatpak = os.path.dirname(os.path.dirname(base_lutris))  # ~/.var/app/net.lutris.Lutris
        
        self.db_path = os.path.join(base_lutris, "pga.db")
        self.covers_dir = os.path.join(base_lutris, "coverart/")
        self.banners_dir = os.path.join(base_lutris, "banners/")
        self.lutris_icons_dir = os.path.join(base_lutris, "icons/")
        
        # ⚠️ CRÍTICO: En Flatpak, los YAML están en data/lutris/games/, NO en config
        self.config_dir_main = os.path.join(base_lutris, "games/")
        
        # ⚠️ CRÍTICO: En Flatpak, los iconos del "sistema" van en la carpeta data de la app
        self.system_icons_dir = os.path.join(base_flatpak, "data/icons/hicolor/128x128/apps/")
        
        print(f"   📂 Base: {base_lutris}")
        print(f"   📂 Configs: {self.config_dir_main}")
        print(f"   📂 System Icons: {self.system_icons_dir}")
    
    def _configure_native(self):
        """Configura rutas para Lutris Nativo"""
        self.mode = "NATIVO"
        print("\n🐧 Modo detectado: NATIVO (Estructura dividida)")
        
        base_data = os.path.dirname(self.PATH_NATIVE_DB)  # ~/.local/share/lutris
        base_config = os.path.expanduser("~/.config/lutris")
        
        self.db_path = os.path.join(base_data, "pga.db")
        self.covers_dir = os.path.join(base_data, "coverart/")
        self.banners_dir = os.path.join(base_data, "banners/")
        self.lutris_icons_dir = os.path.join(base_data, "icons/")
        
        # En Nativo, sí se separan en .config
        self.config_dir_main = os.path.join(base_config, "games/")
        
        # En Nativo, los iconos del sistema van a la ruta estándar del usuario
        self.system_icons_dir = os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps/")
        
        print(f"   📂 Data: {base_data}")
        print(f"   📂 Config: {base_config}")
    
    def _configure_native_default(self):
        """Configura rutas nativas por defecto (cuando no se encuentra Lutris)"""
        self.mode = "NATIVO_DEFAULT"
        
        base_data = os.path.expanduser("~/.local/share/lutris")
        base_config = os.path.expanduser("~/.config/lutris")
        
        self.db_path = os.path.join(base_data, "pga.db")
        self.covers_dir = os.path.join(base_data, "coverart/")
        self.banners_dir = os.path.join(base_data, "banners/")
        self.lutris_icons_dir = os.path.join(base_data, "icons/")
        self.config_dir_main = os.path.join(base_config, "games/")
        self.system_icons_dir = os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps/")
    
    def get_paths(self):
        """Retorna un diccionario con todas las rutas configuradas"""
        return {
            'mode': self.mode,
            'db_path': self.db_path,
            'covers_dir': self.covers_dir,
            'banners_dir': self.banners_dir,
            'lutris_icons_dir': self.lutris_icons_dir,
            'config_dir_main': self.config_dir_main,
            'system_icons_dir': self.system_icons_dir
        }
    
    def print_summary(self):
        """Imprime un resumen de las rutas configuradas"""
        print("\n" + "="*60)
        print(f"✅ CONFIGURACIÓN {self.mode}")
        print("="*60)
        print(f"DB:       {self.db_path}")
        print(f"Covers:   {self.covers_dir}")
        print(f"Banners:  {self.banners_dir}")
        print(f"Icons:    {self.lutris_icons_dir}")
        print(f"Configs:  {self.config_dir_main}")
        print(f"Sistema:  {self.system_icons_dir}")
        print("="*60 + "\n")


def get_lutris_paths(interactive=True):
    """
    Función de conveniencia para obtener las rutas de Lutris
    
    Args:
        interactive: Si es True, pregunta al usuario cuando hay ambas instalaciones
    
    Returns:
        dict con las rutas configuradas
    """
    detector = LutrisDetector()
    if interactive:
        detector.print_summary()
    return detector.get_paths()


# Ejemplo de uso directo
if __name__ == "__main__":
    print("🕵️‍♂️ Detector de Lutris\n")
    paths = get_lutris_paths()
    
    print("\n📋 Rutas detectadas:")
    for key, value in paths.items():
        print(f"  {key}: {value}")
