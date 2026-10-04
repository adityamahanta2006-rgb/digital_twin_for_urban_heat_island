import shapely
import datetime
import json
import os

from downloader import basic_downloader, building_downloader
from street_network_download import download_street_network
from download_utils import coordinates

from dotenv import load_dotenv

if __name__ == "__main__":

    key = "gee-key.json"
    dw = basic_downloader.GEEDownloader(key_path=key)
    b_dw = building_downloader.BuildingDownloader()
    street_dw = download_street_network.StreetNetworkDownloader()

    # Determine if using the local environment file for running locally
    load_dotenv(override=True)
    dest_dir = "/data_dir/data"

    # if is_running_in_docker == 1:
    # else:
        # "/home/user/Desktop/JP/fast-urban-dt-prototyper/fast-urban-dt-prototyper/udt-assembler/data"
        # dest_dir = os.getenv('HOST_STORAGE_DIR', "/")
    city_name = os.getenv('URBAN_AREA_NAME', "Urban Area")

    extent = os.getenv('EXTENT', None)
    if extent is None:
        raise ValueError("EXTENT variable not set in environment.")
    
    # ensure destination and common subfolders exist
    # os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "building_data"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "street_networks", "graph"), exist_ok=True)
    os.makedirs(os.path.join(dest_dir, "street_networks", "shp"), exist_ok=True)

    extent = extent.split(",")
    bbox = [float(coord) for coord in extent]
    # min_x, min_y, max_x, max_y
    # bbox = [11.20334558240936, 44.44566160614209, 11.447334767165243, 44.55593795106484] # Bologna
    # bbox = [8.978462375987206, 45.357641115672706, 9.428737378385136, 45.75547017266898] # milan
    # polygon_bbox = coordinates.bbox_to_polygon(44.44566160614209, 44.55593795106484, 11.20334558240936, 11.447334767165243)
    polygon_bbox = coordinates.bbox_to_polygon(bbox[1], bbox[3], bbox[0], bbox[2])

    info = { # DEM
        "year": 2025,
        "map_name": "NASADEM",
        "map_year": 2025,
        "type": "GEE",
        "url": "NASA/NASADEM_HGT/001",
        "aoi": polygon_bbox,
        "gee_collection_extract_method": "SINGLE", 
        "scale": 30,
        "bands": ['elevation'],
        "output_name": "dem.tif"
    }
    dw.download_only_cloud(info, dest_dir)
    metadata = {
        "name": "dem",
        "title": "NASADEM Digital Elevation Model",
        "location": f"data/dem.tif"
    }
    with open(f'{dest_dir}/dem.metadata', "w") as meta_file:
        json.dump(metadata, meta_file)   
    print("DEM downloaded and saved")
    print("-------")


    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
    print(f"From {start_date} to {end_date}")
    info = { # Land Cover Dynamic World mosaic
        "map_name": "LandCover Dynamic World",
        "year": 2025,
        "map_year": 2025,
        "start_date": start_date,
        "end_date": end_date,
        "type": "GEE",
        "url": "GOOGLE/DYNAMICWORLD/V1",
        "aoi": polygon_bbox,
        "gee_collection_extract_method": "MOSAIC", 
        "gee_collection_reducer": "MODE",
        "scale": 10,
        'bands': ['label'],
        "output_name": "landcover_dynamic_world.tif"
    }
    dw.download_only_cloud(info, dest_dir)
    metadata = {
        "name": "landcover_dynamic_world",
        "title": "Dynamic World Landcover",
        "location": f"data/landcover_dynamic_world.tif"
    }
    with open(f'{dest_dir}/landcover_dynamic_world.metadata', "w") as meta_file:
        json.dump(metadata, meta_file)   
    print("Land Cover Dynamic World downloaded and saved")
    print("-------")

    info = { # Land Cover Copernicus
        "year": 2019,
        "map_name": "LandCover Copernicus",
        "map_year": 2019,
        "type": "GEE",
        "url": "COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019",
        "aoi": polygon_bbox,
        "gee_collection_extract_method": "SINGLE", 
        "scale": 100,
        'bands': ['discrete_classification'],
        "output_name": "landcover_copernicus.tif"
    }
    dw.download_only_cloud(info, dest_dir)
    metadata = {
        "name": "landcover_copernicus",
        "title": "Copernicus Landcover",
        "location": f"data/landcover_copernicus.tif"
    }
    with open(f'{dest_dir}/landcover_copernicus.metadata', "w") as meta_file:
        json.dump(metadata, meta_file)   
    print("Land Cover Copernicus downloaded and saved")
    print("-------")

    info = { # Land Cover GHS
        "year": 2018,
        "map_name": "LandCover GHS",
        "map_year": 2018,
        "type": "GEE",
        "url": "JRC/GHSL/P2023A/GHS_BUILT_C/2018",
        "aoi": polygon_bbox,
        "gee_collection_extract_method": "SINGLE", 
        "export_projection": "EPSG:6326",
        "scale": 10,
        'bands': ['built_characteristics'],
        "output_name": "landcover_urban.tif"
    }
    dw.download_only_cloud(info, dest_dir)
    metadata = {
        "name": "landcover_urban",
        "title": "Urban Landcover (GSH)",
        "location": f"data/landcover_urban.tif"
    }
    with open(f'{dest_dir}/landcover_urban.metadata', "w") as meta_file:
        json.dump(metadata, meta_file)   
        
    print("Land Cover GHS downloaded and saved")
    print("-------")

    info = { # Population
        "year": 2025,
        "map_name": "GHS Population",
        "map_year": 2025,
        "type": "GEE",
        "url": "JRC/GHSL/P2023A/GHS_POP/2025",
        "aoi": polygon_bbox,
        "gee_collection_extract_method": "SINGLE", 
        "scale": 100,
        'bands': ['population_count'],
        "output_name": "population.tif"
    }

    # check if the file already exists
    
    dw.download_only_cloud(info, dest_dir)
    metadata = {
        "name": "population",
        "title": "Population Counts",
        "location": f"data/population.tif"
    }
    with open(f'{dest_dir}/population.metadata', "w") as meta_file:
        json.dump(metadata, meta_file)   

    print("Population downloaded and saved")
    print("-------")

    buildings_output_path_metadata = f'{dest_dir}/buildings_2d.metadata'
    if not os.path.exists(buildings_output_path_metadata):
        building_data_path = f'/udt_assembler/downloader/building_download_data'
        dataset_type = os.getenv('BUILDING_DATASET', 'globfp')  # Options: globfp, microsoft
        buildings_dest_dir = f'{dest_dir}/building_data'
        # building_data_path = "/home/user/Desktop/JP/fast-urban-dt-prototyper/fast-urban-dt-prototyper/udt-assembler/downloader/building_download_data"
        b_dw.download(info={ # Building data
            "mode": dataset_type,
            "bbox": bbox,
            "data_path": building_data_path,
            "crs": "EPSG:4326"
        }, dest_dir=buildings_dest_dir)
        print("3D building data downloaded and saved")
        try:
            metadata = {
                "name": "buildings_2d",
                "title": "Building Footprints 2D",
                "location": f"data/building_data/buildings_2d.shp"
            }
            with open(f'{dest_dir}/buildings_2d.metadata', "w") as meta_file:
                json.dump(metadata, meta_file)

            metadata = {
                "name": "buildings_3d",
                "title": "Buildings 3D",
                "location": f"data/building_data/buildings_3d.geojson"
            }
            with open(f'{dest_dir}/buildings_3d.geojson', "w") as meta_file:
                json.dump(metadata, meta_file)
        except Exception as e:
            print(e)
    else:
        print(f"Buildings already exists. Skipping download.")

    print("-------")

    
    network_data_base_path = dest_dir
    info = { # Street Network
        "geometry": shapely.geometry.box(*bbox),
        "name": city_name,
        "data_base_path": network_data_base_path
    }
    
    modes = ["bike_network", "drive_network", "walk_network", "public_transport_network"]
    download_modes = []
    for mode in modes:
        mode_st_net_output_path_metadata = f'{dest_dir}/{mode}.metadata'
        if not os.path.exists(mode_st_net_output_path_metadata):
            if mode == "walk_network": download_modes.append("PEDESTRIAN")
            elif mode == "bike_network": download_modes.append("CYCLING")
            elif mode == "drive_network": download_modes.append("DRIVING")
            elif mode == "public_transport_network": download_modes.append("PUBLIC_TRANSPORT")

        
    
    street_dw.download(info=info, dest_dir=dest_dir, modes=download_modes)
    print("Street Networks downloaded and saved")
    for mode in modes:
        try:
            metadata = {
                "name": f"{mode}",
                "title": f"{mode}".capitalize(),
                "location": f"data/street_networks/graph/{mode}.graphml"
            }
            with open(f'{dest_dir}/{mode}.metadata', "w") as meta_file:
                json.dump(metadata, meta_file)
        except Exception as e:
            print(e)
    print("-------")



