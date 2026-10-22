# scripts/analyze_contribution.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, load_icv_data, extract_champions_contribution
from src.plotting import plot_relative_contribution


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config', 'lca_config.yaml')

    config = load_config(config_path)
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])

    icv_path = os.path.join(base_dir, config['paths']['raw_data_icv'])

    print("Procesando Inventario de Ciclo de Vida para análisis de contribución global...")
    df_icv = load_icv_data(icv_path)

    # Detectamos cuántos procesos tienes en total y le decimos que los coja TODOS
    total_procesos = len(df_icv)

    print(f"Extrayendo y disgregando el consumo de los {total_procesos} procesos...")
    df_pct = extract_champions_contribution(df_icv, top_n=total_procesos)

    print("Generando gráfico de barras apiladas al 100%...")
    plot_relative_contribution(df_pct, "Relative_Contribution_100_All", config)


if __name__ == "__main__":
    main()