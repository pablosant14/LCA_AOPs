# scripts/analyze_breakeven.py
import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.processing import load_config, clean_sima_pro_data, calculate_breakeven_cycles
from src.plotting import plot_breakeven_curve


def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config = load_config(os.path.join(base_dir, 'config', 'lca_config.yaml'))

    print("Cargando matrices de SimaPro limpias...")
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

    # Unificamos universos para que el script pueda pescar cualquier columna
    df_total = pd.concat([df_homo, df_hetero], axis=1)
    df_total = df_total.loc[:, ~df_total.columns.duplicated()]

    # =========================================================================
    # LOS 3 CONTENDIENTES DEL BREAK-EVEN (Tienen que existir en df_total)
    # =========================================================================
    col_homo = "[HOM] NaClO 0,75mM - Philips 15W"  # El "enemigo" a batir de un solo uso
    col_hetero = "2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA"  # Tu sistema completo
    col_powder = "0,5 g/L LaGa"  # El impacto puro de sintetizar el catalizador

    print("Calculando amortización del catalizador...")
    df_breakeven = calculate_breakeven_cycles(df_total, col_homo, col_hetero, col_powder, cycles=10)

    print("Generando gráfico de Break-Even...")
    plot_breakeven_curve(df_breakeven, "BreakEven_Analysis", config)


if __name__ == "__main__":
    main()