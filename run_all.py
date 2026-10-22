import subprocess
import sys
import os
import glob

def run_script(script_path):
    print(f"\n{'=' * 60}")
    print(f"🚀 Ejecutando: {script_path}")
    print(f"{'=' * 60}")
    try:
        subprocess.run([sys.executable, script_path], check=True, text=True)
        print(f"✅ {script_path} completado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR: El script {script_path} falló.")
        print(f"⚠️ Aislando el error y saltando al siguiente gráfico para no detener la pipeline...")

def main():
    print("Iniciando la Pipeline dinámica completa de Análisis ACV...")
    search_pattern = os.path.join("scripts", "*.py")
    scripts_to_run = sorted(glob.glob(search_pattern))

    if not scripts_to_run:
        print("⚠️ Advertencia: No se encontró ningún script en la carpeta 'scripts/'.")
        return

    for script in scripts_to_run:
        run_script(script)

    print("\n🎉 ¡Pipeline finalizada! Revisa la consola para ver qué gráficos se generaron y cuáles fallaron.")

if __name__ == "__main__":
    main()