# scripts/analyze_breakeven.py
import sys
import os
import re
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.processing import load_config, clean_sima_pro_data
from src.plotting import apply_thesis_style


def beautify_label(text):
    """Limpia el texto basura y aplica formato matemático para subíndices y superíndices."""
    text = str(text).replace('(del proyecto 00_TFM_Juanjo)', '').strip()
    text = re.sub(r'H2O2', r'H$_2$O$_2$', text)
    text = re.sub(r'Ga2O3', r'Ga$_2$O$_3$', text)
    text = re.sub(r'CO2', r'CO$_2$', text)
    text = re.sub(r'W/m2', r'W/m$^2$', text)
    return text


def get_dynamic_column(df, required_kws, exclude_kws=None):
    """Busca columnas por palabras clave para el heterogéneo y el polvo."""
    if exclude_kws is None: exclude_kws = []
    for col in df.columns:
        c_upper = str(col).upper()
        if all(kw.upper() in c_upper for kw in required_kws) and not any(ekw.upper() in c_upper for ekw in exclude_kws):
            return col
    raise ValueError(f"No se encontró columna para kws={required_kws}")


def calculate_dynamic_breakeven(df, col_homo, col_hetero, col_powder, cycles=10):
    """Calcula el impacto diluido del reuso del catalizador en N ciclos."""
    for col in [col_homo, col_hetero, col_powder]:
        if col not in df.columns:
            raise ValueError(f"🚨 Error: La columna '{col}' no se encuentra en la matriz unificada.")

    impact_homo = df[col_homo].apply(pd.to_numeric, errors='coerce')
    impact_hetero_op = df[col_hetero].apply(pd.to_numeric, errors='coerce')
    impact_powder = df[col_powder].apply(pd.to_numeric, errors='coerce')

    results = []
    for n in range(1, cycles + 1):
        current_hetero = impact_hetero_op + (impact_powder / n)
        for cat in df.index:
            results.append({
                'Category': cat, 'Cycle': n,
                'System': 'Homogeneous_Champion', 'Impact': impact_homo[cat],
                'Label_Homo': col_homo, 'Label_Hetero': col_hetero
            })
            results.append({
                'Category': cat, 'Cycle': n,
                'System': 'Heterogeneous_Target', 'Impact': current_hetero[cat],
                'Label_Homo': col_homo, 'Label_Hetero': col_hetero
            })
    return pd.DataFrame(results)


def plot_dynamic_breakeven(df_breakeven, filename, config):
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    categories = df_breakeven['Category'].unique()
    num_cats = len(categories)
    cols = 3
    rows = (num_cats + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten()

    for i, cat in enumerate(categories):
        ax = axes[i]
        df_cat = df_breakeven[df_breakeven['Category'] == cat]

        df_homo = df_cat[df_cat['System'] == 'Homogeneous_Champion']
        df_het = df_cat[df_cat['System'] == 'Heterogeneous_Target']

        # Usamos los nombres embellecidos para la leyenda
        nombre_homo = beautify_label(df_homo['Label_Homo'].iloc[0])
        nombre_het = beautify_label(df_het['Label_Hetero'].iloc[0])

        label_homo = f"Best Homogeneous\n({nombre_homo})"
        label_het = f"Best Heterogeneous\n({nombre_het})"

        ax.plot(df_homo['Cycle'], df_homo['Impact'], label=label_homo, color='#1f77b4', linestyle='--', linewidth=2)
        ax.plot(df_het['Cycle'], df_het['Impact'], label=label_het, color='#ff7f0e', marker='o', markersize=5,
                linewidth=2)

        ax.set_title(cat, fontweight='bold', fontsize=12)
        ax.set_xlabel('Number of Reuse Cycles', fontweight='bold')
        ax.set_ylabel('Impact Value', fontweight='bold')
        ax.set_xticks(df_breakeven['Cycle'].unique())

        # Eliminamos la cuadrícula de fondo
        ax.grid(False)

        # Eliminamos los ticks superiores y derechos mediante la regla de la tesis
        try:
            apply_thesis_style(ax)
        except NameError:
            ax.tick_params(which='both', top=False, right=False, left=True, bottom=True)

        # Leyenda activada para todos los subgráficos
        ax.legend(frameon=True, loc='best', fontsize=9)

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()

    results_dir = config['paths']['results_dir']
    if not os.path.isabs(results_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results_dir = os.path.join(base_dir, results_dir)
    os.makedirs(results_dir, exist_ok=True)

    out_path = os.path.join(results_dir, f"{filename}.png")
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico de Break-Even guardado en: {out_path}")


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

    print("Cargando matrices de SimaPro...")
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

    print("Buscando dinámicamente los contendientes...")

    if 'Climate change' in df_homo.index:
        cc_impacts = df_homo.loc['Climate change'].apply(pd.to_numeric, errors='coerce')
        col_homo = cc_impacts.idxmin()
        print(f"  -> Campeón Homogéneo detectado: {col_homo}")
    else:
        raise ValueError("No se encuentra 'Climate change' en la matriz para determinar el campeón.")

    col_hetero = get_dynamic_column(df_total, ['LAGA', '0,5 MM PAA'])
    print(f"  -> Sistema Heterogéneo detectado: {col_hetero}")

    col_powder = get_dynamic_column(df_total, ['LAGA'], exclude_kws=['PAA', 'PS', 'PMS', 'H2O2'])
    print(f"  -> Polvo de catalizador detectado: {col_powder}")

    print("Calculando amortización del catalizador...")
    df_breakeven = calculate_dynamic_breakeven(df_total, col_homo, col_hetero, col_powder, cycles=10)

    print("Generando gráfico de Break-Even...")
    plot_dynamic_breakeven(df_breakeven, "BreakEven_Analysis", config)


if __name__ == "__main__":
    main()