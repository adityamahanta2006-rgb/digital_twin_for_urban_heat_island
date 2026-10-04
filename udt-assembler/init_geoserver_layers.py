import requests
import os
from requests.auth import HTTPBasicAuth

from dotenv import load_dotenv

if __name__ == "__main__":

    load_dotenv(override=True)
    dest_dir = "/data_dir/data"

    GEOSERVER_URL = "http://geoserver:8080/geoserver/rest"

    geoserver_username = os.getenv("GEOSERVER_ADMIN_USER", "admin")
    geoserver_password = os.getenv("GEOSERVER_ADMIN_PASSWORD", "geoserver123") 
    AUTH = HTTPBasicAuth(geoserver_username, geoserver_password) 

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    username = os.getenv("UDTDB_USER", "udt")
    password = os.getenv("UDTDB_PASSWORD", "userudt")
    database = os.getenv("UDTDB_DB", "udt_data")

    print(host, port, database, username)

    # hardcoded to default PostGIS connection parameters
    db_connection_params = {
        "host": host,
        "port": port,
        "database": database,
        "user": username,
        "schema": "public",
        "passwd": password,
        "dbtype": "postgis",
    }

    def create_workspace(name: str):
        url = f"{GEOSERVER_URL}/workspaces"
        payload = {"workspace": {"name": name}}
        r = requests.post(url, json=payload, auth=AUTH)
        if r.status_code not in (200, 201):
            print(f"⚠️ Workspace may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Workspace '{name}' created")

    def create_store(workspace: str, store_name: str):
        url = f"{GEOSERVER_URL}/workspaces/{workspace}/datastores"
        payload = {
            "dataStore": {
                "name": store_name,
                "type": "PostGIS",
                "enabled": True,
                "connectionParameters": db_connection_params,
            }
        }
        r = requests.post(url, json=payload, auth=AUTH)
        # r.raise_for_status()
        if r.status_code not in (200, 201):
            print(f"⚠️ Store may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Store '{store_name}' created in workspace '{workspace}'")

    def create_vector_store(workspace: str, store_name: str, file_path: str):
        url = f"{GEOSERVER_URL}/workspaces/{workspace}/datastores"
        payload = {
            "dataStore": {
                "name": store_name,
                "type": "Shapefile",
                "enabled": True,
                "connectionParameters": {
                    "entry": [
                        { "key": "url", "value": file_path },
                        { "key": "charset", "value": "UTF-8" },
                        { "key": "create spatial index", "value": "true" },
                        { "key": "memory mapped buffer", "value": "false" },
                        { "key": "cache and reuse memory maps", "value": "true" }
                    ]
                }
            }
        }
        r = requests.post(url, json=payload, auth=AUTH)
        # r.raise_for_status()
        if r.status_code not in (200, 201):
            print(f"⚠️ Store may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Store '{store_name}' created in workspace '{workspace}'")

    def create_raster_store(workspace: str, store_name: str, file_path: str):
        url = f"{GEOSERVER_URL}/workspaces/{workspace}/coveragestores"
        payload = {
            "coverageStore": {
                "name": store_name,
                "type": "GeoTIFF",  # or "WorldImage", "NetCDF", etc.
                "enabled": True,
                "workspace": workspace,
                "url": file_path,  # Example: "file:data/dem.tif"
            }
        }
        r = requests.post(url, json=payload, auth=AUTH)
        # r.raise_for_status()
        if r.status_code not in (200, 201):
            print(f"⚠️ Store may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Store '{store_name}' created in workspace '{workspace}'")

    def publish_layer(workspace: str, store_name: str, layer_name: str, title, native_crs="EPSG:3857"):
        url = f"{GEOSERVER_URL}/workspaces/{workspace}/datastores/{store_name}/featuretypes"
        payload = {
            "featureType": {
                "name": layer_name,
                "nativeName": layer_name,
                "nativeCRS": native_crs,
                "srs": native_crs,
                "title": title,
                "enabled": True,
                "advertised": True,   
            }
        }
        r = requests.post(url, json=payload, auth=AUTH)
        # r.raise_for_status()

        if r.status_code not in (200, 201):
            print(f"⚠️ Layer may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Layer '{workspace}:{layer_name}' published")

    def publish_raster_layer(workspace: str, store_name: str, layer_name: str, title: str, abstract: str):
        url = f"{GEOSERVER_URL}/workspaces/{workspace}/coveragestores/{store_name}/coverages"
        payload = {
            "coverage": {
                "name": layer_name, 
                "title": title,
                "abstract": abstract,
                "defaultInterpolationMethod": "nearest neighbor",
                "description": abstract,
                "enable": True,
                "nativeCRS": "EPSG:4326",
                "srs": "EPSG:3857",
            }
        }

        r = requests.post(url, json=payload, auth=AUTH)
        # r.raise_for_status()

        if r.status_code not in (200, 201):
            print(f"⚠️ Layer may already exist: {r.status_code} {r.text}")
        else:
            print(f"✅ Layer '{workspace}:{layer_name}' published")
            

    # Start saving data       
    workspace = "udt"
    create_workspace(workspace)

    # Create the PostGIS store
    store_name = "udt_database"
    create_store(workspace, store_name)
    
    # publish pedestrian network layers
    layer_name = "pedestrian_network"
    publish_layer(workspace, store_name, layer_name, "Pedestrian Street Network Edges")
    layer_name = "pedestrian_network_nodes"
    publish_layer(workspace, store_name, layer_name, "Pedestrian Street Network Nodes")
    
    # publish bike network layers
    layer_name = "bike_network"
    publish_layer(workspace, store_name, layer_name, "Cycling Street Network Edges")
    layer_name = "bike_network_nodes"
    publish_layer(workspace, store_name, layer_name, "Cycling Street Network Nodes")

    # publish public transport network layers
    layer_name = "public_transport_network"
    publish_layer(workspace, store_name, layer_name, "Public Transport Network Edges")
    layer_name = "public_transport_network_nodes"
    publish_layer(workspace, store_name, layer_name, "Public Transport Network Nodes")

    # publish road network layers
    layer_name = "road_network"
    publish_layer(workspace, store_name, layer_name, "Road Street Network Edges")
    layer_name = "road_network_nodes"
    publish_layer(workspace, store_name, layer_name, "Road Street Network Nodes")

    # Create the Buildings store
    # create_vector_store(workspace, store_name, "file:data/building_data/buildings_2d.shp")
    # publish 3D Buildings
    layer_name = "buildings_2d"
    publish_layer(workspace, store_name, layer_name, "Buildings Footprints")

    # Publish rasters
    store_name = "dem"
    create_raster_store(workspace, store_name, "file:data/dem.tif")
    abstract = "Digital Terrain Model from NASADEM for the urban area."
    layer_name = "dem"
    layer_title = "Terrain"
    publish_raster_layer(workspace, store_name, layer_name, layer_title, abstract)

    store_name = "landcover_copernicus"
    create_raster_store(workspace, store_name, "file:data/landcover_copernicus.tif")
    abstract = "Copernicus Land Cover at 100m resolution."
    layer_name = "landcover_copernicus"
    layer_title = "Landcover (Copernicus)"
    publish_raster_layer(workspace, store_name, layer_name, layer_title, abstract)

    store_name = "landcover_dynamic_world"
    create_raster_store(workspace, store_name, "file:data/landcover_dynamic_world.tif")
    abstract = "Dynamic World v1 LandCover."
    layer_name = "landcover_dynamic_world"
    layer_title = "Landcover (Dynamic World)"
    publish_raster_layer(workspace, store_name, layer_name, layer_title, abstract)

    store_name = "landcover_urban"
    create_raster_store(workspace, store_name, "file:data/landcover_urban.tif")
    abstract = "Urban Landcover from GHS-BUILT C."
    layer_name = "landcover_urban"
    layer_title = "Landcover (GHS Urban)"
    publish_raster_layer(workspace, store_name, layer_name, layer_title, abstract)

    store_name = "population"
    create_raster_store(workspace, store_name, "file:data/population.tif")
    abstract = "Estimated population counts from GHS-POP 2025."
    layer_name = "population"
    layer_title = "Population (GHS-POP 2025)"
    publish_raster_layer(workspace, store_name, layer_name, layer_title, abstract)


