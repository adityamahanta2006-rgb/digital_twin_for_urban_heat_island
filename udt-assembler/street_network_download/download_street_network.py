import ray
from .modules import network_extractor as net_extractor
from osmnx import settings
from pathlib import Path

class StreetNetworkDownloader():
    def __init__(self):
        pass

    def download(self, info: dict, dest_dir: str, modes=[]) -> str:

        # Change for your own data base path
        # Add here your path 
        data_base_path = info.get('data_base_path', None)  # Default to global if not provided
        if data_base_path is None:
            raise ValueError("data_base_path must be provided in info dictionary.")
        
        output_base_path = f"{dest_dir}/street_networks"

        # The extractor instance
        extractor = net_extractor.NetworkExtractor(base_path=data_base_path, output_path=output_base_path)
        
        # Custom OSMnx settings
        settings.default_crs = "epsg:4326"

        errors = []

        print(f"Starting Download of Street Networks...")

        try:
            # extract info from GHS with search_name and country

            geom = info.get('geometry', None)  # Default to global if not provided
            if geom is None:
                raise ValueError("Geometry must be provided in info dictionary.")
            
            print(geom)
            
            city_name = info.get('name', None)  # Default to global if not provided
            if city_name is None:
                raise ValueError("Geometry must be provided in info dictionary.")

            # the geometry from which to extract the network. Is given by the GHS dataset.
            geometry = geom

            # Variables for the elimination of duplicate pedestrian/driving streets
            dist_threshold = 20
            slope_threshold = 15

            # Assessment = False, so duplicate pedestrian/driving streets will be eliminated.
            assess = False

            # Create graph and shapefile folders if they do not exist
            Path(f"{dest_dir}/graph").mkdir(parents=True, exist_ok=True) # graphml folder
            Path(f"{dest_dir}/shp").mkdir(parents=True, exist_ok=True) # shapefiles folder

            # Process the 4 networks in parallel using the paralellized download_network function.
            g_promises = []
            mode_counter = 0

            pedestrian_i = None
            if "PEDESTRIAN" in modes:
                # the pedestrian network
                pedestrian_i = mode_counter
                mode_counter += 1
                g_promises.append(extractor.download_network.remote(
                    extractor,
                    "walk", 
                    geometry, 
                    city_name, 
                    assessment=assess, 
                    dist_threshold=dist_threshold, 
                    slope_threshold=slope_threshold,
                    add_elevation=True,
                    dem_file_location=f'{data_base_path}/dem.tif'
                ))

            cycling_i = None
            if "CYCLING" in modes:
                # the cycling network
                cycling_i = mode_counter
                mode_counter += 1
                g_promises.append(extractor.download_network.remote(
                    extractor,
                    "bike", 
                    geometry, 
                    city_name, 
                    assessment=assess, 
                    add_elevation=True,
                    dem_file_location=f'{data_base_path}/dem.tif'
                ))

            driving_i = None
            if "DRIVING" in modes:
                # the driving network
                driving_i = mode_counter
                mode_counter += 1
                g_promises.append(extractor.download_network.remote(
                    extractor,
                    "drive", 
                    geometry, 
                    city_name, 
                    assessment=assess, 
                    add_elevation=True,
                    dem_file_location=f'{data_base_path}/dem.tif'
                ))

            pt_i = None
            if "PUBLIC_TRANSPORT" in modes:
                # the public transport network
                pt_i = mode_counter
                mode_counter += 1
                g_promises.append(extractor.download_network.remote(
                    extractor,
                    "public_transport", 
                    geometry, 
                    city_name, 
                    assessment=assess, 
                    add_elevation=False,
                    dem_file_location=f'{data_base_path}/dem.tif'
                ))       
            
            # [g_walk, g_bike, g_drive, g_public] = ray.get(g_promises)
            responses = ray.get(g_promises)

            # Save graphs
            if pedestrian_i is not None:
                g_walk = responses[pedestrian_i]
                extractor.save_as_graph(g_walk, f'graph/walk_network')
                extractor.save_as_shp(g_walk, f'shp/walk_network')    

            if cycling_i is not None:
                g_bike = responses[cycling_i]
                extractor.save_as_graph(g_bike, f'graph/bike_network')
                extractor.save_as_shp(g_bike, f'shp/bike_network')

            if driving_i is not None:
                g_drive = responses[driving_i]
                extractor.save_as_graph(g_drive, f'/graph/drive_network')
                extractor.save_as_shp(g_drive, f'shp/drive_network')

            if pt_i is not None:
                g_public = responses[pt_i]
                extractor.save_as_graph(g_public, f'/graph/public_transport_network')
                has_edges = g_public.number_of_edges() > 0 # save only if edges exist
                has_nodes = g_public.number_of_nodes() > 0 # save only if nodes exist
                extractor.save_as_shp(g_public, f'shp/public_transport', save_edges=has_edges, save_nodes=has_nodes)
            
            ray.shutdown()

        except Exception as ex:
            errors.append(city_name)
            print(ex)
            ray.shutdown()
