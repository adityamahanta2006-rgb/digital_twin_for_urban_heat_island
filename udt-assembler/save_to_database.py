import subprocess
import os
import shlex

from dotenv import load_dotenv

if __name__ == "__main__":

    load_dotenv(override=True)
    dest_dir = "/data_dir/data"
    
    # Save data to PostGIS database
    data_folder = "/data_dir/data/street_networks"
    urban_area_name = os.getenv("URBAN_AREA_NAME", "urban_area")

    #  -h, --host=HOSTNAME      database server host or socket directory
    #  -p, --port=PORT          database server port number
    #  -U, --username=NAME      connect as specified database user
    #  -W, --password           force password prompt (should happen automatically)
    #  -e, --exit-on-error      exit on error, default is to continue

    # UDTDB_HOST="db"
    # UDTDB_PORT="5432"
    # UDTDB_DB="udt_data"
    # UDTDB_USER="udt"
    # UDTDB_PASSWORD="userudt"

    # Save road network
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    username = os.getenv("UDTDB_USER", "udt")
    password = os.getenv("UDTDB_PASSWORD", "userudt")
    database = os.getenv("UDTDB_DB", "udt_data")

    env = {"PGPASSWORD": f"{password}", **os.environ}

    # Common psql connection command
    # psql_command = f"PGPASSWORD={password} psql --host={host} --port={port} --username={username} -d {database}"
    psql_command = f"psql postgresql://{username}:{password}@{host}:{port}/{database}"

    print(psql_command)

    print("connected to database, start saving data...")

    # road network
    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/drive_network_edges.shp public.road_network"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/drive_network_nodes.shp public.road_network_nodes"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    # pedestrian network
    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/walk_network_edges.shp public.pedestrian_network"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/walk_network_nodes.shp public.pedestrian_network_nodes"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    # cycling network
    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/bike_network_edges.shp public.bike_network"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/bike_network_nodes.shp public.bike_network_nodes"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    # public transport network
    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/public_transport_edges.shp public.public_transport_network"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    input_command = f"shp2pgsql -s 4326:3857 -d {data_folder}/shp/public_transport_nodes.shp public.public_transport_network_nodes"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)

    # Save building footprints to database
    building_data_folder = "/data_dir/data/building_data"
    input_command = f"shp2pgsql -s 4326:3857 -d {building_data_folder}/buildings_2d.shp public.buildings_2d"
    input_command_split = shlex.split(input_command)
    psql_command_split = shlex.split(psql_command)

    result = subprocess.run(input_command_split, env=env, check=True, capture_output=True)
    psql = subprocess.run(psql_command_split, input=result.stdout, capture_output=True)