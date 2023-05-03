# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_utils.ipynb.

# %% ../nbs/05_utils.ipynb 4
from __future__ import annotations
from pathlib import Path

# %% auto 0
__all__ = ['val2list', 'create_dir']

# %% ../nbs/05_utils.ipynb 5
def val2list(val,lsize=1):
    "Convert an element (nonlist value) to a list of 1 element"
    if not isinstance(val,list):
        val=[val for i in range(lsize)]
    return val

# %% ../nbs/05_utils.ipynb 9
def create_dir(path_dir):
    path_dir = Path(path_dir)
    if not path_dir.exists():
        path_dir.mkdir(parents=True)
