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
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    target_metrics = config.get('target_categories', [])
    df_plot = df_scenario.loc[df_scenario.index.isin(target_metrics)].apply(pd.to_numeric, errors='coerce').dropna(
        how='all')

    if df_plot.empty:
        print("⚠️ No hay datos válidos para plotear en el radar.")
        return

    # Normalización al máximo de cada categoría (0 a 1)
    df_norm = df_plot.div(df_plot.max(axis=1), axis=0)

    categories = list(df_norm.index)
    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

    # Colores fijos para que encajen con tu matriz
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    plotted_any = False
    for i, col in enumerate(valid_cols):
        if col not in df_norm.columns: continue
        values = df_norm[col].values.flatten().tolist()
        values += values[:1]

        # Le aplicamos tu embellecedor matemático
        label_name = beautify_label(col)

        ax.plot(angles, values, linewidth=2, linestyle='solid', label=label_name, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.15)
        plotted_any = True

    if not plotted_any:
        print("⚠️ No se graficó nada en el radar porque no se encontraron las columnas.")
        return

    # Ajustes estéticos del Polígono
    plt.xticks(angles[:-1], categories, fontweight='bold', size=11)
    ax.tick_params(axis='x', pad=25)
    ax.set_rlabel_position(30)

    # Líneas de graduación grises
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "Max"], color="grey", size=9)
    plt.ylim(0, 1.05)

    # Leyenda limpia fuera del radar
    ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), frameon=False, title='Treatment Strategies')

    # Quitamos el borde redondo exterior feo para que quede profesional
    ax.spines['polar'].set_visible(False)

    plt.title("Environmental Impact Profile (Normalized)", fontweight='bold', pad=30)

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

    print("Cargando matrices de SimaPro para el Radar...")
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

    # =========================================================================
    # SELECCIÓN IDÉNTICA A LA MATRIZ DE ECOEFICIENCIA
    # =========================================================================
    print("Buscando dinámicamente a los Campeones del ACV...")

    # 1. El Campeón Homogéneo (PMS)
    col_pms = get_dynamic_column(df_total, ['PMS'])

    # 2. El Homogéneo Mítico (H2O2 para comparar como referente histórico)
    col_h2o2 = get_dynamic_column(df_total, ['H2O2'])

    # 3. Tu Sistema Estrella (LaGa + 0.5 mM PAA)
    col_laga_paa = get_dynamic_column(df_total, ['LAGA', '0,5 MM PAA'])

    # Creamos la lista eliminando cualquier nulo por si fallara la lectura
    valid_cols = [c for c in [col_pms, col_h2o2, col_laga_paa] if c is not None]

    if len(valid_cols) < 2:
        print("❌ Error: Faltan tratamientos para generar una comparativa en el radar.")
        return

    print(f"Generando Gráfico de Radar con: {valid_cols}")
    df_cribado = df_total[valid_cols].copy()

    plot_radar_chart(df_cribado, "EDA_Radar_Chart_Champions", valid_cols, config)


if __name__ == "__main__":
    main()