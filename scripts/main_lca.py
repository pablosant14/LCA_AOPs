# scripts/main_lca.py
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing import load_config, clean_sima_pro_data
from src.plotting import plot_impact_comparison


def main():
    # Calculamos la ruta absoluta de la raíz del proyecto dinámicamente
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(base_dir, 'config', 'lca_config.yaml')

    config = load_config(config_path)

    # IMPORTANTE: También hay que arreglar las rutas relativas del YAML
    raw_homo_path = os.path.join(base_dir, config['paths']['raw_data_homo'])
    raw_hetero_path = os.path.join(base_dir, config['paths']['raw_data_hetero'])

    # Pasamos la ruta de resultados absoluta también
    config['paths']['results_dir'] = os.path.join(base_dir, config['paths']['results_dir'])

    # 1. Procesar Homogéneos
    print("Procesando matriz homogénea...")
    df_homo = clean_sima_pro_data(
        raw_homo_path,
        config['skip_rows']['homo'],
        config['target_categories']
    )
    plot_impact_comparison(df_homo, "Homogeneous_Comparison", config)

    # 2. Procesar Heterogéneos
    print("Procesando matriz heterogénea...")
    df_hetero = clean_sima_pro_data(
        raw_hetero_path,
        config['skip_rows']['hetero'],
        config['target_categories']
    )
    plot_impact_comparison(df_hetero, "Heterogeneous_Comparison", config)


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()