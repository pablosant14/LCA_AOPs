# scripts/plot_ecoefficiency.py
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, load_icv_data, clean_sima_pro_data, calculate_ecoefficiency_matrix
from src.plotting import plot_ecoefficiency_matrix

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])

    print("Cargando bases de datos (SimaPro e ICV)...")
    df_homo = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_homo']),
                                  config['skip_rows']['homo'], config['target_categories'])
    df_hetero = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_hetero']),
                                    config['skip_rows']['hetero'], config['target_categories'])
    df_icv = load_icv_data(os.path.join(base_dir, config['paths']['raw_data_icv']))

    print("Calculando coordenadas de Ecoeficiencia...")
    df_eco = calculate_ecoefficiency_matrix(df_icv, df_homo, df_hetero)

    if df_eco.empty:
        print("❌ Error: No se pudo mapear ningún proceso.")
        return

    # =========================================================================
    # EL "DREAM TEAM" DE LA TESIS (Narrativa visual completa)
    # =========================================================================
    procesos_estrella = [
        'UV-C/NaClO',                                # El peor escenario
        'UV-C/H2O2',                                 # El clásico
        'UV-C/PMS',                                  # El mejor homogéneo
        '2.5 W/m2 UV-C  + 0.5 g/L LaGa',             # El catalizador base
        '2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PAA' # El sistema optimizado (Estrella)
    ]

    print(f"🌟 Procesos VIP seleccionados: {procesos_estrella}")

    # Filtramos la matriz
    df_eco_final = df_eco[df_eco.index.isin(procesos_estrella)].copy()

    print("Dibujando el Cuadrante Mágico...")
    plot_ecoefficiency_matrix(df_eco_final, "EcoEfficiency_Matrix", config)

if __name__ == "__main__":
    main()