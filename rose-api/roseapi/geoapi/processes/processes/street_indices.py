import shapely
import json
import osmnx as ox
import networkx as nx
import pandas as pd
import geopandas as geopd
from geoapi.processes.utils import BaseProcess
from street_network_utils import network_extractor
from street_network_utils.indices import graph_based, proximity
from geoapi.processes import utils
from geoapi.processes.job_manager import JobManager
from shapely.ops import transform
import pyproj

class Process(BaseProcess):
    def __init__(self):
        self.id = "street-network-indices"
        self.version = "1.0"
        
        self.title = "Calculation of Street Network Indices"
        self.description = "Example Process description"
        self.keywords = [
            "ogc api",
            "processes",
            "street indices"
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
            "network-type": {
                "title":"The type of network to calculate the indices",
                "description":'The type of network to calculate the indices',
                "type": str,
                "minOccurs": 1,
                "maxOccurs": 1,
                "options": ["pedestrian", "cycling", "road"]
            },

            "geometry": {
                "title":"Geometry of the urban area to calculate as GeoJSON",
                "description":'Geometry of the urban area to calculate',
                "type": str,
                "minOccurs": 1,
                "maxOccurs": 1,
                "options": None
            },

            "return-geometry": {
                "title": "Return the geometry as GeoJSON",
                "description": 'Determine if the street network is returned as a GeoJSON or if the output is left empty.',
                "type": bool,
                "minOccurs": 1,
                "maxOccurs": 1,
                "options": None
            }
        }

        self.outputs = {
            "index-values": {
                "title": "Dictionary with the values of the different indices calculated",
                "description": 'Dictionary with the values of the different indices calculated',
                "type": object,
                "format": { "mediaType": "application/json" },
            }, 

            "street-network": {
                "title": "The street",
                "description": 'Dictionary with the values of the different indices calculated',
                "type": object,
                "format": { "mediaType": "application/geo+json" },
            }
        }

    def main(self, input: object):
        """
        The process main execution function.
        """

        job_manager = JobManager()

        def add_result(results_dict, column, value):
            try:
                results_dict[column].append(value)
            except:
                results_dict[column] = []
                results_dict[column].append(value)

        def filter_graph(g: nx.MultiDiGraph | nx.MultiGraph, aoi: shapely.Polygon) -> nx.MultiDiGraph | nx.MultiGraph:
            # Filter the graph by the area of interest
            remove_edges = []
            for u,v,key,data in g.edges(data=True, keys=True):
                if not data["geometry"].within(aoi):
                    remove_edges.append((u,v,key))
            g.remove_edges_from(remove_edges)
            g.remove_nodes_from(list(nx.isolates(g)))
            return g

        network_type = input['network-type']
        save_network = input['return-geometry']

        # Validate network type
        if network_type not in ["pedestrian", "cycling", "road"]:
            raise Exception("Network Type not supported")

        base_data_path = utils.get_data_storage_base_path() + "/data"
        
        # Load the street networks
        extractor = network_extractor.NetworkExtractor(base_data_path)

        # Load the area of interest
        geometry = input['geometry']
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
            area = geom.area

        results_dict = {"area": area}
        add_result(results_dict, "area", area)

        job_manager.update_job_progress(self.job_id, 10)

        if network_type == 'pedestrian':
            # Indicators using the pedestrian network
            try:
                g_walk = extractor.load_graph(f'street_networks/graph/walk_network')
                g_public = extractor.load_graph(f'street_networks/graph/public_transport_network')    
            except Exception as ex:
                return f'Error loading graphs' 

            # Filter the graph by the area of interest
            g_walk = filter_graph(g_walk, geom)

            job_manager.update_job_progress(self.job_id, 30)

            add_result(results_dict, "number_of_nodes", g_walk.number_of_nodes())
            add_result(results_dict, "number_of_edges", g_walk.number_of_edges())
        
            # walking proximity to pois
            print("starting calculation walk_prox_poi")
            walk_prox_poi_mean, walk_prox_poi_median, walk_prox_poi_range,  walk_prox_poi_std, walk_prox_poi_iqr = proximity.proximity_to_pois(g_walk, geom, walk_time=15, parallelize=True, max_partition_size=5000)
            add_result(results_dict, "walk_prox_poi_mean", walk_prox_poi_mean)
            add_result(results_dict, "walk_prox_poi_median", walk_prox_poi_median)

            # walking proximity to public transport
            walk_prox_pub_transport_mean, walk_prox_pub_transport_median, walk_prox_pub_transport_range, walk_prox_pub_transport_std, walk_prox_pub_transport_iqr = proximity.proximity_to_public_transport(g_walk, g_public, distance=400, parallelize=True, max_partition_size=5000)
            add_result(results_dict, "walk_prox_pub_transport_mean", walk_prox_pub_transport_mean)
            add_result(results_dict, "walk_prox_pub_transport_median", walk_prox_pub_transport_median)

            # Walking Circuity
            walk_circuity = graph_based.circuity(g_walk, add_property=True)
            add_result(results_dict, "walk_circuity", walk_circuity)

            # Walking street length
            walk_st_len_mean, walk_st_len_med, walk_st_len_range, walk_st_len_std, walk_st_len_iqr, walk_st_len_total = graph_based.street_length(g_walk)
            add_result(results_dict, "walk_street_len_mean", walk_st_len_mean)
            add_result(results_dict, "walk_street_len_median", walk_st_len_med)
            add_result(results_dict, "walk_street_density", walk_st_len_total / area)
            add_result(results_dict, "walk_street_len_total", walk_st_len_total)

            # Walking Link-Node ratio
            walk_link_node_ratio = graph_based.link_node_ratio(g_walk)
            add_result(results_dict, "walk_link_node_ratio", walk_link_node_ratio)

            # Walking intersection density
            walk_intersection_density, walk_intersection_count = graph_based.intersection_density(g_walk, area)
            add_result(results_dict, "walk_intersection_density", walk_intersection_density)
            add_result(results_dict, "walk_intersection_count", walk_intersection_count)

            # save the pedestrian graph with indicators attached
            # saver.save_as_shp(g_walk, f'walk_indices_network')
            return_g = g_walk
            
            # free memory
            # del g_walk
            # del g_public

        if network_type == 'cycling':
            # Indicators using the cycling network
            try:
                g_bike = extractor.load_graph(f'street_networks/graph/bike_network')
            except Exception as ex:
                raise Exception("Error loading cycling graph")
            
            # Filter the graph by the area of interest
            g_bike = filter_graph(g_bike, geom)
            
            job_manager.update_job_progress(self.job_id, 30)

            # cycling proximity to POIs
            bike_prox_poi_mean, bike_prox_poi_median, bike_prox_poi_range, bike_prox_poi_std, bike_prox_poi_iqr = proximity.proximity_to_pois(g_bike, geom, walk_time=15, parallelize=True, max_partition_size=5000)
            add_result(results_dict, "bike_prox_poi_mean", bike_prox_poi_mean)
            add_result(results_dict, "bike_prox_poi_median", bike_prox_poi_median)

            # Cycling slope
            bike_slope_mean, bike_slope_median, bike_slope_range, bike_slope_std, bike_slope_iqr = graph_based.steepness(g_bike)
            add_result(results_dict, "bike_slope_mean", bike_slope_mean)
            add_result(results_dict, "bike_slope_median", bike_slope_median)
            
            # Cycling circuity
            bike_circuity = graph_based.circuity(g_bike, add_property=True)
            add_result(results_dict, "bike_circuity", bike_circuity)

            # Cycling street length
            bike_st_len_mean, bike_st_len_med, bike_st_len_range, bike_st_len_std, bike_st_len_iqr, bike_st_len_total = graph_based.street_length(g_bike)
            add_result(results_dict, "bike_street_len_mean", bike_st_len_mean)
            add_result(results_dict, "bike_street_len_median", bike_st_len_med)
            add_result(results_dict, "bike_street_density", bike_st_len_total / area)
            add_result(results_dict, "bike_street_len_total", bike_st_len_total)

            # Cycling Link-Node ratio
            bike_link_node_ratio = graph_based.link_node_ratio(g_bike)
            add_result(results_dict, "bike_link_node_ratio", bike_link_node_ratio)

            # Cycling intersection density
            bike_intersection_density, bike_intersection_count = graph_based.intersection_density(g_bike, area)
            add_result(results_dict, "bike_intersection_density", bike_intersection_density)
            add_result(results_dict, "bike_intersection_count", bike_intersection_count)

            # save the cycling graph with indicators attached
            # saver.save_as_shp(g_bike, f'bike_indices_network')
            return_g = g_bike
            # free memory
            # del g_bike

        if network_type == 'road':
            # Indicators using the driving network
            try:
                g_drive = extractor.load_graph(f'street_networks/graph/drive_network')
            except Exception as ex:
                print(ex)
                raise Exception("Error loading driving graph")
            
            # Filter the graph by the area of interest
            g_drive = filter_graph(g_drive, geom)
            
            job_manager.update_job_progress(self.job_id, 30)

            # Driving orientation entropy
            orientation_entropy = graph_based.orientation_entropy(g_drive)
            add_result(results_dict, "drive_orientation_entropy", orientation_entropy)
            job_manager.update_job_progress(self.job_id, 31)

            # drive proximity to POIs
            drive_prox_poi_mean, drive_prox_poi_median, drive_prox_poi_range, drive_prox_poi_std, drive_prox_poi_iqr = proximity.proximity_to_pois(g_drive, geom, walk_time=10, parallelize=True, max_partition_size=5000)
            add_result(results_dict, "drive_prox_poi_mean", drive_prox_poi_mean)
            add_result(results_dict, "drive_prox_poi_median", drive_prox_poi_median)
            job_manager.update_job_progress(self.job_id, 32)

            # Driving circuity
            drive_circuity = graph_based.circuity(g_drive, add_property=True)
            add_result(results_dict, "drive_circuity", drive_circuity)
            job_manager.update_job_progress(self.job_id, 33)

            # Driving street length
            drive_st_len_mean, drive_st_len_med, drive_st_len_range, drive_st_len_std, drive_st_len_iqr, drive_st_len_total = graph_based.street_length(g_drive)
            add_result(results_dict, "drive_street_len_mean", drive_st_len_mean)
            add_result(results_dict, "drive_street_len_median", drive_st_len_med)
            add_result(results_dict, "drive_street_density", drive_st_len_total / area)
            add_result(results_dict, "drive_street_len_total", drive_st_len_total)
            job_manager.update_job_progress(self.job_id, 34)

            # Driving Link-Node ratio
            drive_link_node_ratio = graph_based.link_node_ratio(g_drive)
            add_result(results_dict, "drive_link_node_ratio", drive_link_node_ratio)
            job_manager.update_job_progress(self.job_id, 35)

            # Driving intersection density
            drive_intersection_density, drive_intersection_count = graph_based.intersection_density(g_drive, area)
            add_result(results_dict, "drive_intersection_density", drive_intersection_density)
            add_result(results_dict, "drive_intersection_count", drive_intersection_count)
            job_manager.update_job_progress(self.job_id, 36)

            # save the cycling graph with indicators attached
            # saver.save_as_shp(g_drive, f'drive_indices_network')
            return_g = g_drive

            # free memory
            # del g_drive

        job_manager.update_job_progress(self.job_id, 80)

        if save_network:
            edges = ox.graph_to_gdfs(return_g, node_geometry=False, fill_edge_geometry=False, edges=True, nodes=False)
            edges.crs = "epsg:4326"

            geojson_rep = edges.to_json()
            geojson_obj = json.loads(geojson_rep)
        else:
            geojson_obj = None

        job_manager.update_job_progress(self.job_id, 99)

        return {
            "index-values": results_dict,
            "street-network": geojson_obj
        }
    
    def __str__(self) -> str:
        return f'{self.title} - {self.description}'