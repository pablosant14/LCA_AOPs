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

    print("Seleccionando los mejores procesos (Frontera de Pareto)...")
    # Separamos las familias para sacar los campeones
    df_homos = df_eco[df_eco['Type'] == 'Homo']
    df_heteros = df_eco[df_eco['Type'] == 'Hetero']

    mejores = []

    # Campeones Homogéneos (Mejor huella de carbono y mejor eficiencia energética)
    if not df_homos.empty:
        mejores.append(df_homos['GWP'].idxmin())
        mejores.append(df_homos['EEO_UVC'].idxmin())

    # Campeones Heterogéneos (Mejor huella de carbono y mejor eficiencia energética)
    if not df_heteros.empty:
        mejores.append(df_heteros['GWP'].idxmin())
        mejores.append(df_heteros['EEO_UVC'].idxmin())

    # Tratamiento de control (Siempre es bueno tener el referente)
    if 'UV-C/NaClO' in df_eco.index: mejores.append('UV-C/NaClO')
    if '2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PAA' in df_eco.index:
        mejores.append('2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PAA')

    # Limpiamos duplicados (por si el mejor en energía también es el mejor en huella)
    procesos_estrella = list(dict.fromkeys(mejores))

    print(f"🌟 Procesos seleccionados dinámicamente para la matriz: {procesos_estrella}")

    df_eco_final = df_eco[df_eco.index.isin(procesos_estrella)].copy()

    print("Dibujando el Cuadrante Mágico...")
    plot_ecoefficiency_matrix(df_eco_final, "EcoEfficiency_Matrix", config)


if __name__ == "__main__":
    main()