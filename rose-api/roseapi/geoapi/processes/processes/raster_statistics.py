import shapely
import json
import rasterio
import numpy as np

from geoapi import metadata_manager 
from geoapi.processes.utils import BaseProcess
from geoapi.processes import utils
from geoapi.processes.job_manager import JobManager
from shapely.geometry import mapping
from rasterio.warp import transform_geom
from rasterio.transform import array_bounds
import rasterio.mask
from shapely.ops import unary_union
from shapely.ops import transform
import pyproj

class Process(BaseProcess):
    def __init__(self):
        self.id = "raster-statistics"
        self.version = "1.0"
        
        self.title = "Raster Statistics"
        self.description = "Calculation of raster statistics based on datasets uploaded"
        self.keywords = [
            "ogc api",
            "processes",
            "taster stats"
        ]
        self.jobControlOptions = [
            "sync-execute",
            "async-execute"
        ]
        self.outputTransmission = [
            "value"
        ]

        self.inputs = {
            # All the metadata for the inputs received by the system
            "raster-name": {
                "title":"Raster dataset name",
                "description":'The title of the raster dataset to calculate',
                "type": str,
                "minOccurs": 1,
                "maxOccurs": 1,
                "options": ["DEM", "Land Cover Copernicus", "Dynamic Land Cover", "Urban Land Cover", "Population"]
            },

            # "band": {
            #     "title":"Optional - Band",
            #     "description":'Optional band to calculate the stats. If not provided, the first band will be used',
            #     "type": int,
            #     "minOccurs": 0,
            #     "maxOccurs": 1,
            #     "options": None
            # },

            "categories": {
                "title":"Optional - List of raster categories",
                "description":'Optional list of categories to calculate stats from',
                "type": list[str],
                "minOccurs": 0,
                "maxOccurs": 1,
                "options": None
            },

            "geometry": {
                "title":"Geometry of the urban area to calculate the raster statistics",
                "description":'Geometry of the urban area to calculate. The same geometry is returned with the data',
                "type": str,
                "minOccurs": 1,
                "maxOccurs": 1,
                "options": None
            },
        }

        self.outputs = {
            "raster-stats": {
                "title": "Raster Statistics for area of interest",
                "description": 'GeoJSON object with raster statistics calculated',
                "type": object,
                "format": { "mediaType": "application/geo+json" },
            }
        }

    def main(self, input: object):
        """
        The process main execution function.
        """

        def map_raster_type(raster_type:str) -> str:
            if raster_type == "DEM": return "dem"
            if raster_type == "Land Cover Copernicus": return "landcover_copernicus"
            if raster_type == "Dynamic Land Cover": return "landcover_dynamic_world"
            if raster_type == "Urban Land Cover": return "landcover_urban"
            if raster_type == "Population": return "population"

        job_manager = JobManager()

        # read inputs
        raster_type = input['raster-name']
        geometry = input['geometry']
        categories = input['categories']
        if categories is None or len(categories) == 0: categories = []

        # Validate network type
        if raster_type not in list(self.inputs["raster-name"]["options"]):
            raise Exception("Raster Layer not supported")
        
        # Load the area of interest
        geom_geojson = geometry
        geom_geojson = json.loads(geom_geojson)
        if "features" in geom_geojson:
            geom_geojson = geom_geojson["features"][0]
        geom_geojson = json.dumps(geom_geojson)
        geom = shapely.from_geojson(geom_geojson)

        try:
            # Convert to 3857 for area calculation
            wgs84 = pyproj.CRS('EPSG:4326')
            cartesian = pyproj.CRS('EPSG:3857')
            project = pyproj.Transformer.from_crs(wgs84, cartesian, always_xy=True).transform

            geom_m = transform(project, geom) 
            area = geom_m.area / 1000000 # m2 to km2
            if area == 0:
                raise Exception("Geometry area is zero")
            
        except Exception as ex:
            raise Exception("Invalid Geometry")
        
        job_manager.update_job_progress(self.job_id, 10)

        raster_type =  map_raster_type(raster_type)
        raster_metadata = metadata_manager.FileStorageMetadata.objects.all().filter(dataset_name=raster_type).first()
        base_data_path = utils.get_data_storage_base_path()
        raster_location = f'{base_data_path}/{raster_metadata.path}'

        # update progress
        job_manager.update_job_progress(self.job_id, 30)

        # Open raster and mask with geometry
        with rasterio.open(raster_location) as src:
            if src.crs is None:
                raise Exception("Raster has no CRS")

            # Convert shapely geometry to geojson mapping and reproject to raster CRS (assume input geom in EPSG:4326)
            uni_geom = unary_union([geom])
            geom_mapping = mapping(uni_geom)

            dst_crs = src.crs.to_string() if hasattr(src.crs, "to_string") else str(src.crs)
            try:
                geom_in_raster_crs = transform_geom("EPSG:4326", dst_crs, geom_mapping, precision=6)
            except Exception:
                # If transform fails, try using geometry as-is (best-effort)
                geom_in_raster_crs = geom_mapping

            print(geom_in_raster_crs)
            out_image, out_transform = rasterio.mask.mask(src, [geom_in_raster_crs], all_touched=False, crop=True, filled=True)
            job_manager.update_job_progress(self.job_id, 50)

            # Compute array bounds for the cropped window (minx, miny, maxx, maxy)
            height = out_image.shape[1]
            width = out_image.shape[2]
            minx, miny, maxx, maxy = array_bounds(height, width, out_transform)

            band = out_image[0]

            # Create a masked array handling rasterio's masked output or nodata values
            if np.ma.isMaskedArray(band):
                masked = band
            else:
                nodata = src.nodata
                if nodata is not None:
                    masked = np.ma.masked_equal(band, nodata)
                else:
                    masked = np.ma.masked_invalid(band)

            count = int(masked.count())

            # Assemble result object
            raster_stats = {
                "raster": raster_type,
                "area_km2": area,
                "count": count,
                "min": float(masked.min()),
                "max": float(masked.max()),
                "mean": float(masked.mean()),
                "median": float(np.ma.median(masked)),
                "std": float(masked.std()),
                "sum": float(masked.sum())
            }

            for category in categories:
                # Determine mask and underlying data
                print(category)
                mask_cat = np.where(band == int(category), 1, 0).astype("uint8")

                cat_count = int(np.count_nonzero(mask_cat))
                total_valid = count if count > 0 else 0
                percentage = (cat_count / total_valid * 100.0) if total_valid > 0 else 0.0

                # Store percentage for the category (keyed by the category value as string)
                raster_stats[f"{category}_percentage"] = float(percentage)

            # Build a GeoJSON GeometryCollection from the shapely geometry and attach raster stats as properties
            geom_mapping_local = mapping(geom)

            if geom_mapping_local.get("type") == "GeometryCollection":
                geom_collection = geom_mapping_local
            else:
                geom_collection = {
                    "type": "GeometryCollection",
                    "geometries": [geom_mapping_local]
                }

            raster_stats_feature = {
                "type": "Feature",
                "geometry": geom_collection,
                "properties": raster_stats
            }

            # Replace raster_stats variable with the GeoJSON Feature for downstream use
            raster_stats = raster_stats_feature

            job_manager.update_job_progress(self.job_id, 100)

        return {
            "raster-stats": raster_stats
        }
    
    def __str__(self) -> str:
        return f'{self.title} - {self.description}'