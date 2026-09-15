# run_all.py
import subprocess
import sys
import os
import glob

def run_script(script_path):
    """Ejecuta un script de Python y captura si hay errores."""
    print(f"\n{'=' * 60}")
    print(f"🚀 Ejecutando: {script_path}")
    print(f"{'=' * 60}")

    try:
        # sys.executable asegura que usemos el Python del .venv activado
        subprocess.run([sys.executable, script_path], check=True, text=True)
        print(f"✅ {script_path} completado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR fatal al ejecutar {script_path}.")
        print(f"El script falló y detuvo la pipeline. Revisa el error arriba.")
        sys.exit(1)  # Abortamos la ejecución total si un paso falla

def main():
    print("Iniciando la Pipeline dinámica completa de Análisis ACV...")

    # Buscamos todos los archivos .py dentro de la carpeta 'scripts' y los ordenamos alfabéticamente
    search_pattern = os.path.join("scripts", "*.py")
    scripts_to_run = sorted(glob.glob(search_pattern))

    if not scripts_to_run:
        print("⚠️ Advertencia: No se encontró ningún script en la carpeta 'scripts/'.")
        return

    for script in scripts_to_run:
        run_script(script)

    print("\n🎉 ¡Pipeline finalizada! Todos los gráficos Q1 están en la carpeta 'results/'.")

if __name__ == "__main__":
    main()