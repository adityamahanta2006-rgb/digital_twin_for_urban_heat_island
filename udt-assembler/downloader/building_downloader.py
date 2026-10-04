import geopandas as gpd
import pandas as pd
import shapely
import json
import requests
import zipfile
import os
import gzip
import shutil
from typing import List, Tuple

class BuildingDownloader():
    def __init__(self):
        pass

    def download(self, info: dict, dest_dir: str) -> str:
        print("Downloading buildings...")
        mode = info.get('mode', 'globfp')
        bbox = info.get('bbox', None)  # Default to global if not provided
        data_path = info.get('data_path', './building_download_data/')
        crs = info.get('crs', 'EPSG:4326')
        print(data_path)

        if bbox is None:
            raise ValueError("Bounding box (bbox) must be provided in info dictionary.")

        if mode == 'globfp':
            world_grid_path = f"{data_path}/3D-GloBFP/world_grid.geojson"
            links_path = f"{data_path}/3D-GloBFP/all_links.json"
            height_field = "Height"
            grid_ID_field = "grid_ID"

        elif mode == 'microsoft':
            world_grid_path = f"{data_path}/microsoft_buildings/world_grid.geojson"
            links_path = f"{data_path}/microsoft_buildings/all_links.json"
            height_field = "height"
            grid_ID_field = "id"

        else:
            world_grid_path = f"{data_path}/3D-GloBFP/world_grid.geojson"
            links_path = f"{data_path}/3D-GloBFP/all_links.json"
            height_field = "Height"
            grid_ID_field = "grid_ID"

        # Download buildings
        bbox = shapely.geometry.box(*bbox)
        # Read the world grid shapefile to find the tile ID
        world_grid = gpd.read_file(world_grid_path)

        # Obtain the tile to download the buildings from
        grid_ids = world_grid.loc[world_grid.intersects(bbox)]
        print(grid_ids)

        # for testing
        # grid_ids = grid_ids[0:1]

        print(f"Downloading {len(grid_ids)} tiles")
        download_links = json.load(open(links_path))
        download_link = None
        for idx, row in grid_ids.iterrows():
            grid_id = row[grid_ID_field]
            for d in download_links:
                if str(grid_id) == str(d["id"]):
                    print("found")

                    download_link = d['download_url']
                    break

            # Download the data
            os.makedirs(f"{data_path}/temp/building_data", exist_ok=True)
            if mode == 'globfp':
                response = requests.get(download_link)
                with open(f"{data_path}/temp/downloaded_file.zip", "wb") as f:
                    f.write(response.content)
                print("Building data downloaded and saved")

                # extract file
                with zipfile.ZipFile(f"{data_path}/temp/downloaded_file.zip", 'r') as zip_ref:
                    zip_ref.extractall(f"{data_path}/temp/building_data")
                print("Building data extracted")
                
            elif mode == 'microsoft':
                print(download_link)
                response = requests.get(download_link)
                with open(f"{data_path}/temp/downloaded_file.csv.gz", "wb") as f:
                    f.write(response.content)
                print("Building data downloaded and saved")

                feature_collection = {"type":"FeatureCollection", "features": []}

                with gzip.open(f"{data_path}/temp/downloaded_file.csv.gz", "rt") as f:
                    for line in f:
                        feature_collection["features"].append(json.loads(line.strip()))


                gdf = gpd.GeoDataFrame.from_features(feature_collection)
                gdf.to_file(f"{data_path}/temp/building_data/buildings_{grid_id}.shp")
                
            else:
                raise ValueError(f"Unsupported mode: {mode}")

        # List the file contents
        files = os.listdir(f"{data_path}/temp/building_data")
        files_set = set()

        # In case there are multiple shapefiles, add them to a set to they get added only once
        for f in files:
            if "shp" in f:
                files_set.add(f)
        files_list = list(files_set)
        print("Shapefiles found:", files_list)

        # Clip the buildings to the area of interest and make a single buildings file
        all_buildings = gpd.GeoDataFrame()
        for f in files_list:
            buildings = gpd.read_file(f"{data_path}/temp/building_data/{f}", bbox=bbox)
            all_buildings = pd.concat([all_buildings, buildings], ignore_index=True)

        all_buildings.crs = "epsg:4326"
        all_buildings.reset_index(drop=True, inplace=True)
        all_buildings.to_file(f"{dest_dir}/buildings_2d.shp")

        print("Buildings clipped to area of interest and saved")
        
        def extrude_polygon(polygon: shapely.Polygon, height: float) -> List[List[Tuple[float, float, float]]]:
            """Extrude 2D shapely Polygon to 3D mesh (list of faces)."""
            if not polygon.is_valid:
                return None

            faces = []
            bottom = [(x, y, 0.0) for x, y in polygon.exterior.coords]
            top = [(x, y, height) for x, y in polygon.exterior.coords]
            faces += [bottom, top[::-1]]

            coords = list(polygon.exterior.coords)
            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                faces.append([
                    (x1, y1, 0.0),
                    (x2, y2, 0.0),
                    (x2, y2, height),
                    (x1, y1, height),
                ])

            for interior in polygon.interiors:
                hole_coords = list(interior.coords)
                faces.append([(x, y, 0.0) for x, y in hole_coords])
                faces.append([(x, y, height) for x, y in hole_coords][::-1])
                for i in range(len(hole_coords) - 1):
                    x1, y1 = hole_coords[i]
                    x2, y2 = hole_coords[i + 1]
                    faces.append([
                        (x1, y1, 0.0),
                        (x2, y2, 0.0),
                        (x2, y2, height),
                        (x1, y1, height),
                    ])
            return faces



        """Convert polygons in GeoDataFrame to extruded 3D GeoJSON."""
        features = []
    
        # Extrude buildings to 3D using the height field
        h_field = height_field

        default_height = 10.0  # Default height if not specified in data
        for idx, row in all_buildings.iterrows():
            poly = row["geometry"]
            height = float(row[h_field]) if h_field and h_field in row else default_height
            faces = extrude_polygon(poly, height)
            if faces is None:
                continue

            for face in faces:
                if face[0] != face[-1]:
                    face = face + [face[0]]

                features.append({
                    "type": "Feature",
                    "properties": {**row.drop(labels="geometry").to_dict(), "height": height},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[list(c) for c in face]]
                    }
                })

        geojson = {
            "type": "FeatureCollection", 
            "crs": { "type": "name", "properties": { "name": "EPSG:4326" } }, 
            "features": features
        }

        # Export as 3D GeoJSON
        with open(f"{dest_dir}/buildings_3d.geojson", "w", encoding="utf-8") as f:
            json.dump(geojson, f, indent=2)

        print(f"3D Buildings saved to {dest_dir}/buildings_3d.geojson")

        # clean up temp files
        shutil.rmtree(f"{data_path}/temp", ignore_errors=True)

        return None
    
    def is_exist(self, info: dict) -> bool:
        pass