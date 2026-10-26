# src/plotting.py
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import \
    scienceplots  # ¡ESTE ES EL IMPORT FUNDAMENTAL! Tiene que estar aquí para cargar el estilo 'science' de matplotlib


def format_chem_text(text):
    '''Detecta fórmulas y unidades químicas (H2O2, Ga2O3...) y les aplica el formato mathtext de matplotlib sin cursiva matemática fea.'''
    if not isinstance(text, str):
        return text

    replacements = {
        "H2O2": "H$_2$O$_2$",
        "Ga2O3": "Ga$_2$O$_3$",
        "LaFeO3": "LaFeO$_3$",
        "W/m2": "W/m$^2$",
        "m3": "m$^3$",
        "CO2": "CO$_2$"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def apply_thesis_style(ax):
    '''Aplica la regla estricta de la tesis para los ejes de un gráfico: caja cerrada pero ticks (rayitas) SOLO abajo y a la izquierda.'''
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)
    # Desactivamos los ticks superiores y derechos (major y minor ticks con which='both')
    ax.tick_params(which='both', top=False, right=False, left=True, bottom=True)


def plot_impact_comparison(df, output_name, config):
    '''Genera el gráfico de barras comparativo de impacto ambiental bruto (SimaPro) de tesis.'''
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # Saca la columna de unidades (se asume cargada con skiprows)
    if 'Unidad' in df.columns:
        df_plot = df.drop(columns=['Unidad']).T
    else:
        df_plot = df.T

    # Limpiamos los nombres de los tratamientos en el eje X con formato matemático
    df_plot.index = [format_chem_text(idx) for idx in df_plot.index]

    fig, ax = plt.subplots(figsize=(10, 6))
    df_plot.plot(kind='bar', ax=ax, edgecolor='black', width=0.8)

    # Aplicar formato tesis Q1
    apply_thesis_style(ax)

    plt.title(f"LCA Impact Comparison - {output_name}", fontweight='bold', pad=15)
    plt.ylabel("Impact Value")

    # Rotamos a 45 grados y alineamos a la derecha para textos largos
    plt.xticks(rotation=45, ha='right')
    # Leyenda fuera de la caja
    plt.legend(title="Impact Category", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_icv_dual_axis(df, output_name, config, top_n=12):
    '''Genera dos gráficos de barras de inventario (ICV) de doble eje (Dual-Axis) de tesis: Homo y Hetero.'''
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # =========================================================================
    # TÍTULOS HARDCODEABLES (Editables a tu gusto. Usa \n para saltar de línea)
    # =========================================================================
    titulo_homo = "A) Life Cycle Inventory: Energy vs Mass Inputs"
    titulo_hetero = "Life Cycle Inventory: Energy vs Mass Inputs"

    # Limpiar los nombres de los experimentos (eje X) de forma dinámica
    df_clean = df.copy()
    df_clean.index = [format_chem_text(str(idx)) for idx in df_clean.index]

    # Dividir universos: Homo vs Hetero (Usamos Equipo Asignado o Masa de Catalizador como plan B)
    if 'Equipo Asignado' in df_clean.columns:
        df_clean['Equipo Asignado'] = df_clean['Equipo Asignado'].fillna('')
        df_homo = df_clean[df_clean['Equipo Asignado'].str.contains('Philips', case=False)].copy()
        df_hetero = df_clean[df_clean['Equipo Asignado'].str.contains('Apria|LED', case=False)].copy()
    else:
        # Fallback brutal si falta la columna equipo en el Excel
        if 'Masa Cat. (kg/m3)' in df_clean.columns:
            df_homo = df_clean[df_clean['Masa Cat. (kg/m3)'] == 0].copy()
            df_hetero = df_clean[df_clean['Masa Cat. (kg/m3)'] > 0].copy()
        else:
            df_homo = df_clean.copy()
            df_hetero = pd.DataFrame()

    def _draw_plot(df_subset, suffix, is_hetero, custom_title):
        """Subfunción interna para fabricar el gráfico dependiendo del universo."""
        if df_subset.empty:
            return

        # Definimos las columnas base
        cols_plot = ['Electricidad Total (kWh/m3)', 'Masa Comercial (kg/m3)']
        if is_hetero and 'Masa Cat. (kg/m3)' in df_subset.columns:
            cols_plot.append('Masa Cat. (kg/m3)')

        # 1. FILTRO ANTI-FANTASMAS
        df_temp = df_subset[cols_plot].apply(pd.to_numeric, errors='coerce').fillna(0)
        df_temp = df_temp.loc[(df_temp > 0).any(axis=1)]

        if df_temp.empty:
            return

        # 2. Orden estético: por consumo eléctrico de menor a mayor
        df_sorted = df_temp.sort_values(by='Electricidad Total (kWh/m3)', ascending=True)

        # 3. head(top_n) dinámico
        df_plot = df_sorted.head(top_n).copy()

        fig, ax1 = plt.subplots(figsize=(10, 6))
        x = np.arange(len(df_plot.index))
        width = 0.35

        # --- EJE IZQUIERDO (Electricidad kWh/m3) ---
        bar1 = ax1.bar(x - width / 2, df_plot['Electricidad Total (kWh/m3)'], width,
                       label='Electricity (kWh/m$^3$)', color='#1f77b4', edgecolor='black')

        ax1.set_ylabel('Total Electricity (kWh/m$^3$)', color='#1f77b4', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#1f77b4')
        ax1.set_xticks(x)

        # Dinamismo absoluto de nombres: Toma el index de df_plot que viene del Excel de Juanjo
        ax1.set_xticklabels(df_plot.index, rotation=45, ha='right')

        # --- EJE DERECHO (Masas Químicas kg/m3) ---
        ax2 = ax1.twinx()

        # Masa de Reactivo Comercial (kg/m3)
        bar2 = ax2.bar(x + width / 2, df_plot['Masa Comercial (kg/m3)'], width,
                       label='Reagent Mass (kg/m$^3$)', color='#ff7f0e', edgecolor='black')

        # Masa de Catalizador (kg/m3) SOLO se renderiza y añade a la leyenda para Heterogéneos
        if is_hetero and 'Masa Cat. (kg/m3)' in cols_plot:
            bar3 = ax2.bar(x + width / 2, df_plot['Masa Cat. (kg/m3)'], width,
                           bottom=df_plot['Masa Comercial (kg/m3)'],
                           label='Catalyst Mass (kg/m$^3$)', color='#8c564b', edgecolor='black')

        ax2.set_ylabel('Chemical Input Mass (kg/m$^3$)', color='#d62728', fontweight='bold')

        # Spines logic dual axis
        ax1.spines['top'].set_visible(True)
        ax1.spines['right'].set_visible(True)
        ax2.spines['top'].set_visible(True)
        ax2.spines['right'].set_visible(True)

        # Reglas tesis UPM
        try:
            apply_thesis_style(ax1)
        except NameError:
            ax1.tick_params(which='both', top=False, right=False, left=True, bottom=True)

        # Eje secundario (derecho): EXCEPCIÓN A LA REGLA -> right=True para ver las marcas
        ax2.tick_params(which='both', top=False, bottom=False, left=False, right=True, labelright=True)

        # Usamos la variable inyectada para el título
        plt.title(custom_title, fontweight='bold', pad=15)

        # Unificación matemática de leyendas (solo capturará lo que realmente se haya dibujado)
        lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
        lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
        ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(1.10, 1))

        plt.tight_layout()

        results_dir = config['paths']['results_dir']
        if not os.path.isabs(results_dir):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            results_dir = os.path.join(base_dir, results_dir)
        os.makedirs(results_dir, exist_ok=True)

        output_path = os.path.join(results_dir, f"{output_name}_{suffix}.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Gráfico ICV guardado: {output_path}")

    # Ejecutamos el motor inyectando los títulos respectivos
    _draw_plot(df_homo, "Homogeneous", is_hetero=False, custom_title=titulo_homo)
    _draw_plot(df_hetero, "Heterogeneous", is_hetero=True, custom_title=titulo_hetero)


def plot_relative_contribution(df_pct, output_name, config):
    '''Genera el gráfico de barras apiladas al 100% (Contribution) disgregando energía de tesis Q1.'''
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # =========================================================================
    # TÍTULOS HARDCODEABLES (Editables a tu gusto. Usa \n para saltar de línea)
    # =========================================================================
    if "Homogeneous" in output_name:
        custom_title = "(B) Disaggregated relative contribution of input phases (electricity vs. chemical reagents) for the homogeneous systems"
    elif "Heterogeneous" in output_name:
        custom_title = ""
    else:
        custom_title = "Disaggregated Resource Inventory Contribution\n(All Processes)"

    # Limpiamos nombres del eje X
    df_clean = df_pct.copy()
    df_clean.index = [format_chem_text(str(idx)) for idx in df_clean.index]

    # ========================================================
    # 1. PURGA DINÁMICA DE FANTASMAS (Elimina Catalizador si es 0%)
    # ========================================================
    # Solo conservamos las columnas que aporten algo (>0) al sistema
    df_plot = df_clean.loc[:, (df_clean > 0).any(axis=0)]

    # ========================================================
    # 2. CANDADO DE COLORES
    # ========================================================
    color_map = {
        'Electricity (UV-C)': '#1f77b4',  # Azul oscuro
        'Electricity (Stirring)': '#aec7e8',  # Azul claro
        'Chemical Reagents': '#ff7f0e',  # Naranja
        'Catalyst': '#8c564b'  # Marrón
    }

    # Mapeamos los colores exclusivamente para las columnas que han sobrevivido
    plot_colors = [color_map.get(col, '#333333') for col in df_plot.columns]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Gráfico apilado (stacked=True) al 100%
    df_plot.plot(kind='bar', stacked=True, color=plot_colors, ax=ax, edgecolor='black', width=0.6)

    ax.set_ylabel("Relative Input Contribution (%)", fontweight='bold')

    # Aplicar estilo cerrado de la tesis
    try:
        apply_thesis_style(ax)
    except NameError:
        ax.tick_params(which='both', top=False, right=False, left=True, bottom=True)

    # Límite fijo al 100%
    ax.set_ylim(0, 100)

    # Usamos el título hardcodeado desde arriba
    plt.title(custom_title, fontweight='bold', pad=15)

    plt.xticks(rotation=45, ha='right')

    # Leyenda fuera de la caja perimetral
    plt.legend(title="Input Phase", bbox_to_anchor=(1.05, 1), loc='upper left', frameon=True)

    plt.tight_layout()

    results_dir = config['paths']['results_dir']
    if not os.path.isabs(results_dir):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        results_dir = os.path.join(base_dir, results_dir)
    os.makedirs(results_dir, exist_ok=True)

    output_path = os.path.join(results_dir, f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Gráfico de contribución guardado en: {output_path}")

# Añadir al final de src/plotting.py

def plot_ecoefficiency_matrix(df, output_name, config):
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    fig, ax = plt.subplots(figsize=(8, 8))

    # Dibujar los puntos (scatter)
    ax.scatter(df['EEO_UVC'], df['GWP'], color='#1f77b4', s=100, edgecolor='black', zorder=3)

    # ========================================================
    # DIBUJAR LOS CUADRANTES (Líneas de la Mediana)
    # ========================================================
    median_eeo = df['EEO_UVC'].median()
    median_gwp = df['GWP'].median()

    ax.axvline(median_eeo, color='gray', linestyle='--', alpha=0.7, zorder=1)
    ax.axhline(median_gwp, color='gray', linestyle='--', alpha=0.7, zorder=1)

    # Colorear sutilmente el "Cuadrante Mágico" (Inferior Izquierdo)
    ax.axvspan(ax.get_xlim()[0], median_eeo, ymin=0,
               ymax=(median_gwp - ax.get_ylim()[0]) / (ax.get_ylim()[1] - ax.get_ylim()[0]),
               color='#2ca02c', alpha=0.1, zorder=0)

    # Añadir las etiquetas a los puntos (formateadas químicamente)
    for idx, row in df.iterrows():
        label = format_chem_text(idx)
        ax.annotate(label, (row['EEO_UVC'], row['GWP']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=10, fontweight='bold', zorder=4)

    ax.set_xlabel(r"Photocatalytic E$_{EO}$ (kWh/m$^3$$\cdot$order)", fontweight='bold')
    ax.set_ylabel(r"Global Warming Potential (kg CO$_2$ eq)", fontweight='bold')

    # Reglas de la Tesis
    apply_thesis_style(ax)

    plt.title("Eco-efficiency Matrix: Energy vs. Climate Impact", fontweight='bold', pad=15)

    # Anotaciones de cuadrante
    ax.text(0.05, 0.05, "Ideal Region\n(Fast & Green)", transform=ax.transAxes,
            fontsize=12, color='#2ca02c', fontweight='bold', alpha=0.5)

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Matriz de Ecoeficiencia guardada en: {output_path}")


# Añadir al final de src/plotting.py
import seaborn as sns


def plot_impact_heatmap(df, output_name, config):
    '''Genera un mapa de calor normalizado para identificar cuellos de botella ambientales.'''
    # Asegurar que el entorno gráfico es limpio
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # 1. Limpieza: Asegurar que todo es numérico (a veces SimaPro exporta texto oculto)
    df_numeric = df.apply(pd.to_numeric, errors='coerce').dropna(how='all', axis=1)

    # 2. Filtro: Seleccionar solo las categorías diana del lca_config.yaml
    target_cats = config.get('target_categories', df_numeric.index.tolist())
    df_plot = df_numeric[df_numeric.index.isin(target_cats)].copy()

    # 3. Normalización: Dividimos cada valor de la fila por el máximo de esa fila (escala 0-100%)
    df_norm = df_plot.div(df_plot.max(axis=1), axis=0) * 100

    # 4. Formatear nombres químicos para el eje X
    df_norm.columns = [format_chem_text(c) for c in df_norm.columns]

    fig, ax = plt.subplots(figsize=(14, 8))

    # Dibujar el Heatmap con paleta roja (mayor intensidad = peor impacto)
    sns.heatmap(df_norm, cmap='Reds', annot=False, linewidths=.5, ax=ax,
                cbar_kws={'label': 'Relative Environmental Impact (%)'})

    plt.title("Normalized Environmental Impact Heatmap", fontweight='bold', pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Impact Category", fontweight='bold')

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap de exploración guardado en: {output_path}")


# Añadir a src/plotting.py (y pon 'from math import pi' en los imports de arriba si no lo tienes)
from math import pi

import numpy as np
import matplotlib.pyplot as plt
from math import pi

import numpy as np
import matplotlib.pyplot as plt
import os
from math import pi


def plot_radar_chart(df_scenario, scenario_name, valid_cols, config):
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    target_metrics = config.get('target_categories', [])
    df_plot = df_scenario.loc[df_scenario.index.isin(target_metrics)].apply(pd.to_numeric, errors='coerce').dropna(
        how='all')

    # NORMALIZACIÓN (de 0 a 1 respecto al máximo)
    df_norm = df_plot.div(df_plot.max(axis=1), axis=0)

    categories = list(df_norm.index)
    N = len(categories)

    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    # Aumentamos el ancho (10, 8) para dejar sitio a la leyenda a la derecha
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))

    colors = plt.cm.tab10.colors
    for i, col in enumerate(valid_cols):
        values = df_norm[col].values.flatten().tolist()
        values += values[:1]

        label_name = beautify_label(col)  # Aplica tu función de embellecimiento

        ax.plot(angles, values, linewidth=2, linestyle='solid', label=label_name, color=colors[i % len(colors)])
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.15)

    # FORMATO DE EJES (Sin títulos)
    plt.xticks(angles[:-1], categories, fontweight='bold', size=11)

    # ⚠️ LA MAGIA ESTÁ AQUÍ: Aleja el texto (Climate change, etc.) del polígono
    ax.tick_params(axis='x', pad=25)

    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "Max"], color="grey", size=9)
    plt.ylim(0, 1.05)

    # ⚠️ LEYENDA A SALVO: Desplazada totalmente a la derecha y centrada verticalmente
    ax.legend(loc='center left', bbox_to_anchor=(1.15, 0.5), frameon=True, title='Treatment Strategies')

    # Quitamos la línea de contorno exterior para que quede más moderno
    ax.spines['polar'].set_visible(False)

    plt.tight_layout()

    output_path = os.path.join(config['paths']['results_dir'], f"Radar_{scenario_name.replace(' ', '_')}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')  # El tight es clave para no recortar la leyenda
    plt.close()

def plot_breakeven_curve(df_breakeven, filename, config):
    plt.style.use('default')
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    categories = df_breakeven['Category'].unique()
    num_cats = len(categories)

    # Crear un grid de gráficos (2 filas, 3 columnas máximo para nuestras 5 categorías)
    cols = 3
    rows = (num_cats + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
    axes = axes.flatten()

    for i, cat in enumerate(categories):
        ax = axes[i]
        df_cat = df_breakeven[df_breakeven['Category'] == cat]

        # Filtrar datos de cada sistema
        df_homo = df_cat[df_cat['System'].str.contains('Homogeneous')]
        df_het = df_cat[df_cat['System'].str.contains('Heterogeneous')]

        # Pintar línea recta del homogéneo y la curva del heterogéneo
        ax.plot(df_homo['Cycle'], df_homo['Impact'], label='Homogeneous (NaClO)',
                color='#1f77b4', linestyle='--', linewidth=2)
        ax.plot(df_het['Cycle'], df_het['Impact'], label='Heterogeneous (LaGa + PAA)',
                color='#ff7f0e', marker='o', markersize=5, linewidth=2)

        ax.set_title(cat, fontweight='bold', fontsize=12)
        ax.set_xlabel('Number of Reuse Cycles', fontweight='bold')
        ax.set_ylabel('Impact Value', fontweight='bold')
        ax.set_xticks(df_breakeven['Cycle'].unique())
        ax.grid(True, linestyle='--', alpha=0.5)

        # Leyenda solo en el primer gráfico para no saturar
        if i == 0:
            ax.legend(frameon=True, loc='best')

    # Ocultar los subgráficos vacíos si sobran (ej. si son 5 categorías y 6 huecos)
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