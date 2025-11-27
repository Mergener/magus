# Magus

## Dev Setup

Create a virtual environment and install dependencies:

- Linux
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt 
```

- Windows
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt 
```

Once you're done installing dependencies, make sure to install the pre-commit hooks:

```bash
pre-commit install
```

## Running

After the setup phase, from the repository root directory, you can...

... run the client:
```bash 
python -m client
```
... run the server:
```bash 
python -m server
```

## Generating Executable

To generate an executable, run the corresponding bundle script (`bundle.sh` for Linux/macOS, `bundle.bat` for Windows).
The built executable will be located in the `bin/` directory.

## Acknowledgments

Acknlowledgments for third-party assets or any other contributions are listed in `acknowledgments.md`.