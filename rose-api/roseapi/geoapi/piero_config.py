import json
from django.http import JsonResponse
from geoapi import models as geoapi_models
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

default_piero_config = {
    "analysis": {
        "clipping_box": {
            "center": {
                "crs": "EPSG:3857",
                "x": 1021198.6979,
                "y": 5697310.3403,
                "z": 10
            },
            "floor_preset": {
                "altitude": 167,
                "floor": 0,
                "size": 2.8
            },
            "size": {
                "x": 20,
                "y": 20,
                "z": 20
            }
        },
        "cross_section": {
            "orientation": 40,
            "pivot": {
                "crs": "EPSG:2154",
                "x": 841913,
                "y": 6517811
            }
        }
    },
    "basemap": {
        "colormap": {
            "max": 90,
            "min": 0,
            "mode": 2,
            "ramp": "Greys"
        },
        "extent": {
            "crs": "EPSG:3857",                   
            "east": 1119038.0941,
            "north": 5789646.2704,
            "south": 5623319.2969,
            "west": 932531.7451
        },
        "graticule": {
            "color": "white",
            "enabled": False,
            "thickness": 10,
            "xStep": 1000,
            "yStep": 1000
        },
        "layers": [
            {
                "name": "OpenStreetMap",
                "source": {
                    "type": "osm"
                },
                "type": "color",
                "visible": True
            }
        ]
    },
    "bookmarks": [],
    "camera": {
        "lookAt": {
            "crs": "EPSG:3857",
            "x": 1022101,
            "y": 5694787,
            "z": 0
        },
        "position": {
            "crs": "EPSG:3857",
            "x": 1022101,
            "y": 5691787,
            "z": 5000
        }
    },
    "crs_definitions": {
        "EPSG:3857":
            "+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs +type=crs",
        "EPSG:4326": "+proj=longlat +datum=WGS84 +no_defs +type=crs"
    },

    "datasets": [],

    "default_crs": "EPSG:3857",
    "enabled_features": [],
    "importedVectorDatasetRendering": "overlay", 
    "overlays": []
}

@csrf_exempt
@require_http_methods(["GET", "POST"])
def serve_json_file(request):
    if request.method == "GET":
        rose_config = geoapi_models.GeoAPIConfiguration.objects.all().first()
        print(rose_config)
        piero_config = rose_config.piero_config if rose_config and rose_config.piero_config else default_piero_config

        piero_config_json = json.dumps(piero_config)

        # file_path = "/home/user/Desktop/JP/fast-urban-dt-prototyper/fast-urban-dt-prototyper/piero-conf.json"
        # with open(file_path, 'r') as f:
        #     data = json.load(f) 
        
        return JsonResponse(piero_config)
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)

        rose_config = geoapi_models.GeoAPIConfiguration.objects.all().first()
        print(rose_config)
        if not rose_config:
            return JsonResponse({"status": "error", "message": "No Configuration."}, status=500)
        else:
            rose_config.piero_config = data
            rose_config.save()

        return JsonResponse({"status": "success", "message": "Configuration saved successfully."})

    else:
        return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)


        

    

    
