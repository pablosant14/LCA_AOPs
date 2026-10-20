import os
import pandas as pd
import numpy as np


def crear_archivos_fantasma():
    print("Fabricando archivos mock para SimaPro e ICV...")

    # Crear carpetas si no existen
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('results', exist_ok=True)

    # =========================================================================
    # 1. MATRIZ HOMOGÉNEA (Con 25 filas de basura SimaPro simulada)
    # =========================================================================
    garbage_homo = [["Basura de cabecera SimaPro"] + [np.nan] * 6 for _ in range(25)]
    cols_homo = ["Categoría de impacto", "Unidad", "[HOM] NaClO 0,75mM - Philips 15W", "[HOM] H2O2 1,64 mM",
                 "[HOM] PS 1,64 mM", "3,2 mM H2O2", "0,75 mM NaClO"]
    data_homo = [
        ["Climate change", "kg CO2 eq", 23.21, 28.5, 2.37, 30.1, 25.4],
        ["Eutrophication, freshwater", "kg P eq", 0.05, 0.06, 0.01, 0.07, 0.05],
        ["Acidification", "mol H+ eq", 0.12, 0.15, 0.03, 0.16, 0.13],
        ["Human toxicity, non-cancer", "CTUh", 1.5, 1.8, 0.5, 1.9, 1.6],
        ["Resource use, fossils", "MJ", 300, 350, 50, 360, 310]
    ]
    df_homo = pd.DataFrame(garbage_homo + [cols_homo] + data_homo)
    df_homo.to_excel('data/raw/Análisis_métodos_homogéneos.xlsx', index=False, header=False, sheet_name="Sheet1")

    # =========================================================================
    # 2. MATRIZ HETEROGÉNEA (Con 40 filas de basura simulada)
    # =========================================================================
    garbage_hetero = [["Basura de cabecera SimaPro"] + [np.nan] * 7 for _ in range(40)]
    cols_hetero = ["Categoría de impacto", "Unidad", "0,5 g/L Ga2O3", "0,5 g/L LaGa",
                   "2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA", "2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PS",
                   "UV-C / H2O2", "UV-C / PS"]
    data_hetero = [
        ["Climate change", "kg CO2 eq", 583.56, 316.14, 10.82, 12.5, 45.0, 39.79],
        ["Eutrophication, freshwater", "kg P eq", 1.5, 0.8, 0.03, 0.04, 0.1, 0.09],
        ["Acidification", "mol H+ eq", 3.2, 1.7, 0.08, 0.1, 0.2, 0.18],
        ["Human toxicity, non-cancer", "CTUh", 40.0, 22.0, 0.9, 1.1, 3.5, 3.0],
        ["Resource use, fossils", "MJ", 8000, 4500, 150, 180, 600, 550]
    ]
    df_hetero = pd.DataFrame(garbage_hetero + [cols_hetero] + data_hetero)
    df_hetero.to_excel('data/raw/Análisis_métodos_heterogéneos.xlsx', index=False, header=False, sheet_name="Sheet1")

    # =========================================================================
    # 3. MATRIZ DE INVENTARIO (ICV)
    # =========================================================================
    cols_icv = ["Experimento", "Electricidad Total (kWh/m3)", "Equipo Asignado", "Masa Comercial (kg/m3)",
                "Masa Cat. (kg/m3)", "t80 (min)"]
    data_icv = [
        ["[HOM] NaClO 0,75mM - Philips 15W", 8.17, "Philips 15W", 0.05, 0.0, 15.72],
        ["0,5 g/L LaGa", 150.0, "Apria LED", 0.0, 0.5, 193.9],
        ["2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA", 9.84, "Apria LED", 0.03, 0.125, 27.86],
        ["[HOM] PS 1,64 mM", 10.5, "Philips 15W", 0.08, 0.0, 18.0],
        ["0,5 g/L Ga2O3", 180.0, "Apria LED", 0.0, 0.5, 240.0]
    ]
    df_icv = pd.DataFrame(data_icv, columns=cols_icv)
    df_icv.to_excel('data/raw/ICV_final_corregido.xlsx', index=False, sheet_name="ICV_Principal")

    print("✅ ¡Archivos fantasma creados con éxito en data/raw/!")


if __name__ == "__main__":
    crear_archivos_fantasma()