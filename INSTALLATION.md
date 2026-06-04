# Installation Guide for UNSAFE

This guide provides step-by-step instructions to set up the **UNSAFE** (UNcertain Structure And Fragility Ensemble) framework on your system.

---

## Prerequisites
Before you begin, ensure you have Python 3.9 or higher installed on your system. 

You can verify your Python version by running:
```bash
python --version
```

---

## Option A: Using Standard Python Virtual Environment (`venv` + `pip`)
This is the recommended method if you want to use standard Python tooling without installing Conda or Mamba.

### 1. Create a Virtual Environment
Navigate to the root of the project directory and create a virtual environment:
```bash
# Create a virtual environment named "env"
python -m venv env
```

### 2. Activate the Virtual Environment
Activate the environment based on your operating system and terminal:
- **Windows (PowerShell):**
  ```powershell
  .\env\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt):**
  ```cmd
  .\env\Scripts\activate.bat
  ```
- **macOS / Linux:**
  ```bash
  source env/bin/activate
  ```

### 3. Install the Package and Dependencies
Install `unsafe` in editable development mode:
```bash
pip install -e .
```

### 4. Install Jupyter and Visualization Dependencies
To run the included examples and visualization notebooks:
```bash
pip install jupyter matplotlib seaborn rioxarray ipykernel
```

---

## Option B: Using Conda or Mamba
Conda/Mamba is highly recommended for GIS/geospatial packages, as it cleanly resolves binary dependencies (like GDAL/GEOS) for libraries like `geopandas` and `rasterio`.

### 1. Create the Conda Environment
From the project root directory, create the environment using the provided YAML file:
```bash
conda env create -f examples/env/environment.yml
```
*(Or replace `conda` with `mamba` if you use Mamba)*

### 2. Activate the Environment
```bash
conda activate unsafe_env
```

### 3. Register the Environment with Jupyter
Install the IPython kernel so it can be selected from within Jupyter notebooks:
```bash
python -m ipykernel install --user --name unsafe_env
```

### 4. Install the Package in Development Mode
From the project root directory, install `unsafe` in editable development mode:
```bash
pip install -e .
```

---

## Running the Examples

Once installed, you can run the provided tutorial notebooks to verify the installation:

1. Launch Jupyter Notebook:
   ```bash
   jupyter notebook
   ```
2. Navigate to the partial data example notebook:
   [partial_data_example.ipynb](examples/phil_frd_partial/notebooks/partial_data_example.ipynb)
3. If you used **Option B**, ensure the Jupyter kernel is set to `unsafe`.
4. Run all cells in the notebook to verify the installation output.
