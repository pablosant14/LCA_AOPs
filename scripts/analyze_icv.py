# scripts/analyze_icv.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, load_icv_data
from src.plotting import plot_icv_dual_axis


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config', 'lca_config.yaml')

    config = load_config(config_path)
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])
    icv_path = os.path.join(base_dir, config['paths']['raw_data_icv'])

    print("Procesando matriz del Inventario de Ciclo de Vida (ICV)...")
    df_icv = load_icv_data(icv_path)

    plot_icv_dual_axis(df_icv, "ICV_Inventory_Inputs", config)


if __name__ == "__main__":
    main()