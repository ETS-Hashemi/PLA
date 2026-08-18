import pathlib
import sys

# Make the in-repo `pla` package importable when running pytest without an
# editable install.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
