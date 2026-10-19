# scripts/exploratory_lca.py
import sys
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.processing import load_config, clean_sima_pro_data


def beautify_label(text):
    """Limpia el texto basura y aplica formato matemático para subíndices y superíndices."""
    text = text.replace('(del proyecto 00_TFM_Juanjo)', '').strip()
    text = re.sub(r'H2O2', r'H$_2$O$_2$', text)
    text = re.sub(r'Ga2O3', r'Ga$_2$O$_3$', text)
    text = re.sub(r'CO2', r'CO$_2$', text)
    text = re.sub(r'W/m2', r'W/m$^2$', text)
    return text


def plot_radar_chart(df_scenario, scenario_name, valid_cols, config):
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    target_metrics = config.get('target_categories', [])
    df_plot = df_scenario.loc[df_scenario.index.isin(target_metrics)].apply(pd.to_numeric, errors='coerce').dropna(
        how='all')

    # NORMALIZACIÓN (de 0 a 1 respecto al máximo de cada categoría)
    df_norm = df_plot.div(df_plot.max(axis=1), axis=0)

    categories = list(df_norm.index)
    N = len(categories)

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    # Lienzo ancho para que quepa la leyenda a la derecha
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

    colors = plt.cm.tab10.colors
    for i, col in enumerate(valid_cols):
        if col not in df_norm.columns:
            continue
        values = df_norm[col].values.flatten().tolist()
        values += values[:1]

        label_name = beautify_label(col)

        ax.plot(angles, values, linewidth=2, linestyle='solid', label=label_name, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.15)

    # FORMATO DE EJES Y ETIQUETAS
    plt.xticks(angles[:-1], categories, fontweight='bold', size=11)

    # Separamos las etiquetas del polígono para que no se superpongan
    ax.tick_params(axis='x', pad=25)

    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "Max"], color="grey", size=9)
    plt.ylim(0, 1.05)

    # LEYENDA TOTALMENTE FUERA DEL GRÁFICO
    ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), frameon=True, title='Treatment Strategies')

    # Limpiamos el borde exterior polar
    ax.spines['polar'].set_visible(False)

    plt.tight_layout()

    results_dir = config['paths']['results_dir']
    if not os.path.isabs(results_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results_dir = os.path.join(base_dir, results_dir)
    os.makedirs(results_dir, exist_ok=True)

    output_path = os.path.join(results_dir, f"{scenario_name.replace(' ', '_')}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico de Radar guardado: {output_path}")


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

    print("Cargando matrices de SimaPro para Exploratory Data Analysis (EDA)...")
    df_homo = clean_sima_pro_data(
        os.path.join(base_dir, config['paths']['raw_data_homo']),
        config['skip_rows']['homo'],
        config['target_categories']
    )
    df_hetero = clean_sima_pro_data(
        os.path.join(base_dir, config['paths']['raw_data_hetero']),
        config['skip_rows']['hetero'],
        config['target_categories']
    )

    df_total = pd.concat([df_homo, df_hetero], axis=1)
    df_total = df_total.loc[:, ~df_total.columns.duplicated()]

    # Seleccionamos los pesos pesados para el radar (ajusta esta lista si quieres ver otros)
    columnas_cribado = [
        "[HOM] NaClO 0,75mM - Philips 15W",
        "0,5 g/L LaGa",
        "2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA"
    ]

    valid_cols = [c for c in columnas_cribado if c in df_total.columns]
    df_cribado = df_total[valid_cols].copy()

    print("Generando Gráfico de Radar cribado...")
    # Llamada corregida con los 4 parámetros (incluyendo valid_cols)
    plot_radar_chart(df_cribado, "EDA_Radar_Chart_Filtered", valid_cols, config)


if __name__ == "__main__":
    main()