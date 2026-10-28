# scripts/scenario_comparison.py
import sys
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.processing import load_config, clean_sima_pro_data


def beautify_label(text):
    """Limpia el texto basura y aplica formato matemático para subíndices y superíndices."""
    text = str(text).replace('(del proyecto 00_TFM_Juanjo)', '').strip()
    text = re.sub(r'H2O2', r'H$_2$O$_2$', text)
    text = re.sub(r'Ga2O3', r'Ga$_2$O$_3$', text)
    text = re.sub(r'CO2', r'CO$_2$', text)
    text = re.sub(r'W/m2', r'W/m$^2$', text)
    return text


def plot_scenario_comparison(df, scenario_name, columns_to_compare, config):
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    valid_cols = [c for c in columns_to_compare if c in df.columns]
    if len(valid_cols) < 2:
        print(f"⚠️ Saltando '{scenario_name}': Faltan columnas. Buscadas: {columns_to_compare}")
        return

    df_scenario = df[valid_cols].copy()
    target_metrics = config.get('target_categories', [])
    df_plot = df_scenario.loc[df_scenario.index.isin(target_metrics)].apply(pd.to_numeric, errors='coerce').dropna(
        how='all')

    if df_plot.empty:
        return

    x = np.arange(len(df_plot.index))
    width = 0.8 / len(valid_cols)

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = plt.cm.tab10.colors

    for i, col in enumerate(valid_cols):
        offset = (i - len(valid_cols) / 2 + 0.5) * width
        label_name = beautify_label(col)
        ax.bar(x + offset, df_plot[col], width, label=label_name, color=colors[i % len(colors)], edgecolor='black',
               linewidth=0.8)

    ax.set_ylabel('Impact Value (Log Scale, Absolute Units)', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(df_plot.index, rotation=25, ha='right', fontweight='bold')
    ax.legend(title='Treatment Strategies', bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)

    ax.set_yscale('log')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)
    ax.tick_params(top=False, right=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    results_dir = config['paths']['results_dir']
    if not os.path.isabs(results_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results_dir = os.path.join(base_dir, results_dir)
    os.makedirs(results_dir, exist_ok=True)

    output_path = os.path.join(results_dir, f"Scenario_{scenario_name.replace(' ', '_')}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico guardado: {output_path}")


def get_dynamic_col(df, required_kws, exclude_kws=None):
    if exclude_kws is None: exclude_kws = []
    for col in df.columns:
        c_upper = str(col).upper()
        if all(kw.upper() in c_upper for kw in required_kws) and not any(ekw.upper() in c_upper for ekw in exclude_kws):
            return col
    return None


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

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

    # 1. Buscar Campeón Homogéneo
    if 'Climate change' in df_homo.index:
        col_homo_champ = df_homo.loc['Climate change'].apply(pd.to_numeric, errors='coerce').idxmin()
    else:
        col_homo_champ = df_homo.columns[0]

    # 2. Búsqueda de Heterogéneos (Permitiendo que tengan UV en el nombre)
        # Anclamos con fuerza bruta a la concentración de 0.5 mM
    col_laga_paa = get_dynamic_col(df_total, ['LAGA', '0,5 MM PAA'])
    # Cambiamos PS por PMS porque es lo que Juanjo ha corrido en SimaPro
    col_laga_pms = get_dynamic_col(df_total, ['LAGA', 'PMS'])
    col_laga_pure = get_dynamic_col(df_total, ['LAGA'], exclude_kws=['PAA', 'PS', 'PMS', 'H2O2'])
    col_ga2o3_pure = get_dynamic_col(df_total, ['GA2O3'], exclude_kws=['PAA', 'PS', 'PMS', 'H2O2'])

    # 3. Definición de escenarios 100% dinámicos
    scenarios = {
        "1_Homogeneous_Oxidants": list(df_homo.columns),
        "2_Catalyst_Base_Ga2O3_vs_LaGa": [c for c in [col_ga2o3_pure, col_laga_pure] if c is not None],
        # Metemos el PMS en el escenario 3
        "3_Heterogeneous_Intensification": [c for c in [col_laga_pure, col_laga_paa, col_laga_pms] if c is not None],
        "4_Final_Showdown": [c for c in [col_homo_champ, col_laga_paa] if c is not None]
    }

    for name, columns in scenarios.items():
        columns = list(dict.fromkeys(columns)) # Evitar duplicados
        plot_scenario_comparison(df_total, name, columns, config)

if __name__ == "__main__":
    main()