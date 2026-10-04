import json
import os
from dotenv import load_dotenv
import shapely
import requests
from pyproj import Transformer
import pyproj
from shapely.ops import transform

if __name__ == "__main__":
    zoom_level = 5000
    base_crs = "EPSG:3857"

    load_dotenv(override=True)

    base_geoserver_url = os.getenv("HOST_GEOSERVER_BASE_URL", "http://localhost:8082")
    base_geoserver_url = base_geoserver_url + "/geoserver/ows"

    extent = os.getenv('EXTENT', None)
    if extent is None:
        raise ValueError("EXTENT variable not set in environment.")
    
    extent_crs = os.getenv('EXTENT_CRS', "EPSG:4326")
    extent_4326 = extent

    building_source = os.getenv('BUILDING_DATASET', 'globfp')  # Options: globfp, microsoft
    height_field = "Height" if building_source == 'globfp' else "height" 

    extent = extent.split(",")
    extent = [float(coord) for coord in extent]
    bbox = shapely.geometry.box(*extent)

    # convert bbox geometry from EPSG:4326 to target base_crs (EPSG:3857)
    
    transformer = Transformer.from_crs(extent_crs.lower(), base_crs.lower(), always_xy=True)
    bbox = transform(transformer.transform, bbox)
    extent = [bbox.bounds[0], bbox.bounds[1], bbox.bounds[2], bbox.bounds[3]]
    map_center = bbox.centroid.representative_point().coords[0]

    print(extent)
    print(map_center)

    base_piero_config = {}
    with open('/udt_assembler/base_piero_config.json', 'r') as f:
        base_piero_config = json.load(f)

    base_piero_config['default_crs'] = base_crs

    base_piero_config["basemap"]["extent"] = {
        "crs": "EPSG:3857",  
        "east": extent[2],
        "north": extent[3],
        "south": extent[1],
        "west": extent[0]
    }

    base_piero_config['camera']['position'] = {
        "crs": base_crs,
        "x": map_center[0],
        "y": map_center[1] - 3000,
        "z": zoom_level,
    }

    base_piero_config['camera']['lookAt'] = {
        "crs": base_crs,
        "x": map_center[0],
        "y": map_center[1],
        "z": 0,
    }

    # Add overlay layers
    base_piero_config['overlays'].append({
        "name": "Road Network",
        "source": {
            "format": "image/png",
            "layer": "udt:road_network",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Pedestrian Network",
        "source": {
            "format": "image/png",
            "layer": "udt:pedestrian_network",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Cycling Network",
        "source": {
            "format": "image/png",
            "layer": "udt:bike_network",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Public Transport Stops",
        "source": {
            "format": "image/png",
            "layer": "udt:public_transport_network_nodes",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['datasets'].append({
        "name": "3D Buildings",
        "featureProjection":"EPSG:3857",
        "source": "geojson3d",
        "layerName": "udt:buildings_2d",
        "baseUrl": f"{base_geoserver_url}/geoserver/ows",
        "type": "featureCollection",
        "heightProperty": height_field,
        "elevationProperty": "altitude",
        "elevation": 0,
        "maxLevel": 5,
        "minLevel": 5,
        "extent": {
            "crs": "EPSG:3857",  
            "east": extent[2],
            "north": extent[3],
            "south": extent[1],
            "west": extent[0]
        }
    })

    base_piero_config['overlays'].append({
        "name": "Terrain",
        "source": {
            "format": "image/png",
            "layer": "udt:dem",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Land Cover (Urban)",
        "source": {
            "format": "image/png",
            "layer": "udt:landcover_urban",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Land Cover (Copernicus)",
        "source": {
            "format": "image/png",
            "layer": "udt:landcover_copernicus",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Landcover (Dynamic World)",
        "source": {
            "format": "image/png",
            "layer": "udt:landcover_dynamic_world",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Population",
        "source": {
            "format": "image/png",
            "layer": "udt:population",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })

    base_piero_config['overlays'].append({
        "name": "Building Footprints 2D",   
        "source": {
            "format": "image/png",
            "layer": "udt:buildings_2d",
            "projection": f"{base_crs}",
            "type": "wms",
            "url": f"{base_geoserver_url}/geoserver/ows?service=WMS&version=1.1.1&request=GetCapabilities"
        },
        "visible": False
    })


    LOCAL_UPDATE_PIERO_CONFIG_URL = "http://web:80/api/piero-config"
    try:
        resp = requests.post(
            LOCAL_UPDATE_PIERO_CONFIG_URL,
            json=base_piero_config,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        print("Config updated:", resp.status_code)
        try:
            print(resp.json())
        except ValueError:
            print(resp.text)
    except requests.exceptions.RequestException as e:
        print("Failed to update config:", e)

    LOCAL_UPDATE_METADATA = "http://web:80/api/update-file-metadata"
    try:
        resp = requests.put(
            LOCAL_UPDATE_METADATA,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        print("Metadata Updated:", resp.status_code)
        try:
            print(resp.json())
        except ValueError:
            print(resp.text)
    except requests.exceptions.RequestException as e:
        print("Failed to update metadata:", e)