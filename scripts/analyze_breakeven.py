# scripts/analyze_breakeven.py
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, clean_sima_pro_data, calculate_breakeven_cycles
from src.plotting import plot_breakeven_curve


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])

    print("Cargando matrices de SimaPro limpias...")
    df_homo = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_homo']),
                                  config['skip_rows']['homo'], config['target_categories'])

    df_hetero = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_hetero']),
                                    config['skip_rows']['hetero'], config['target_categories'])

    print("Calculando amortización del catalizador...")
    df_breakeven = calculate_breakeven_cycles(None, df_homo, df_hetero, config)

    print("Generando gráfico de Break-Even...")
    plot_breakeven_curve(df_breakeven, "BreakEven_Analysis", config)


if __name__ == "__main__":
    main()