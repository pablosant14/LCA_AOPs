# LCA_AOPs: Environmental Trade-offs in Aquaculture Water Treatment 🌊♻️

## 📌 Overview

**LCA_AOPs** is an automated Data Science pipeline designed to process, analyze, and visualize Life Cycle Assessment (LCA) data for Advanced Oxidation Processes (AOPs) applied to aquaculture effluents.

The project evaluates the "sustainability dilemma" of transitioning from traditional homogeneous treatments (e.g., UV-C/NaClO, UV-C/H₂O₂) to intensified heterogeneous photocatalysis (e.g., UV-C/LaFeO₃-Ga₂O₃/PAA). It seamlessly integrates kinetic performance metrics (t80, EEO) with environmental footprints (ReCiPe 2016, Ecoinvent) exported from SimaPro software.

## ✨ Key Features

- **Automated Data Cleaning:** Robust ingestion of SimaPro `.XLS`/`.xlsx` exports, automatically handling duplicate indices, unit mismatches, and metadata artifacts.
- **Dynamic Impact Filtering:** Algorithmic screening of datasets to isolate Top/Bottom performing treatments based on targeted impact categories (e.g., Climate Change).
- **Q1-Grade Visualizations:** Integrated with `SciencePlots` to generate publication-ready figures (Cambria font, strict thesis-style axes formatting, chemical text parsing).
- **Advanced Analytics:**
  - **Eco-efficiency Matrix:** Scatter plotting of kinetic energy consumption vs. environmental impact.
  - **Break-Even Analysis:** Mathematical modeling of catalyst amortization curves across multiple reuse cycles.
  - **Disaggregated Contribution:** 100% stacked bar charts separating UV-C electricity, stirring, commercial reagents, and catalyst footprints.
- **Master Orchestration:** A single `run_all.py` script that sequentially and dynamically executes the entire analytical pipeline.

## 📂 Project Structure

```text
LCA_AOPs/
├── config/
│   └── lca_config.yaml
├── data/
│   └── raw/
│       ├── Análisis_métodos_heterogéneos.XLS
│       ├── Análisis_métodos_homogéneos.XLS
│       ├── Análisis_métodos_scavenging.xlsx
│       └── ICV_final_corregido_2.xlsx
├── scripts/
│   ├── 01_exploratory_lca.py
│   ├── 02_analyze_icv.py
│   ├── 03_analyze_champions.py
│   ├── 04_plot_ecoefficiency.py
│   └── 05_analyze_breakeven.py
├── src/
│   ├── processing.py
│   └── plotting.py
├── results/
├── run_all.py
└── README.md
```

### Configuration

- `lca_config.yaml` — Core configuration: paths, target categories, catalyst GWP.

### Raw data

- `Análisis_métodos_heterogéneos.XLS` — SimaPro outputs for heterogeneous treatments.
- `Análisis_métodos_homogéneos.XLS` — SimaPro outputs for homogeneous treatments.
- `Análisis_métodos_scavenging.xlsx` — SimaPro outputs for scavenging mechanisms.
- `ICV_final_corregido_2.xlsx` — Life Cycle Inventory (physical data).

### Analysis scripts

- `01_exploratory_lca.py` — Generates heatmaps and radar charts.
- `02_analyze_icv.py` — Generates dual-axis inventory plots.
- `03_analyze_champions.py` — Generates relative contribution bars.
- `04_plot_ecoefficiency.py` — Generates the eco-efficiency matrix.
- `05_analyze_breakeven.py` — Calculates catalyst amortization cycles.

### Source modules

- `processing.py` — Mathematical, cleaning, and filtering logic.
- `plotting.py` — Matplotlib/Seaborn plotting functions.

### Results

- `results/` — Auto-generated publication-ready PNGs.

### Orchestration

- `run_all.py` — Master pipeline orchestrator.

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/LCA_AOPs.git
cd LCA_AOPs
```

### 2. Set up a virtual environment

```bash
python -m venv .venv
```

**Windows:**

```powershell
.venv\Scripts\activate
```

**Linux/Mac:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install pandas numpy matplotlib seaborn scienceplots pyyaml openpyxl xlrd
```

> **Note:** LaTeX installation on your system is not required, as plots use the no-LaTeX `SciencePlots` style.

## ⚙️ Usage

### 1. Update the configuration

Place your raw SimaPro and ICV files in `data/raw/`.

Update `config/lca_config.yaml` with:

- The correct filenames.
- SimaPro `skip_rows` parameters.
- Your estimated `catalyst_gwp_per_kg`.

### 2. Run the pipeline

Execute the master orchestrator to run all analytical scripts automatically:

```bash
python run_all.py
```

### 3. Retrieve results

Check the `results/` directory for the generated high-resolution PNGs ready for manuscript integration.

## 👨‍🔬 Author

**Pablo Santiago-Espiñeira**  
Ph.D. Candidate in Chemical Engineering  
Universidad Politécnica de Madrid (UPM)

## 📄 License

This project is licensed under the MIT License — see the `LICENSE` file for details.
