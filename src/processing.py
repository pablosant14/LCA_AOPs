import pandas as pd
import yaml
import numpy as np
import os


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def clean_sima_pro_data(filepath, skip_rows, target_categories=None):
    '''Carga y limpia un archivo de SimaPro, buscando la cabecera dinámicamente.'''
    df_raw = pd.read_excel(filepath, sheet_name="Sheet1", header=None)

    start_row = 0
    # Buscamos en las primeras 60 filas dónde está el texto "Categoría de impacto"
    for i in range(min(60, len(df_raw))):
        if str(df_raw.iloc[i, 0]).startswith("Categoría de impacto"):
            start_row = i
            break

    df = pd.read_excel(filepath, sheet_name="Sheet1", skiprows=start_row)

    # Eliminar columnas basura de SimaPro (forzando str)
    cols_to_keep = [c for c in df.columns if not str(c).startswith('Unnamed') and c not in ['V.Máximo', 'Unidad']]
    df = df[cols_to_keep]

    if target_categories:
        df_filtered = df[df['Categoría de impacto'].isin(target_categories)].copy()
    else:
        df_filtered = df.copy()

    df_filtered.set_index('Categoría de impacto', inplace=True)
    df_filtered = df_filtered[~df_filtered.index.duplicated(keep='first')]

    return df_filtered


def load_and_merge_sima_data(config):
    """Carga y fusiona los Excels homogéneo y heterogéneo en una única matriz maestra."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    path_homo = os.path.join(base_dir, config['paths']['raw_data_homo'])
    path_hetero = os.path.join(base_dir, config['paths']['raw_data_hetero'])

    df_homo = clean_sima_pro_data(path_homo, config['skip_rows']['homo'], None)
    df_hetero = clean_sima_pro_data(path_hetero, config['skip_rows']['hetero'], None)

    df_total = pd.concat([df_homo, df_hetero], axis=1)
    df_total = df_total.loc[:, ~df_total.columns.duplicated()]

    return df_total


def load_icv_data(filepath):
    '''
    Carga y limpia el Inventario de Ciclo de Vida de forma dinámicamente tolerante a errores de escritura.
    '''
    xls = pd.ExcelFile(filepath)
    # Busca dinámicamente cualquier hoja que contenga 'ICV'. Si no, pilla la última por defecto.
    sheet = next((s for s in xls.sheet_names if 'ICV' in str(s).upper()), xls.sheet_names[-1])
    df = pd.read_excel(filepath, sheet_name=sheet)

    # ========================================================
    # MAPEO DINÁMICO DE COLUMNAS (Anti-Hardcoding)
    # ========================================================
    rename_map = {}
    for col in df.columns:
        c_str = str(col).lower()
        if 'oxidante' in c_str and ('kg' in c_str or 'masa' in c_str):
            rename_map[col] = 'Masa Comercial (kg/m3)'
        elif 'catalizador' in c_str and ('kg' in c_str or 'masa' in c_str):
            rename_map[col] = 'Masa Cat. (kg/m3)'
        elif 'experimento' in c_str:
            rename_map[col] = 'Experimento'
        elif 'equipo' in c_str:
            rename_map[col] = 'Equipo Asignado'

    df.rename(columns=rename_map, inplace=True)

    # ========================================================
    # AUTOCORRECTOR DE TYPOS (Philip vs Philips)
    # ========================================================
    if 'Equipo Asignado' in df.columns:
        df['Equipo Asignado'] = df['Equipo Asignado'].apply(
            lambda x: 'Philips 15W' if isinstance(x, str) and 'Philip' in x else x
        )

    # ========================================================
    # FILLNA INTELIGENTE (Números con 0, Textos con vacío)
    # ========================================================
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("")

    if 'Experimento' in df.columns:
        df.set_index('Experimento', inplace=True)

    return df


def extract_champions_contribution(df_icv, top_n=5):
    '''Filtra los tratamientos óptimos de forma DINÁMICA (menor t80) y disgrega la electricidad.'''
    if 'Experimento' not in df_icv.columns:
        df_temp = df_icv.reset_index()
    else:
        df_temp = df_icv.copy()

    df_unique = df_temp.drop_duplicates(subset=['Experimento'])
    df_sorted = df_unique.sort_values(by='t80 (min)', ascending=True)
    df_champs = df_sorted.head(top_n).copy()
    df_champs.set_index('Experimento', inplace=True)

    split_ratios = {
        'Philips 15W': {'uv': 6.0 / 15.0, 'stirrer': 9.0 / 15.0},
        'Apria LED': {'uv': 5.0 / 10.0, 'stirrer': 5.0 / 10.0}
    }

    df_champs['Electricity (UV-C)'] = df_champs.apply(
        lambda row: row['Electricidad Total (kWh/m3)'] * split_ratios.get(row['Equipo Asignado'], {'uv': 1.0})['uv'],
        axis=1)

    df_champs['Electricity (Stirring)'] = df_champs.apply(
        lambda row: row['Electricidad Total (kWh/m3)'] * split_ratios.get(row['Equipo Asignado'], {'stirrer': 0.0})[
            'stirrer'],
        axis=1)

    cols_impact = ['Electricity (UV-C)', 'Electricity (Stirring)', 'Masa Comercial (kg/m3)', 'Masa Cat. (kg/m3)']
    # Aseguramos que solo intente procesar columnas que existan realmente
    valid_cols = [c for c in cols_impact if c in df_champs.columns]

    df_champs_final = df_champs[valid_cols]
    df_pct = df_champs_final.div(df_champs_final.sum(axis=1), axis=0) * 100

    # Renombrado de leyenda dinámico según las columnas válidas
    legend_map = {
        'Electricity (UV-C)': 'Electricity (UV-C)',
        'Electricity (Stirring)': 'Electricity (Stirring)',
        'Masa Comercial (kg/m3)': 'Chemical Reagents',
        'Masa Cat. (kg/m3)': 'Catalyst'
    }
    df_pct.columns = [legend_map[c] for c in df_pct.columns]

    return df_pct


def calculate_ecoefficiency_matrix(df_icv, df_homo, df_hetero):
    '''
    Calcula el E_EO fotocatalítico y cruza con GWP utilizando análisis de cadenas (Fuzzy Matching),
    eliminando por completo la necesidad de un diccionario hardcodeado.
    '''
    if 'Experimento' not in df_icv.columns:
        df_temp = df_icv.reset_index()
    else:
        df_temp = df_icv.copy()

    df_unique = df_temp.drop_duplicates(subset=['Experimento']).set_index('Experimento')
    results = []

    split_ratios = {'Philips 15W': {'uv': 6.0 / 15.0}, 'Apria LED': {'uv': 5.0 / 10.0}}
    orders_of_magnitude = np.log10(5)

    # Agrupamos todas las columnas de SimaPro para el escaneo automático
    sima_cols = {col: 'homo' for col in df_homo.columns}
    sima_cols.update({col: 'hetero' for col in df_hetero.columns})

    for exp_icv, row in df_unique.iterrows():
        exp_str = str(exp_icv).upper().replace(',', '.')

        # Filtro de lógica química: detectamos los ingredientes del experimento
        keywords = []
        if 'NACL' in exp_str:
            keywords = ['NACL']
        elif 'H2O2' in exp_str and 'LAGA' not in exp_str:
            keywords = ['H2O2', 'HOM']
        elif 'PS' in exp_str and 'LAGA' not in exp_str:
            keywords = ['PS', 'HOM']
        elif 'LAGA' in exp_str and 'PAA' in exp_str:
            keywords = ['LAGA', 'PAA']
        elif 'LAGA' in exp_str and 'PS' in exp_str:
            keywords = ['LAGA', 'PS']

        # Si no encaja en las comparativas diana, saltamos al siguiente
        if not keywords:
            continue

        # Escáner: Busca la columna de SimaPro que contenga estas palabras clave
        best_col = None
        for col in sima_cols.keys():
            c_upper = str(col).upper()
            if all(kw in c_upper for kw in keywords):
                best_col = col
                break

        if not best_col:
            continue

        elec_total = row.get('Electricidad Total (kWh/m3)', 0)
        # Ignorar blancos o nulos puros
        if elec_total == 0:
            continue

        equipo = row.get('Equipo Asignado', 'Philips 15W')
        elec_uv = elec_total * split_ratios.get(equipo, {'uv': 1.0})['uv']
        eeo = elec_uv / orders_of_magnitude

        target_df = df_homo if sima_cols[best_col] == 'homo' else df_hetero

        try:
            if 'Climate change' in target_df.index:
                gwp_val = target_df.loc['Climate change', best_col]
            else:
                gwp_val = target_df.iloc[0][best_col]

            if isinstance(gwp_val, pd.Series):
                gwp_val = gwp_val.iloc[0]

            results.append({
                'Treatment': exp_icv,
                'EEO_UVC': float(eeo),
                'GWP': float(gwp_val)
            })
        except Exception:
            pass

    df_results = pd.DataFrame(results)
    return df_results.set_index('Treatment') if not df_results.empty else df_results


def dynamic_impact_filter(df_total, target_metric='Climate change', top_n=4):
    '''Criba dinámica de impactos.'''
    if target_metric not in df_total.index:
        return df_total

    metric_data = df_total.loc[target_metric]
    if isinstance(metric_data, pd.DataFrame):
        metric_data = metric_data.iloc[0]

    metric_data_numeric = pd.to_numeric(metric_data, errors='coerce').dropna()
    sorted_series = metric_data_numeric.sort_values(ascending=True)

    best_cols = sorted_series.head(top_n).index.tolist()
    worst_cols = sorted_series.tail(top_n).index.tolist()

    selected_columns = list(dict.fromkeys(best_cols + worst_cols))
    return df_total[selected_columns].copy()


def calculate_breakeven_cycles(df, col_homo, col_hetero, col_powder, cycles=10):
    """Calcula el impacto diluido del reuso del catalizador en N ciclos."""
    for col in [col_homo, col_hetero, col_powder]:
        if col not in df.columns:
            raise ValueError(f"Error: La columna '{col}' no se encuentra en la matriz unificada.")

    impact_homo = df[col_homo].apply(pd.to_numeric, errors='coerce')
    impact_hetero_op = df[col_hetero].apply(pd.to_numeric, errors='coerce')
    impact_powder = df[col_powder].apply(pd.to_numeric, errors='coerce')

    results = []
    for n in range(1, cycles + 1):
        current_hetero = impact_hetero_op + (impact_powder / n)

        for cat in df.index:
            results.append({
                'Category': cat, 'Cycle': n,
                'System': 'Homogeneous (NaClO)', 'Impact': impact_homo[cat]
            })
            results.append({
                'Category': cat, 'Cycle': n,
                'System': 'Heterogeneous (LaGa + PAA)', 'Impact': current_hetero[cat]
            })

    return pd.DataFrame(results)