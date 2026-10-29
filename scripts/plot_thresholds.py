import numpy as np
import matplotlib.pyplot as plt
import os

def plot_threshold_analysis():
    try:
        # Se prioriza el estilo Science (ideal para publicaciones)
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    # Ajustes estéticos para la tesis/Q1
    plt.rcParams.update({
        "font.family": "Cambria",
        "font.size": 12,
        "mathtext.default": "regular"
    })

    # Datos extraídos del texto
    gwp_static_homo = 0.000007
    gwp_rate_homo = 0.0000507
    gwp_hetero_total = 0.00270

    t_actual = 2.62
    t_crit = (gwp_hetero_total - gwp_static_homo) / gwp_rate_homo  # ~ 53.116 min

    t = np.linspace(0, 65, 500)
    gwp_homo = gwp_static_homo + gwp_rate_homo * t

    fig, ax = plt.subplots(figsize=(9, 6))

    # 1. Línea Homogénea (Acumulación dinámica)
    ax.plot(t, gwp_homo, label='Homogeneous (UV-C/PMS) Dynamic Footprint', color='#1f77b4', linewidth=2.5)

    # 2. Línea Heterogénea (Techo fijo por el coste del catalizador)
    ax.axhline(y=gwp_hetero_total, color='#ff7f0e', linestyle='--', linewidth=2.5,
               label='Heterogeneous (LaGa/UV-C/PAA) Single Cycle Total')

    # 3. Punto de intersección (Threshold)
    ax.plot(t_crit, gwp_hetero_total, 'ko', markersize=7, zorder=5)
    ax.text(t_crit - 1, gwp_hetero_total + 0.0001, f'Critical Threshold\n($t_{{crit}}$ = {t_crit:.1f} min)',
            ha='right', va='bottom', fontweight='bold', color='black')

    # 4. Zona de operación real del PMS (sombreado verde)
    ax.axvspan(0, t_actual, color='#2ca02c', alpha=0.15, zorder=1)
    ax.axvline(x=t_actual, color='#2ca02c', linestyle='-', linewidth=2, zorder=2)
    ax.text(t_actual + 1, 0.0015, f'Actual Target Reached\n($t_{{80}}$ = {t_actual} min)',
            ha='left', va='center', color='#2ca02c', fontweight='bold')

    # 5. Flecha indicando el Margen de Seguridad
    ax.annotate('', xy=(t_actual, 0.0004), xytext=(t_crit, 0.0004),
                arrowprops=dict(arrowstyle='<->', color='grey', lw=1.5))
    ax.text((t_actual + t_crit) / 2, 0.0005, 'Temporal Safety Margin (>2000%)',
            ha='center', va='bottom', color='grey', fontweight='bold', fontsize=10)

    # Configuración de límites y etiquetas
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 0.0035)
    ax.set_xlabel('Operational Time (min)', fontweight='bold')
    ax.set_ylabel('Cumulative Carbon Footprint (kg CO$_2$ eq)', fontweight='bold')

    # Cierre ESTRICTO de los ejes superior y derecho (marcos visibles, ticks ocultos)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.tick_params(which='both', top=False, right=False)

    # Añadimos un recuadro negro elegante a la leyenda (estilo paper Q1)
    ax.legend(frameon=False,  loc='best', fontsize=10)

    plt.tight_layout()
    out_dir = 'results'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'Threshold_Analysis.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Gráfica de Threshold Analysis guardada en: {out_path}")

if __name__ == "__main__":
    plot_threshold_analysis()