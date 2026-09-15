# scripts/exploratory_lca.py
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, clean_sima_pro_data, dynamic_impact_filter
from src.plotting import plot_impact_heatmap, plot_radar_chart


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

    print("Cargando matrices de SimaPro...")
    df_homo = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_homo']),
                                  config['skip_rows']['homo'], config['target_categories'])

    df_hetero = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_hetero']),
                                    config['skip_rows']['hetero'], config['target_categories'])

    # 1. Unimos todo
    df_total = pd.concat([df_homo, df_hetero], axis=1)

    # 2. Criba Dinámica: Nos quedamos con los 4 mejores y los 4 peores según Climate change
    print("Aplicando criba dinámica (Top/Bottom impactos)...")
    df_cribado = dynamic_impact_filter(df_total, target_metric='Climate change', top_n=4)

    # 3. Dibujamos solo lo cribado
    print("Generando Heatmap cribado...")
    plot_impact_heatmap(df_cribado, "EDA_Impact_Heatmap_Filtered", config)

    print("Generando Gráfico de Radar cribado...")
    plot_radar_chart(df_cribado, "EDA_Radar_Chart_Filtered", config)


if __name__ == "__main__":
    main()