############ Based on rasterio ############
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box

# align two tiles to the same CRS, resolution and extent
def align_tiles(tile1_path, tile2_path, tile1_band=1, tile2_band=1):
    with rasterio.open(tile1_path) as src1, rasterio.open(tile2_path) as src2:
        # Set the target CRS and calculate common transform and dimensions. CRS of tile1 is selected as the target CRS.
        dst_crs = src1.crs
        transform, width, height = calculate_default_transform(
            src2.crs, dst_crs, src2.width, src2.height, *src2.bounds
        )
        
        # Create arrays to hold the aligned data
        data1_aligned = np.empty((height, width), dtype=src1.meta['dtype'])
        data2_aligned = np.empty((height, width), dtype=src2.meta['dtype'])
        
        # Reproject tile1
        reproject(
            source=rasterio.band(src1, tile1_band),
            destination=data1_aligned,
            src_transform=src1.transform,
            src_crs=src1.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )
        
        # Reproject tile2
        reproject(
            source=rasterio.band(src2, tile2_band),
            destination=data2_aligned,
            src_transform=src2.transform,
            src_crs=src2.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )
        
        # Get NoData values
        nodata1 = src1.nodata
        nodata2 = src2.nodata

    return data1_aligned, data2_aligned, nodata1, nodata2


# 定义验证方法，检查 CRS、分辨率和范围，并可选择保存对齐后的文件
def verify_alignment(data1, data2, transform, src1_path, src2_path, save_aligned=False):
    with rasterio.open(src1_path) as src1, rasterio.open(src2_path) as src2:
        # 检查 CRS
        assert src1.crs == src2.crs, f"CRS alignment failed: {src1.crs} != {src2.crs}"
        print("CRS alignment successful.")

        # 检查分辨率
        res1, res2 = src1.transform[0], src2.transform[0]
        assert res1 == res2, f"Resolution alignment failed: {res1} != {res2}"
        print("Resolution alignment successful.")

        # 检查范围（宽度和高度）
        assert data1.shape == data2.shape, f"Extent alignment failed: {data1.shape} != {data2.shape}"
        print("Extent alignment successful.")
        
        # 可选：将对齐后的栅格保存为 TIFF 文件
        if save_aligned:
            meta = src1.meta.copy()
            meta.update({
                "driver": "GTiff",
                "height": data1.shape[0],
                "width": data1.shape[1],
                "transform": transform
            })
            
            with rasterio.open("aligned_tile1.tif", "w", **meta) as dest1:
                dest1.write(data1, 1)
            with rasterio.open("aligned_tile2.tif", "w", **meta) as dest2:
                dest2.write(data2, 1)
            print("Aligned tiles saved as 'aligned_tile1.tif' and 'aligned_tile2.tif' for visual verification.")


# extract value from raster file for input points
def extract_point_values(gdf, raster_path, target_col_name):
    with rasterio.open(raster_path) as src:
        #print("NODATA:", src.nodata)
        nodata = src.nodata
        # 确保点和 raster 的 CRS 一致
        if gdf.crs != src.crs:
            gdf = gdf.to_crs(src.crs)
        # 提取 raster 上的值
        coords = [(geom.x, geom.y) for geom in gdf.geometry]
        sampled_vals = list(src.sample(coords))
        gdf[target_col_name] = [val[0] for val in sampled_vals]
        return gdf, nodata

# filter points within reference raster file
def get_points_within_raster(gpkg_path, gpkg_layer, ref_raster_path):
    # load points
    gdf = gpd.read_file(gpkg_path, layer=gpkg_layer)
    if gdf.crs is None:
        raise ValueError("GPKG 文件未定义坐标系。")
    
    # read raster
    with rasterio.open(ref_raster_path) as src:
        raster_geom = box(*src.bounds)
        raster_crs = src.crs
        raster_gdf = gpd.GeoDataFrame(geometry=[raster_geom], crs=raster_crs)
        # reproject points to raster
        if gdf.crs != raster_gdf.crs:
            points_gdf = points_gdf.to_crs(raster_gdf.crs)
        
    # filter
    filtered_points = points_gdf[points_gdf.within(raster_geom)]
    #print(f"total {filtered_points.shape[0]} points\n", filtered_points.head())
    return filtered_points