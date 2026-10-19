# src/processing.py
import pandas as pd
import yaml
import numpy as np
import os


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def clean_sima_pro_data(filepath, skip_rows, target_categories=None):
    '''Carga y limpia un archivo de SimaPro, devolviendo un DataFrame indexado por categoría de impacto.'''
    df = pd.read_excel(filepath, sheet_name="Sheet1", skiprows=skip_rows)

    # Eliminar columnas basura de SimaPro
    cols_to_keep = [c for c in df.columns if not c.startswith('Unnamed') and c not in ['V.Máximo', 'Unidad']]
    df = df[cols_to_keep]

    if target_categories:
        df_filtered = df[df['Categoría de impacto'].isin(target_categories)].copy()
    else:
        df_filtered = df.copy()

    df_filtered.set_index('Categoría de impacto', inplace=True)
    # Eliminar filas duplicadas (fantasmas de SimaPro)
    df_filtered = df_filtered[~df_filtered.index.duplicated(keep='first')]

    return df_filtered


def load_and_merge_sima_data(config):
    """Carga y fusiona los Excels homogéneo y heterogéneo en una única matriz maestra."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    path_homo = os.path.join(base_dir, config['paths']['raw_data_homo'])
    path_hetero = os.path.join(base_dir, config['paths']['raw_data_hetero'])

    df_homo = clean_sima_pro_data(path_homo, config['skip_rows']['homo'], None)
    df_hetero = clean_sima_pro_data(path_hetero, config['skip_rows']['hetero'], None)

    # Unir ambas matrices por columnas
    df_total = pd.concat([df_homo, df_hetero], axis=1)

    # Eliminar columnas duplicadas si algún nombre se repetía entre archivos
    df_total = df_total.loc[:, ~df_total.columns.duplicated()]

    return df_total

def load_icv_data(filepath):
    '''
    Carga y limpia el Inventario de Ciclo de Vida (ICV) de forma GENÉRICA.
    Carga todas las columnas numéricas relevantes para análisis dinámicos o cinéticos.
    '''
    df = pd.read_excel(filepath, sheet_name='ICV_Principal')

    # Rellenar NaN con ceros para garantizar procesabilidad numérica
    df.fillna(0, inplace=True)

    # Pasamos 'Experimento' al ÍNDICE. Fundamental para los cruces dinámicos.
    df.set_index('Experimento', inplace=True)

    return df


def extract_champions_contribution(df_icv, top_n=5):
    '''Filtra los tratamientos óptimos de forma DINÁMICA (menor t80) y disgrega la electricidad (Luz vs Agitación).'''

    # ========================================================
    # SELECCIÓN DINÁMICA DE CAMPEONES
    # ========================================================
    # 1. Recuperamos 'Experimento' del índice un momento para poder usar drop_duplicates
    if 'Experimento' not in df_icv.columns:
        df_temp = df_icv.reset_index()
    else:
        df_temp = df_icv.copy()

    # 2. Eliminamos duplicados para que no nos salgan barras repetidas en el gráfico
    df_unique = df_temp.drop_duplicates(subset=['Experimento'])

    # 3. Ordenamos por eficiencia cinética: menor t80 = proceso más rápido (éxito de degradación)
    # FIX TURN 23: Columna t80 garantizada por el cargador genérico load_icv_data
    df_sorted = df_unique.sort_values(by='t80 (min)', ascending=True)

    # 4. Nos quedamos con los Top N "Gladiadores" del Capítulo 5
    df_champs = df_sorted.head(top_n).copy()

    # 5. Devolvemos el nombre del experimento al índice
    df_champs.set_index('Experimento', inplace=True)

    # ========================================================
    # DISGREGACIÓN DE POTENCIAS (Luz vs Agitación)
    # Philips TUV: 6W tubo + 9W agitador/balasto = 15W total
    # Apria LED: Asumimos 5W LED + 5W agitador = 10W total (TODO: Ajustar si se confirma dato exacto)
    # ========================================================
    split_ratios = {
        'Philips 15W': {'uv': 6.0 / 15.0, 'stirrer': 9.0 / 15.0},
        'Apria LED': {'uv': 5.0 / 10.0, 'stirrer': 5.0 / 10.0}
    }

    # Calculamos las dos nuevas columnas dinámicamente sobre la matriz bruta (kWh/m3)
    df_champs['Electricity (UV-C)'] = df_champs.apply(
        lambda row: row['Electricidad Total (kWh/m3)'] * split_ratios.get(row['Equipo Asignado'], {'uv': 1.0})['uv'],
        axis=1)

    df_champs['Electricity (Stirring)'] = df_champs.apply(
        lambda row: row['Electricidad Total (kWh/m3)'] * split_ratios.get(row['Equipo Asignado'], {'stirrer': 0.0})[
            'stirrer'], axis=1)

    # Seleccionamos las 4 columnas finales de entrada de recursos (absolutos kWh/m3)
    cols_impact = ['Electricity (UV-C)', 'Electricity (Stirring)', 'Masa Comercial (kg/m3)', 'Masa Cat. (kg/m3)']
    df_champs_final = df_champs[cols_impact]

    # Normalización al 100% por fila para el gráfico apilado
    df_pct = df_champs_final.div(df_champs_final.sum(axis=1), axis=0) * 100
    df_pct.columns = ['Electricity (UV-C)', 'Electricity (Stirring)', 'Chemical Reagents', 'Catalyst']

    return df_pct


# Reemplaza SOLO esta función en src/processing.py

def calculate_ecoefficiency_matrix(df_icv, df_homo, df_hetero):
    '''
    Calcula el E_EO fotocatalítico y lo cruza con el Impacto Ambiental (Climate Change)
    usando un diccionario de mapeo explícito para evitar errores de texto.
    '''
    mapping = {
        '2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PAA': ('hetero', '2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA'),
        '2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PS': ('hetero', '2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PS'),
        'UV-C/H2O2': ('hetero', 'UV-C / H2O2'),
        'UV-C/PS': ('hetero', 'UV-C / PS'),
        '0.75 mM NaClO': ('homo', '[HOM] NaClO 0,75mM - Philips 15W')
    }

    if 'Experimento' not in df_icv.columns:
        df_temp = df_icv.reset_index()
    else:
        df_temp = df_icv.copy()

    df_unique = df_temp.drop_duplicates(subset=['Experimento']).set_index('Experimento')
    results = []

    split_ratios = {
        'Philips 15W': {'uv': 6.0 / 15.0},
        'Apria LED': {'uv': 5.0 / 10.0}
    }

    orders_of_magnitude = np.log10(5)

    for exp_icv, (source, col_sima) in mapping.items():
        if exp_icv in df_unique.index:
            row = df_unique.loc[exp_icv]

            elec_total = row['Electricidad Total (kWh/m3)']
            equipo = row['Equipo Asignado']
            elec_uv = elec_total * split_ratios.get(equipo, {'uv': 1.0})['uv']
            eeo = elec_uv / orders_of_magnitude

            try:
                if source == 'homo':
                    gwp_val = df_homo.loc['Climate change', col_sima]
                else:
                    gwp_val = df_hetero.loc['Climate change', col_sima]

                # ========================================================
                # FIX ROBUSTO: Forzamos la extracción del número escalar
                # ========================================================
                if isinstance(gwp_val, pd.Series):
                    gwp_val = gwp_val.iloc[0]  # Si SimaPro duplica filas, cogemos el primero

                # Convertimos explícitamente a float para que matplotlib no llore
                gwp = float(gwp_val)
                eeo = float(eeo)

                results.append({
                    'Treatment': exp_icv,
                    'EEO_UVC': eeo,
                    'GWP': gwp
                })
            except KeyError as e:
                print(f"Advertencia: Revisa los nombres en SimaPro. Error en: {e}")

    df_results = pd.DataFrame(results)

    if df_results.empty:
        raise ValueError("No se ha mapeado ni un solo dato. Revisa los nombres del diccionario.")

    return df_results.set_index('Treatment')


def dynamic_impact_filter(df_total, target_metric='Climate change', top_n=4):
    '''
    Criba dinámica: Selecciona los N tratamientos más limpios y los N más sucios.
    A prueba de columnas de texto infiltradas.
    '''
    if target_metric not in df_total.index:
        print(f"Advertencia: '{target_metric}' no está en el índice. Se devuelve la matriz original.")
        return df_total

    # Extraer la fila de la métrica diana
    metric_data = df_total.loc[target_metric]

    if isinstance(metric_data, pd.DataFrame):
        metric_data = metric_data.iloc[0]

    # ========================================================
    # FIX ROBUSTO: Forzar a numérico. Todo lo que sea texto (ej. unidades)
    # se convierte en NaN y lo eliminamos con dropna() antes de ordenar.
    # ========================================================
    metric_data_numeric = pd.to_numeric(metric_data, errors='coerce').dropna()

    # Ordenamos de forma segura (ya solo hay números puros)
    sorted_series = metric_data_numeric.sort_values(ascending=True)

    # Coger los N mejores y los N peores
    best_cols = sorted_series.head(top_n).index.tolist()
    worst_cols = sorted_series.tail(top_n).index.tolist()

    # Unir sin duplicados
    selected_columns = list(dict.fromkeys(best_cols + worst_cols))

    df_cribado = df_total[selected_columns].copy()

    return df_cribado


def calculate_breakeven_cycles(df, col_homo, col_hetero, col_powder, cycles=10):
    """
    Calcula el impacto diluido del reuso del catalizador en N ciclos.
    Impacto(n) = Impacto_Operativo (Elec+PAA) + (Impacto_Polvo / n)
    """
    for col in [col_homo, col_hetero, col_powder]:
        if col not in df.columns:
            raise ValueError(f"🚨 Error: La columna '{col}' no se encuentra en la matriz unificada.")

    impact_homo = df[col_homo].apply(pd.to_numeric, errors='coerce')
    # Juanjo modeló esto SÓLO con la electricidad y el PAA, no restamos nada
    impact_hetero_op = df[col_hetero].apply(pd.to_numeric, errors='coerce')
    impact_powder = df[col_powder].apply(pd.to_numeric, errors='coerce')

    results = []
    for n in range(1, cycles + 1):
        # El impacto de fabricar el polvo se divide entre los usos y se suma al operativo
        current_hetero = impact_hetero_op + (impact_powder / n)

        for cat in df.index:
            results.append({
                'Category': cat,
                'Cycle': n,
                'System': 'Homogeneous (NaClO)',
                'Impact': impact_homo[cat]
            })
            results.append({
                'Category': cat,
                'Cycle': n,
                'System': 'Heterogeneous (LaGa + PAA)',
                'Impact': current_hetero[cat]
            })

    return pd.DataFrame(results)