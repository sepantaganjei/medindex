# Feature scripts setup

> **WARNING:** use **Python 3.11**. Other versions (for example 3.14) can fail during `pyradiomics` installation.

## 0) Check Python version first

From the repository root, run:

```bash
python --version
```

If `python --version` is not `3.11.x`, switch your environment so `python` points to Python 3.11 before continuing.

## 1) Create a virtual environment

From the repository root:

```bash
python -m venv .venv
```

## 2) Activate the virtual environment

- **Linux/macOS (bash/zsh):**

  ```bash
  source .venv/bin/activate
  ```

- **Windows (PowerShell):**

  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```

- **Windows (cmd.exe):**

  ```bat
  .venv\Scripts\activate.bat
  ```

## 3) Install dependencies (required order)

From the repository root, with the venv active:

```bash
pip install "numpy==1.26.4"
pip install . --no-build-isolation
```

This order is required because `pyradiomics` needs `numpy` available during build/metadata.
