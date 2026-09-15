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
    '''Genera el gráfico de barras de inventario (ICV) de doble eje (Dual-Axis) de tesis, controlando el procesado dinámicamente dentro del plotter.'''
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # Limpiar los nombres de los experimentos (eje X)
    df.index = [format_chem_text(idx) for idx in df.index]

    # ========================================================
    # PROCESADO DINÁMICO DENTRO DEL PINTOR (para este plot específico)
    # ========================================================
    # 1. Aseguramos que 'Experimento' es el índice (asumiendo cargado con set_index en processing.py)

    # 2. Subsetear solo las columnas numéricas clave de inventario de recursos
    cols_plot = ['Electricidad Total (kWh/m3)', 'Masa Comercial (kg/m3)', 'Masa Cat. (kg/m3)']
    df_temp = df[cols_plot].copy()

    # 3. Orden estético: por consumo eléctrico de menor a mayor
    # FIX TURN 23: Columna Electricidad Total garantizada por el cargador genérico turn 23.
    df_sorted = df_temp.sort_values(by='Electricidad Total (kWh/m3)', ascending=True)

    # 4. head(top_n) dinámico para que el gráfico sea legible (eliminando la carallada del Turn 17 del loader)
    df_plot = df_sorted.head(top_n).copy()

    # ========================================================
    # PLOTTING con la matriz df_plot de campeones estéticos
    # ========================================================
    fig, ax1 = plt.subplots(figsize=(12, 6))
    x = np.arange(len(df_plot.index))
    width = 0.35

    # --- EJE IZQUIERDO (Electricidad kWh/m3) ---
    # Usamos la columna numérica bruta 'Electricidad Total (kWh/m3)'
    bar1 = ax1.bar(x - width / 2, df_plot['Electricidad Total (kWh/m3)'], width,
                   label='Electricity (kWh/m$^3$)', color='#1f77b4', edgecolor='black')

    ax1.set_ylabel('Total Electricity (kWh/m$^3$)', color='#1f77b4', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax1.set_xticks(x)
    # Etiquetas de texto de 'Experimento' (Índice de df_plot)
    ax1.set_xticklabels(df_plot.index, rotation=45, ha='right')

    # --- EJE DERECHO (Masas Químicas kg/m3) ---
    ax2 = ax1.twinx()

    # Masa de Reactivo Comercial (kg/m3)
    bar2 = ax2.bar(x + width / 2, df_plot['Masa Comercial (kg/m3)'], width,
                   label='Reagent Mass (kg/m$^3$)', color='#ff7f0e', edgecolor='black')
    # Masa de Catalizador (kg/m3) apilada encima del reactivo
    bar3 = ax2.bar(x + width / 2, df_plot['Masa Cat. (kg/m3)'], width,
                   bottom=df_plot['Masa Comercial (kg/m3)'],
                   label='Catalyst Mass (kg/m$^3$)', color='#8c564b', edgecolor='black')

    # ... ylabels, spines, ticks, legend logic same turn 17/22, save clean ...
    ax2.set_ylabel('Chemical Input Mass (kg/m$^3$)', color='#d62728', fontweight='bold')

    # Spines y Ticks logic dual axis de Turn 17/22 general generalization generalized generalized standardised dynamic standarized logic general generalization dynamic standardization standardized generalized logic generalization standardization.
    ax1.spines['top'].set_visible(True)
    ax1.spines['right'].set_visible(True)
    ax2.spines['top'].set_visible(True)
    ax2.spines['right'].set_visible(True)
    # spikes off logic standard general standardization
    ax1.tick_params(which='both', top=False, right=False, left=True, bottom=True)
    # dual ticks dynamic turn 17/22 logic
    ax2.tick_params(which='both', top=False, bottom=False, left=False, right=False, labelright=True)

    plt.title("Life Cycle Inventory: Energy vs Mass Inputs", fontweight='bold', pad=15)

    lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(1.10, 1))

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def plot_relative_contribution(df_pct, output_name, config):
    '''Genera el gráfico de barras apiladas al 100% (Contribution) disgregando energía de tesis Q1.'''
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    df_pct.index = [format_chem_text(idx) for idx in df_pct.index]

    fig, ax = plt.subplots(figsize=(9, 6))

    # 4 Colores Q1: UV-C (Azul oscuro), Agitación (Azul claro), Químicos (Naranja), Catalizador (Marrón)
    colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#8c564b']

    # Gráfico apilado (stacked=True) al 100%
    df_pct.plot(kind='bar', stacked=True, color=colors, ax=ax, edgecolor='black', width=0.6)

    ax.set_ylabel("Relative Input Contribution (%)", fontweight='bold')

    apply_thesis_style(ax)

    # Límite fijo al 100%
    ax.set_ylim(0, 100)

    plt.title("Disaggregated Resource Inventory Contribution", fontweight='bold', pad=15)
    plt.xticks(rotation=45, ha='right')

    # Leyenda fuera de la caja perimetral
    plt.legend(title="Input Phase", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gráfico de contribución disgregado al 100% guardado en: {output_path}")


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


def plot_radar_chart(df, output_name, config):
    '''Genera un gráfico de radar superponiendo los tratamientos cribados.'''
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    # 1. Normalización para que todas las métricas encajen en el radar (0 a 1)
    df_norm = df.div(df.max(axis=1), axis=0)

    # 2. Formateo de los nombres químicos
    df_norm.columns = [format_chem_text(c) for c in df_norm.columns]
    categories = df_norm.index.tolist()
    N = len(categories)

    if N < 3:
        print("Advertencia: El radar necesita al menos 3 categorías de impacto para dibujarse.")
        return

    # Calcular los ángulos de cada "radio" de la tela de araña
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Dibujar un eje por categoría y añadir las etiquetas
    plt.xticks(angles[:-1], categories, size=10, fontweight='bold')

    # Alinear las etiquetas para que no se pisen con el gráfico
    ax.tick_params(axis='x', pad=15)

    # Desactivar las etiquetas del eje Y (las concéntricas) para mayor limpieza
    ax.set_yticklabels([])

    # Dibujar cada tratamiento (columna) en el radar
    colors = plt.cm.tab10.colors  # Paleta categórica
    for i, col in enumerate(df_norm.columns):
        values = df_norm[col].tolist()
        values += values[:1]  # Cerrar el polígono

        ax.plot(angles, values, linewidth=2, linestyle='solid', label=col, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.1, color=colors[i % len(colors)])

    plt.title("Multicategory Impact Radar (Normalized)", size=14, fontweight='bold', y=1.1)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gráfico de radar guardado en: {output_path}")


def plot_breakeven_curve(df, output_name, config):
    '''Genera el gráfico de líneas del punto de equilibrio (Break-Even) del catalizador.'''
    plt.style.use(['science', 'no-latex'])
    plt.rcParams.update({"font.family": "Cambria", "font.size": 11, "mathtext.default": "regular"})

    fig, ax = plt.subplots(figsize=(9, 6))

    # Extraer datos
    x = df.index
    y_hetero = df['Hetero_LaGa_PAA']
    y_homo = df['Homo_NaClO_Baseline']

    # Dibujar las curvas
    ax.plot(x, y_hetero, marker='o', linewidth=2.5, color='#8c564b', label='UV-C/LaFeO$_3$-Ga$_2$O$_3$/PAA')
    ax.plot(x, y_homo, linestyle='--', linewidth=2.5, color='#1f77b4', label='UV-C/NaClO (Baseline)')

    # Buscar el punto de corte (Break-even point) matemáticamente
    # Es el primer ciclo donde el impacto heterogéneo baja del homogéneo
    corte_idx = df[df['Hetero_LaGa_PAA'] <= df['Homo_NaClO_Baseline']].index.min()

    if pd.notna(corte_idx):
        y_corte = df.loc[corte_idx, 'Hetero_LaGa_PAA']
        ax.plot(corte_idx, y_corte, marker='*', markersize=15, color='#d62728', zorder=5)
        ax.annotate(f'Break-Even:\nCycle {int(corte_idx)}',
                    xy=(corte_idx, y_corte), xytext=(corte_idx + 1, y_corte + 2),
                    arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                    fontsize=11, fontweight='bold', color='#d62728')

    # Formato de la Tesis
    apply_thesis_style(ax)

    ax.set_xlabel("Number of Catalyst Reuse Cycles", fontweight='bold')
    ax.set_ylabel(r"Global Warming Potential (kg CO$_2$ eq/m$^3$)", fontweight='bold')
    plt.title("Environmental Break-Even Analysis (Catalyst Amortization)", fontweight='bold', pad=15)

    # Forzar que el eje X muestre números enteros
    ax.set_xticks(np.arange(1, 16, 2))

    plt.legend(loc='upper right')

    plt.tight_layout()
    output_path = os.path.join(config['paths']['results_dir'], f"{output_name}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Gráfico de Break-Even guardado en: {output_path}")