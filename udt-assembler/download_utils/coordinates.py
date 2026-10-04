
# from coordinates range to bounding box
def bbox_to_polygon(min_lat, max_lat, min_lon, max_lon):
    """
    Parse latitude and longitude ranges in the format "0N-18.5N, 18W-43.5E" 
    and convert them into decimal degrees.

    Args:
    - lat_range (str): Latitude range in format "min_lat-max_lat".
    - lon_range (str): Longitude range in format "min_lon-max_lon".

    Returns:
    - (tuple): Tuple of (min_lat, max_lat, min_lon, max_lon) as floats.
    """
    
    return [[
        [min_lon, min_lat],  # Bottom-left
        [min_lon, max_lat],  # Top-left
        [max_lon, max_lat],  # Top-right
        [max_lon, min_lat],  # Bottom-right
        [min_lon, min_lat]   # Closing the polygon
    ]]

# from coordinates range to bounding box
def coordinate_range_to_bounding_box(lat_range, lon_range):
    """
    Parse latitude and longitude ranges in the format "0N-18.5N, 18W-43.5E" 
    and convert them into decimal degrees.

    Args:
    - lat_range (str): Latitude range in format "min_lat-max_lat".
    - lon_range (str): Longitude range in format "min_lon-max_lon".

    Returns:
    - (tuple): Tuple of (min_lat, max_lat, min_lon, max_lon) as floats.
    """
    # Parse latitudes (N -> positive, S -> negative)
    min_lat_str, max_lat_str = lat_range.split('-')
    min_lat = float(min_lat_str[:-1]) * (-1 if min_lat_str[-1] == 'S' else 1)
    max_lat = float(max_lat_str[:-1]) * (-1 if max_lat_str[-1] == 'S' else 1)
    
    # Parse longitudes (W -> negative, E -> positive)
    min_lon_str, max_lon_str = lon_range.split('-')
    min_lon = float(min_lon_str[:-1]) * (-1 if min_lon_str[-1] == 'W' else 1)
    max_lon = float(max_lon_str[:-1]) * (-1 if max_lon_str[-1] == 'W' else 1)
    
    return [[
        [min_lon, min_lat],  # Bottom-left
        [min_lon, max_lat],  # Top-left
        [max_lon, max_lat],  # Top-right
        [max_lon, min_lat],  # Bottom-right
        [min_lon, min_lat]   # Closing the polygon
    ]]

import geopandas as gpd
# from geojson to bounding box
def get_bounding_box_from_geojson(geojson_path):
    # 读取 GeoJSON 文件
    gdf = gpd.read_file(geojson_path)
    
    # 获取边界框
    bounding_box = gdf.total_bounds
    
    # 提取边界框的坐标
    min_lon, min_lat, max_lon, max_lat = bounding_box
    
    return [[
        [min_lon, min_lat],  # Bottom-left
        [min_lon, max_lat],  # Top-left
        [max_lon, max_lat],  # Top-right
        [max_lon, min_lat],  # Bottom-right
        [min_lon, min_lat]   # Closing the polygon
    ]]

import pandas as pd
from shapely.geometry import Polygon
def bounding2geojson(lon_min, lat_min, lon_max, lat_max, save_to):
    # 创建一个包含边界框的多边形
    bbox_polygon = Polygon([(lon_min, lat_min), (lon_min, lat_max), (lon_max, lat_max), (lon_max, lat_min)])
    
    # 创建一个新的 GeoDataFrame 来存储边界框
    bbox_gdf = gpd.GeoDataFrame(geometry=[bbox_polygon], crs=gdf.crs)
    
    # 将新的 GeoDataFrame 追加到原始的 GeoDataFrame 中
    result_gdf = pd.concat([gdf, bbox_gdf], ignore_index=True)
    
    # 将结果写回到 GeoJSON 文件
    result_gdf.to_file(output_path, driver='GeoJSON')