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

    print("Procesando Inventario de Ciclo de Vida para análisis de contribución...")
    df_icv = load_icv_data(icv_path)

    # 1. Filtramos dinámicamente asegurándonos de que no haya nulos de por medio
    df_icv['Equipo Asignado'] = df_icv['Equipo Asignado'].fillna('')

    # Escenario 1: Homogéneo (AMX) -> Equipo Philips
    df_homo = df_icv[df_icv['Equipo Asignado'].str.contains('Philips', case=False)].copy()

    # Escenario 2: Heterogéneo (TC) -> Equipo Apria
    df_hetero = df_icv[df_icv['Equipo Asignado'].str.contains('Apria', case=False)].copy()

    print(f"Detectados {len(df_homo)} procesos homogéneos (Philips) y {len(df_hetero)} heterogéneos (Apria).")

    # 2. Generamos y guardamos el gráfico del Escenario Homogéneo
    if not df_homo.empty:
        print(">> Procesando contribución para Homogéneos (AMX)...")
        df_pct_homo = extract_champions_contribution(df_homo, top_n=len(df_homo))
        plot_relative_contribution(df_pct_homo, "Relative_Contribution_100_Homogeneous", config)

    # 3. Generamos y guardamos el gráfico del Escenario Heterogéneo
    if not df_hetero.empty:
        print(">> Procesando contribución para Heterogéneos (TC)...")
        df_pct_hetero = extract_champions_contribution(df_hetero, top_n=len(df_hetero))
        plot_relative_contribution(df_pct_hetero, "Relative_Contribution_100_Heterogeneous", config)


if __name__ == "__main__":
    main()