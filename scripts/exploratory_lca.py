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
    text = str(text).replace('(del proyecto 00_TFM_Juanjo)', '').strip()
    text = re.sub(r'H2O2', r'H$_2$O$_2$', text)
    text = re.sub(r'Ga2O3', r'Ga$_2$O$_3$', text)
    text = re.sub(r'CO2', r'CO$_2$', text)
    text = re.sub(r'W/m2', r'W/m$^2$', text)
    return text


def get_dynamic_column(df, required_kws, exclude_kws=None):
    if exclude_kws is None: exclude_kws = []
    for col in df.columns:
        c_upper = str(col).upper()
        if all(kw.upper() in c_upper for kw in required_kws) and not any(ekw.upper() in c_upper for ekw in exclude_kws):
            return col
    return None


def plot_radar_chart(df_scenario, scenario_name, valid_cols, config):
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    target_metrics = config.get('target_categories', [])
    df_plot = df_scenario.loc[df_scenario.index.isin(target_metrics)].apply(pd.to_numeric, errors='coerce').dropna(
        how='all')

    if df_plot.empty:
        print("⚠️ No hay datos válidos para plotear en el radar.")
        return

    df_norm = df_plot.div(df_plot.max(axis=1), axis=0)

    categories = list(df_norm.index)
    N = len(categories)
    # Fix del syntax error de la multiplicación de Pi
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
    colors = plt.cm.tab10.colors

    plotted_any = False
    for i, col in enumerate(valid_cols):
        if col not in df_norm.columns: continue
        values = df_norm[col].values.flatten().tolist()
        values += values[:1]
        label_name = beautify_label(col)
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=label_name, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.15)
        plotted_any = True

    if not plotted_any:
        print("⚠️ No se graficó nada en el radar porque no se encontraron las columnas.")
        return

    plt.xticks(angles[:-1], categories, fontweight='bold', size=11)
    ax.tick_params(axis='x', pad=25)
    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "Max"], color="grey", size=9)
    plt.ylim(0, 1.05)
    ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), frameon=True, title='Treatment Strategies')
    ax.spines['polar'].set_visible(False)
    plt.tight_layout()

    results_dir = config['paths']['results_dir']
    if not os.path.isabs(results_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results_dir = os.path.join(base_dir, results_dir)
    os.makedirs(results_dir, exist_ok=True)

    out_path = os.path.join(results_dir, f"{scenario_name.replace(' ', '_')}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico de Radar guardado en: {out_path}")


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

    print("Cargando matrices de SimaPro para Exploratory Data Analysis (EDA)...")
    df_homo = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_homo']), config['skip_rows']['homo'],
                                  config['target_categories'])
    df_hetero = clean_sima_pro_data(os.path.join(base_dir, config['paths']['raw_data_hetero']),
                                    config['skip_rows']['hetero'], config['target_categories'])

    df_total = pd.concat([df_homo, df_hetero], axis=1)
    df_total = df_total.loc[:, ~df_total.columns.duplicated()]

    print("Buscando dinámicamente las columnas para el radar...")
    # 1. Buscamos el Campeón Homogéneo absoluto
    if 'Climate change' in df_homo.index:
        col_homo = df_homo.loc['Climate change'].apply(pd.to_numeric, errors='coerce').idxmin()
    else:
        col_homo = get_dynamic_column(df_total, ['NACL'])

    # 2. Buscamos el Polvo puro (soportando que haya mezclado la luz UV)
    col_powder = get_dynamic_column(df_total, ['LAGA'], exclude_kws=['PAA', 'PS', 'PMS', 'H2O2'])

    # 3. Buscamos tu tratamiento completo anclando el 0.5 mM PAA
    col_hetero = get_dynamic_column(df_total, ['LAGA', '0,5 MM PAA'])

    valid_cols = [c for c in [col_homo, col_powder, col_hetero] if c is not None]

    if not valid_cols:
        print("❌ Error: No se encontraron los tratamientos para el radar.")
        return

    print(f"Generando Gráfico de Radar con: {valid_cols}")
    df_cribado = df_total[valid_cols].copy()
    plot_radar_chart(df_cribado, "EDA_Radar_Chart_Filtered", valid_cols, config)


if __name__ == "__main__":
    main()