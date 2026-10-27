import numpy as np
import matplotlib.pyplot as plt
import os


def plot_decarbonization_scenario():
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({
        "font.family": "Cambria",
        "font.size": 12,
        "mathtext.default": "regular"
    })

    # Datos extraídos del LCA
    # UV-C/PMS
    pms_total = 0.00014
    pms_green = 0.000007  # Solo queda el GWP del reactivo PMS

    # LaGa/UV-C/PAA
    laga_total = 0.00270
    laga_green = 0.00260  # Queda el GWP de la síntesis del polvo y el reactivo PAA

    labels = ['Best Homogeneous\n(UV-C/PMS)', 'Best Heterogeneous\n(LaGa/UV-C/PAA)']
    current_grid = [pms_total, laga_total]
    green_grid = [pms_green, laga_green]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))

    rects1 = ax.bar(x - width / 2, current_grid, width, label='Current Electricity Grid', color='#1f77b4',
                    edgecolor='black')
    rects2 = ax.bar(x + width / 2, green_grid, width, label='100% Renewable Grid', color='#2ca02c', edgecolor='black')

    # Añadir valores numéricos encima de las barras de la izquierda (Current Grid)
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f'{height:.5f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    # Añadir valores numéricos y etiquetas de reducción encima de las barras verdes (100% Renewable Grid)
    for i, rect in enumerate(rects2):
        height = rect.get_height()
        reduction_text = '-95%' if i == 0 else '-3.7%'
        label_content = f'{height:.5f}\n({reduction_text} reduction)'

        ax.annotate(label_content,
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_ylabel('Global Warming Potential (kg CO$_2$ eq)', fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontweight='bold')

    # Ejes perimetrales completamente cerrados sin ticks
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.tick_params(which='both', top=False, right=False)

    ax.legend(frameon=False, loc='upper left')

    ax.set_ylim(0, 0.0034)

    plt.tight_layout()

    out_dir = 'results'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'Decarbonization_Scenario.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Gráfica guardada en: {out_path}")


if __name__ == "__main__":
    plot_decarbonization_scenario()