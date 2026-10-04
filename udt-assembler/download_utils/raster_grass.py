############ Based on Grass GIS ############
import grass.script as gs
import grass.script.array as garray
import subprocess
import os
import tempfile
from colorama import Fore, Style

from pathlib import Path

from osgeo import gdal
# 启用异常
gdal.UseExceptions()

def is_north_up(raster_path):
    """
    检查栅格文件是否为 North-up（无旋转或翻转）。
    
    参数:
        raster_path (str): 栅格文件路径。
    
    返回:
        bool: 如果是 North-up 返回 True，否则返回 False。
    """
    dataset = gdal.Open(raster_path)
    if dataset is None:
        raise FileNotFoundError(f"无法打开文件: {raster_path}")
    
    # 获取仿射变换矩阵
    geotransform = dataset.GetGeoTransform()
    if not geotransform:
        raise ValueError(f"无法获取 GeoTransform 信息: {raster_path}")
    
    # 仿射变换矩阵的定义
    # geotransform = (top_left_x, pixel_width, rotation_x, top_left_y, rotation_y, pixel_height)
    _, pixel_width, rotation_x, _, rotation_y, pixel_height = geotransform

    # North-up 的条件：
    # 1. 没有旋转：rotation_x 和 rotation_y 为 0。
    # 2. 像素高度为负（top-left 的 Y 向下是负方向）。
    is_north_up = rotation_x == 0 and rotation_y == 0 and pixel_height < 0
    
    return is_north_up
def fix_to_north_up(input_raster, output_raster):
    """
    使用 gdalwarp 修正栅格为 North-up。
    """
    cmd = [
        "gdalwarp", 
        "-co", "COMPRESS=LZW", 
        input_raster, 
        output_raster
    ]
    subprocess.run(cmd, check=True)
    print(f"{input_raster} now is North-up, the corrected version is {output_raster}.")


def reproject_raster(input_path, output_path, target_srs="EPSG:4326"):
    """
    重新投影栅格文件。
    
    参数:
        input_path (str): 输入栅格文件路径。
        output_path (str): 输出栅格文件路径。
        target_srs (str): 目标坐标参考系（默认为 "EPSG:4326"）。
    """
    cmd = [
        "gdalwarp", 
        "-t_srs", target_srs, 
        input_path, 
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"{input_path} now is reprojected to {target_srs}, the corrected version is {input_path}.")

# 使用 GRASS 脚本工具导入 TIFF 文件到 GRASS GIS 中
def import_tif_to_grass(input_tif, output_map, band=1, overwrite=True):
    """
    Import a specific band from a multi-band TIFF file into GRASS GIS.
    
    Parameters:
        input_tif (str): Path to the input TIFF file.
        output_map (str): Name of the output GRASS raster map.
        band (int): The band number to import (default: 1).
    """
    gs.run_command('r.import', input=input_tif, output=output_map, band=band, overwrite=overwrite)
    print(f"Imported band {band} from {input_tif} as {output_map}")
    
def safe_import_tif_to_grass(input_tif, output_map, band=1, overwrite=True, extent="input", resolution="estimated"):
    """
    Safely import a raster into GRASS GIS.
        Fixes potential flipping/rotation issues using gdalwarp if necessary.
    
    Parameters:
        input_tif (str): Path to the input TIFF file.
        output_map (str): Name of the output GRASS raster map.
        band (int): The band number to import (default: 1).
    """
    temp_dir = tempfile.mkdtemp()
    if not is_north_up(input_tif):
        print(Fore.RED + f"{input_tif} is not North-up, need to fix!" + Style.RESET_ALL)
        corrected_path = os.path.join(temp_dir, f"{Path(input_tif).stem}_corrected.tif")
        fix_to_north_up(input_tif, corrected_path)
    else:
        corrected_path = input_tif
    
    try:
        gs.run_command('r.import', input=corrected_path, output=output_map, band=band, overwrite=overwrite, extent=extent, resolution=resolution)
    except Exception as e:
        print(Fore.RED + f"Try to import fail, with error: {e}. Thus we need to reproject and import again" + Style.RESET_ALL)
        current_corrected_path = corrected_path
        corrected_path = os.path.join(temp_dir, f"{Path(current_corrected_path).stem}_reproj.tif")
        reproject_raster(current_corrected_path, corrected_path, target_srs="EPSG:4326")
        gs.run_command('r.import', input=corrected_path, output=output_map, band=band, overwrite=overwrite, extent=extent,resolution=resolution)
        
    print(f"Imported band {band} from {input_tif} as {output_map}")

def extract_band_from_grass(raster_map):
    """
    Extract raster data as a NumPy array along with its NoData value directly using GRASS GIS API.

    Parameters:
        raster_map (str): Name of the GRASS raster map to extract.

    Returns:
        numpy.ndarray: The extracted raster data as a NumPy array.
        float or None: The NoData value associated with the raster (None if not defined).
    """
    # Load the raster map as a GRASS GIS array
    raster = garray.array()
    raster.read(raster_map)

    # Convert to NumPy array (no modifications)
    data = raster[:]

    # Get NoData value
    nodata_value = raster.null_value

    return data, nodata_value

# CRS 对齐
def align_crs(map1, map2):
    """使用 r.proj 工具将 map2 的 CRS 转换为 map1 的 CRS

    Usage: align_crs("map1_grass", "map2_grass")
    """
    gs.run_command('r.proj', input=map2, location=map1)
    print(f"Aligned CRS of {map2} to {map1}")

# 分辨率对齐
def align_resolution(map1, map2, map2_output):
    """通过 r.resample 将 map2_grass 的分辨率调整为与 map1_grass 相同：
    Usage: align_resolution("map1_grass", "map2_grass")
    """
    # 获取 map1 的分辨率（假设 map1 已经按所需分辨率对齐）
    resolution = gs.parse_command('r.info', map=map1)['res']

    # 使用 r.resample 工具调整 map2 的分辨率
    gs.run_command('r.resample', input=map2, output=map2_output, resolution=resolution)
    print(f"Aligned resolution of {map2} to {map1} with result name {map2_output}")

# 对齐范围 (Extent)：确保两个栅格地图的范围一致，可以使用 r.region 设置范围，然后将第二个栅格地图的范围调整为第一个栅格地图的范围
def align_extent(map1, map2, map2_output):
    # 获取 map1 的范围
    gs.run_command('r.region', raster=map1)

    # 使用 r.resample 工具将 map2 的范围调整为 map1 的范围
    gs.run_command('r.resample', input=map2, output=map2_output)
    print(f"Aligned extent of {map2} to {map1} with result name {map2_output}")

# align two tiles to the same CRS, resolution and extent
def align_tiles(tile1_path, tile2_path, tile1_band=1, tile2_band=1):
    # import tiffs
    imported_tile1 = Path(tile1_path).stem + f"_band{tile1_band}_grass"
    imported_tile2 = Path(tile2_path).stem + f"_band{tile2_band}_grass"
    import_tif_to_grass(tile1_path, imported_tile1, tile1_band)
    import_tif_to_grass(tile2_path, imported_tile2, tile2_band)
    # align crs
    align_crs(imported_tile1, imported_tile2)
    # align resolution
    aligned_tile2 = imported_tile2 + "_aligned"
    align_resolution(imported_tile1, imported_tile2, aligned_tile2)
    # align extent
    align_extent_tile2 = aligned_tile2 + "_extent"
    align_extent(imported_tile1, aligned_tile2, align_extent_tile2)
    # load data
    map1_array, nodata1 = extract_band_from_grass(imported_tile1)
    map2_array, nodata2 = extract_band_from_grass(align_extent_tile2)
    return map1_array, map2_array, nodata1, nodata2


# 提取每个样本点在不同栅格图层中的值
def sample_raster(geojson_file, raster_layer, output_csv, sample_method="average"):
    gs.run_command('r.sample', input=raster_layer, points=geojson_file, output=output_csv, method=sample_method)
    
    
# grass_utils.py
import grass.script.setup as gsetup
import grass.script as gs
from contextlib import contextmanager

@contextmanager
def grass_temp_region():
    """
    使用临时 GRASS GIS region 的上下文管理器。
    进入时自动设置临时 region，退出时自动删除临时 region。
    """
    # store the current region settings and installs an atexit
    # handler to recover the current region on script termination
    gisbase, location_name, mapset = os.environ.get('GISDBASE'), os.environ.get('LOCATION_NAME', 'MOLCX'), os.environ.get('MAPSET', 'PERMANENT')
    #print(f"Initial Grass Env: gisbase={gisbase} | location_name={location_name} | mapset={mapset}")
    gsetup.init(gisbase, location_name, mapset)
    gs.use_temp_region()  # 设置临时 region
    try:
        yield
    finally:
        # after making operations using the temporary region,
        # to unset the temporary WIND_OVERRIDE file and remove any 
        # region named by it, it is possible to use del_temp_region
        gs.del_temp_region()  # 清理临时 region
