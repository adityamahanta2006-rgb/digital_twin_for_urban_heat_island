# Global default value
DEFAULT_CRS_EPSG_CODE = 4326
DEFAULT_CRS = f'EPSG:{DEFAULT_CRS_EPSG_CODE}'

# MOLCA legends
MOLCA_Label_Codes={'Shrubland':5, 'Grassland':7, 'Cropland':8, 'Built-up':13, 'Bareland':12, 'Permanent_ice_and_snow':16, 'Water':15, 'Wetland':9, 'Lichens_and_Mosses':11,'Forest':20, 'No data': 255}

# No Data
DEFAULT_TARGET_NO_DATA = 255

# for paralle
NUM_WORKERS = 2 # not used by now
def set_number_of_workers(num):
    global NUM_WORKERS
    NUM_WORKERS = num

# supported parallel methods for MOLCX generation
METHOD_PARALLEL_DS_PER_TILE = "datasets_per_tile" # Traverse the tiles sequentially and process datasets in parallel for each tile.
METHOD_PARALLEL_TILES = "tiles" # Tiles are processed in parallel, and each tile processes datasets sequentially.
METHOD_SERIAL = "serial" # Serial processing, no parallelism.

# set log
LOG_LEVEL = 'info'
def set_log_level(level):
    global LOG_LEVEL
    LOG_LEVEL = level.strip().upper()
    
def get_log_level():
    return LOG_LEVEL