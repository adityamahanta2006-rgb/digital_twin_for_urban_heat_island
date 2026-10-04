import os
from pathlib import Path

def make_sure_dir_exist(p, is_file=False):
    if is_file:
        p = os.path.dirname(os.path.realpath(p))
    Path(p).mkdir(parents=True, exist_ok=True)

if __name__ == '__main__':
    p = r"C:\Users\XU\OneDrive - Politecnico di Milano\CCI HRLC\Phase2\MOLCAP\matcher\tmp/result\Static_products_processing/Africa/gpkg_africa_static_prod_exist.csv"
    make_sure_dir_exist(p)