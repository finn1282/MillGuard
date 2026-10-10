#!/bin/sh
# macOS only: LightGBM needs libomp. Preferred: `brew install libomp`. Fallback (no brew): reuse scikit-learn's bundled copy.
PY=${1:-.venv/bin/python}
SP=$($PY -c "import site; print(site.getsitepackages()[0])")
SRC=$(ls "$SP"/sklearn/.dylibs/libomp.dylib 2>/dev/null)
[ -z "$SRC" ] && { echo "no bundled libomp found; run: brew install libomp"; exit 1; }
cp "$SRC" "$SP/lightgbm/lib/libomp.dylib"
install_name_tool -add_rpath @loader_path "$SP/lightgbm/lib/lib_lightgbm.dylib" 2>/dev/null
codesign --force --sign - "$SP/lightgbm/lib/lib_lightgbm.dylib" "$SP/lightgbm/lib/libomp.dylib" 2>/dev/null
$PY -c "import lightgbm; print('lightgbm OK')"
