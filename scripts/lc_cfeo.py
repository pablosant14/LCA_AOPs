import numpy as np
import matplotlib.pyplot as plt
import os


def plot_dynamic_lc_cfeo():
    try:
        plt.style.use(['science', 'no-latex'])
    except OSError:
        plt.style.use('default')

    plt.rcParams.update({
        "font.family": "Cambria",
        "font.size": 12,
        "mathtext.default": "regular"
    })

    # Parámetros cinéticos (k_obs)
    k_homo = 0.6140
    k_hetero = 0.1480

    # Parámetros de Huella de Carbono (GWP)
    static_gwp_homo = 0.000007
    rate_gwp_homo = 0.0000507
    static_gwp_hetero = 0.00260
    rate_gwp_hetero = 0.000009

    t = np.linspace(0.1, 30, 1000)

    # Cálculos corregidos (añadidos operadores matemáticos)
    c_c0_homo = np.exp(-k_homo * t)
    pct_homo = 100 * (1 - c_c0_homo)

    orders_homo = -np.log10(c_c0_homo)
    gwp_homo = static_gwp_homo + rate_gwp_homo * t
    lc_cfeo_homo = gwp_homo / orders_homo

    c_c0_hetero = np.exp(-k_hetero * t)
    pct_hetero = 100 * (1 - c_c0_hetero)

    orders_hetero = -np.log10(c_c0_hetero)
    gwp_hetero = static_gwp_hetero + rate_gwp_hetero * t
    lc_cfeo_hetero = gwp_hetero / orders_hetero

    mask_homo = pct_homo <= 99
    mask_hetero = pct_hetero <= 99

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.plot(pct_homo[mask_homo], lc_cfeo_homo[mask_homo],
            label='Best Homogeneous\n(10 W/m$^2$ + 0.1 mM PMS)',
            color='#1f77b4', linestyle='--', linewidth=2.5)

    ax.plot(pct_hetero[mask_hetero], lc_cfeo_hetero[mask_hetero],
            label='Best Heterogeneous\n(2.5 W/m$^2$ UV-C + 0.5 g/L LaGa + 0.5 mM PAA)',
            color='#ff7f0e', linewidth=2.5)

    # Línea vertical y texto posicionado entre ambas curvas
    ax.axvline(x=80, color='grey', linestyle=':', alpha=0.7)
    ax.text(78, 0.001, '80% Target', rotation=90, color='grey', fontsize=10, verticalalignment='center')

    ax.set_yscale('log')
    ax.set_xlim(10, 100)
    ax.set_ylim(0.0001, 0.1)

    ax.set_xlabel('Antibiotic Abatement (%)', fontweight='bold')
    ax.set_ylabel('Dynamic LC-CF$_{EO}$ (kg CO$_2$ eq / order)', fontweight='bold')

    # Cierre de ejes superior y derecho manteniendo la norma de no poner ticks
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.tick_params(which='both', top=False, right=False)

    ax.legend(frameon=False, loc='best', fontsize=10)
    plt.tight_layout()

    out_dir = 'results'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'LC_CFEO_Dynamic_Curve.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Gráfica generada con éxito en: {out_path}")


if __name__ == "__main__":
    plot_dynamic_lc_cfeo()