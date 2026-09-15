# scripts/plot_ecoefficiency.py
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, load_icv_data, clean_sima_pro_data, calculate_ecoefficiency_matrix
from src.plotting import plot_ecoefficiency_matrix


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config', 'lca_config.yaml')
    config = load_config(config_path)
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])

    print("Cargando bases de datos (SimaPro e ICV)...")
    # Cargar SimaPro
    df_homo = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_homo']),
                                  config['skip_rows']['homo'], config['target_categories'])
    df_hetero = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_hetero']),
                                    config['skip_rows']['hetero'], config['target_categories'])

    # Cargar ICV
    df_icv = load_icv_data(os.path.join(base_dir, config['paths']['raw_data_icv']))

    print("Calculando coordenadas de Ecoeficiencia...")
    df_eco = calculate_ecoefficiency_matrix(df_icv, df_homo, df_hetero)

    print("Dibujando el Cuadrante Mágico...")
    plot_ecoefficiency_matrix(df_eco, "EcoEfficiency_Matrix", config)


if __name__ == "__main__":
    main()