# src/processing.py
import pandas as pd
import yaml
import numpy as np


def load_config(config_path="config/lca_config.yaml"):
    '''Carga el archivo de configuración YAML del proyecto.'''
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def clean_sima_pro_data(filepath, skip_rows, target_categories):
    '''Carga y filtra el Excel bruto de impacto del SimaPro (formatos antiguo .XLS).'''
    df = pd.read_excel(filepath, sheet_name="Sheet1", skiprows=skip_rows)

    # ========================================================
    # FIX: Eliminamos explícitamente 'Unidad' y 'V.Máximo'
    # ========================================================
    cols_to_keep = [c for c in df.columns if not c.startswith('Unnamed') and c not in ['V.Máximo', 'Unidad']]
    df = df[cols_to_keep]

    df_filtered = df[df['Categoría de impacto'].isin(target_categories)].copy()
    df_filtered.set_index('Categoría de impacto', inplace=True)

    # Eliminar filas duplicadas (fantasmas del SimaPro)
    df_filtered = df_filtered[~df_filtered.index.duplicated(keep='first')]

    return df_filtered


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

def calculate_breakeven_cycles(df_icv, df_homo, df_hetero, config):
    '''
    Calcula la curva de amortización ambiental (GWP) de un proceso heterogéneo
    frente a un proceso homogéneo base, variando los ciclos de reúso (1 a 15).
    '''
    # 1. Definimos los contendientes (puedes cambiarlos según lo que decidas en la tesis)
    hetero_process = '2.5 W/m2 UV-C  + 0.5 g/L LaGa + 0.5 mM PAA'
    homo_process = '0.75 mM NaClO'

    # Columnas mapeadas en SimaPro
    col_hetero_sima = '2,5 W/m2 UV-C + 0,5 g/L LaGa + 0,5 mM PAA'
    col_homo_sima = '[HOM] NaClO 0,75mM - Philips 15W'

    # 2. Extraer el impacto base de SimaPro (Sabemos que están en 3 ciclos y 1 ciclo respect.)
    gwp_hetero_3cycles = float(df_hetero.loc['Climate change', col_hetero_sima])
    gwp_homo_constant = float(df_homo.loc['Climate change', col_homo_sima])

    # ========================================================
    # INGENIERÍA INVERSA DEL IMPACTO DEL CATALIZADOR
    # ========================================================
    # Dosis total de catalizador en el reactor = 0.5 kg/m3.
    # Impacto estimado de fabricar 1 kg de LaGa (kg CO2 eq/kg).
    # TODO: Ajustar este valor con el nodo puro de SimaPro de tu TFM.
    catalyst_gwp_per_kg = config.get('catalyst_gwp_per_kg', 50.0)

    total_catalyst_gwp = 0.5 * catalyst_gwp_per_kg

    # Si el SimaPro se calculó para 3 ciclos, el impacto reportado es:
    # GWP_SimaPro = GWP_Operacion + (GWP_Catalizador_Total / 3)
    # Despejamos el impacto operativo (luz + PAA + etc):
    gwp_operativo = gwp_hetero_3cycles - (total_catalyst_gwp / 3.0)

    # 3. Proyectar la curva para N ciclos (de 1 a 15)
    ciclos = np.arange(1, 16)
    gwp_hetero_curve = gwp_operativo + (total_catalyst_gwp / ciclos)

    # 4. Empaquetar resultados
    df_breakeven = pd.DataFrame({
        'Ciclos': ciclos,
        'Hetero_LaGa_PAA': gwp_hetero_curve,
        'Homo_NaClO_Baseline': np.repeat(gwp_homo_constant, len(ciclos))
    }).set_index('Ciclos')

    return df_breakeven