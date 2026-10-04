
import rasterio
import os
from shapely.geometry import box

def tif_file_iter(dir, exclude_parent_folder_prefixes=['.', '_']):
    #go through all directories, subdirectiories and files
    for dir, _, files in os.walk(dir):
        # ADD in 20250912: exclude some folders
        if exclude_parent_folder_prefixes and any([dir.split(os.sep)[-1].startswith(ele) for ele in exclude_parent_folder_prefixes]):
            print(f"Excluding folder {dir} ...")
            continue
        #layer = dir.split("/")[-1] # in windows, folders are seperated by \
        layer = os.path.basename(os.path.normpath(dir))
        #for get filenames
        for fname in files:
            #if filenames end with .tif perform following
            # FIX 20241228: handle error "._N35_15_2020LC030_n35_15_2020lc030.tif' not recognized as a supported file format."
            if fname.endswith(".tif") and not fname.startswith('._'):
                #get path to the tile
                raster_path=os.path.join(dir, fname)
                #open raster tile with rasterio by passing the path
                raster =rasterio.open(raster_path)
                #get bounds of raster tile
                bounds=raster.bounds
                #construct bounding box from bounds
                gpd_box= box(bounds.left, bounds.bottom, bounds.right, bounds.top)
                
                yield {"path": raster_path, "geometry": gpd_box, 'crs': raster.crs, 'layer': layer}

def list_tif_files(dir):
    res = []
    for dir, _, files in os.walk(dir):
        #for get filenames
        for fname in files:
            #if filenames end with .tif perform following
            if not fname.startswith('.') and fname.endswith(".tif"):
                #get path to the tile
                fpath=os.path.join(dir, fname)
                res.append(fpath)

    return res