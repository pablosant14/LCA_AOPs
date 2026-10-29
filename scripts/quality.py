import numpy as np
import matplotlib.pyplot as plt
import os


def plot_phytotoxicity():
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({
        "font.family": "Cambria",
        "font.size": 12,
        "mathtext.default": "regular"
    })

    # Tratamientos evaluados
    treatments = ['UV-C/NaClO\n(Homogeneous)', 'UV-C/PMS\n(Homogeneous)',
                  'LaGa/UV-C\n(Heterogeneous)', 'LaGa/UV-C/PAA\n(Intensified Het.)']

    # Datos de Germination Index (GI) en % (¡Sustituye los del LaGa por tus datos exactos!)
    gi_radish = [59.9, 104.4, 112.5, 135.2]
    gi_tomato = [26.6, 72.8, 105.1, 122.4]

    x = np.arange(len(treatments))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))

    # Barras
    rects1 = ax.bar(x - width / 2, gi_radish, width, label='Raphanus sativus (Radish)',
                    color='#d62728', edgecolor='black', zorder=3)
    rects2 = ax.bar(x + width / 2, gi_tomato, width, label='Solanum lycopersicum (Tomato)',
                    color='#2ca02c', edgecolor='black', zorder=3)

    # Líneas de referencia (Control 100% y Umbral Toxicidad 70%)
    ax.axhline(y=100, color='blue', linestyle='-.', linewidth=2, zorder=2)
    ax.text(-0.4, 102, 'Control Reference (100%)', color='blue', fontweight='bold', fontsize=10)

    ax.axhline(y=70, color='grey', linestyle=':', linewidth=2, zorder=2)
    ax.text(-0.5, 72, 'Non-Phytotoxic Threshold (70%)', color='grey', fontweight='bold', fontsize=10)

    # Etiquetas de valor encima de las barras
    for rect in rects1 + rects2:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    ax.set_ylabel('Germination Index, GI (%)', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(treatments, fontweight='bold')

    # Límites del eje Y
    ax.set_ylim(0, 160)

    # Cierre estricto de ejes
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.tick_params(which='both', top=False, right=False)

    ax.legend(frameon=False, edgecolor='black', loc='upper left')

    plt.tight_layout()

    out_dir = 'results'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'Phytotoxicity_Analysis.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Gráfica guardada en: {out_path}")


if __name__ == "__main__":
    plot_phytotoxicity()