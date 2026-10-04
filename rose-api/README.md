# UrbanDT - The Urban Digital Twin Prototyping Platform

<div style="text-align:center; width:100%" >
<img src="https://res.cloudinary.com/dpcllcxnv/image/upload/v1763427061/UrbanDT/Thesis_architecture_ben6lr.png" width="200
  ">
</div>

## Overview
Build Urban Digital Twin prototypes from anywhere in the world by harnessing the power of open-source software and global open data with just a map extent.

Use UrbanDT platform for constructing the skeleton of a Urban Digital Twin and populate with real-world data from global open data sources. Perform 3D visualisation, street network analysis, and population and land cover assessments all in one place.

Extend the UrbanDT prototype with local data, data streams, and authoritative information thanks to UrbanDT flexibility and its data input system to convert your prototypes into fully-featured Urban Digital Twins.

UrbanDT uses:

- PostGIS (PostgreSQL + GIS extensions): For geospatial data management of vector formats.
- GeoServer: For visualisation and sharing support of raster and vector datasets using OGC web standards.
- ROSE-API: For OGC APIs support and processing capabilities through OGC API - Processes interfaces and cloud-based asynchronous processing.
- Piero: For 3D and 2D visualisation, taking advantage of Giro3D as a web rendering engine.

Quickly and easily create UrbanDT prototypes with Docker, which handles the creation of the entire UrbanDT infrastructure and downloads base data to have a ready-to-use prototype in no time! 


<div style="text-align:center; width:100%" >
<img src="https://res.cloudinary.com/dpcllcxnv/image/upload/v1763430812/UrbanDT/workflow_tfsbjh.jpg" width="100%"
  ">
</div>

## Repository layout
- docker-compose.yml — Orchestration for UrbanDT services.
- example-configs/ — Check example configurations to get started as fast as possible. 
- piero/ — Software for the Piero-based web visualisation application.
- rose-api/ — Software of ROSE-API, an OGC API-compliant web application that provides OGC API - Processes support for asynchronous processing capabilities.
- udt-assembler/ — Automated pipeline for downloading and configure default base data for the UrbanDT protoype.

*Note: It works better in Linux!*

## Prerequisites
- Git
- Docker & Docker Compose (v2+)
- Recommended: 16+ GB RAM for local composition.

## Quickstart — How to run the platform using Docker
1. Clone repository:
    ```
    git clone https://github.com/Diuke/urban-dt-platform.git
    cd urban-dt-platform
    ```

2. Copy and edit the configuration file template:

    ``cp example_configs/.env_template .env``

    Edit the configuration file (``.env``) to set the extent of the UrbanDT, its name, and various configuration parameters of the underlying UrbanDT platform services.

    The list of all configuration parameters is available in section ["Configuration file parameters"](#configuration-file-parameters)

3. Add Google Earth Engine key:
    
    Google Earth Engine is necessary to download base raster-based data (land cover, population, and elevation model) for the UrbanDT. 

    Tutorial on how to gey a GEE key: https://developers.google.com/earth-engine/guides/app_key

    Copy your GEE key in ``./udt-assembler``.

4. Start services:

    Start all services with 
    ``docker compose up --build -d``

    This will create a new instance of a UrbanDT with the database, processing server, GeoServer, and web visualisation application. In addition, it runs the automated data provision service (udt-data-assembler) that downloads, process, and inserts data into the prototype.

    The data download service may take some minutes to download and process all necessary data.

5. Verify services:
     
    - ROSE-API: http://localhost:8000/api
    - GeoServer: http://localhost:8081/geoserver
    - User Application: http://localhost:8080

6. Bring down
    docker compose down -v

Notes:
- For production, run behind a TLS-terminating reverse proxy, enable persistent volumes, and configure proper secrets management.
- For large datasets, prefer streaming ingestion via Kafka and asynchronous workers.

## Running locally

## Configuration file parameters 

UrbanDT offers various configuration parameters to control different aspects of the deployment and creation of UrbanDT instances. The configuration parameters can be modified in the configuration file ``.env``.

Example configuration files and a configuration file template can be found in the folder ``example-configs/``.

General
- ``COMPOSE_PROJECT_NAME`` — Sets the name of the Docker container.
- ``EXTENT`` — The bounding box of the UrbanDT. Used for setting the limits of the data download and the map visualisation. The extent should be in the form form ``"min_lat,min_lng,max_lat,min_lng"``
- ``EXTENT_CRS`` — Code of the CRS in which the extent is.
- ``DOWNLOAD_BASE_DATA`` — Determine if default base data should be downloaded. If set to 0, a UrbanDT instance will be created without any data.
- ``BUILDING_DATASET`` — Select the open dataset from which to download building data. Should be either "globfp" or "microsoft".
- ``URBAN_AREA_NAME`` — Set the name of the urban area. This is used to name certain downloaded datasets.

Docker volume shared folders
- ``HOST_OUTPUT_DIR`` — Location in the host of the shared output directory of ROSE-API processes.
- ``HOST_PROCESSING_DIR`` — Location in the host of the shared folder where custom processing scripts are stored.
- ``HOST_STORAGE_DIR`` — Location in the host of the shared data directory. This folder is shared with the GeoServer and ROSE-API services for data input and sharing.

ROSE-API Variables
- ``HOST_HTTP_WEB_PORT`` — Mapped port in the host for HTTP access to the ROSE-API instance.
- ``HOST_HTTPS_WEB_PORT`` — Mapped port in the host for HTTPS access to the ROSE-API instance.
- ``WEB_WORKERS`` — Number of Celery workers for asynchronous processing.
- ``WEB_TIMEOUT`` — Timeout of requests made to ROSE-API server.
- ``DEBUG`` — Determine if ROSE-API should be started in Debug mode.
- ``DJANGO_SECRET_KEY`` — Set the Django secret key.
- ``BASE_HOST`` — Set the base URL of ROSE-API in the host. E.g. "http://localhost:8000"
- ``HOST_STORAGE_DIR``
- ``HOST_STORAGE_DIR``
- ``HOST_STORAGE_DIR``

Timeseries / InfluxDB (optional)
- INFLUXDB_IMAGE=influxdb:2.6
- INFLUXDB_BUCKET=timeseries
- INFLUXDB_ORG=udt_org
- INFLUXDB_USER=influx_user
- INFLUXDB_PASSWORD=influx_pass
- INFLUXDB_PORT=8086

Kafka (streaming)
- KAFKA_BROKER=kafka:9092
- KAFKA_ZOOKEEPER=zookeeper:2181
- KAFKA_TOPIC=ingest-topic

Redis / Cache
- REDIS_IMAGE=redis:7
- REDIS_URL=redis://redis:6379

Object storage (S3-compatible)
- S3_ENDPOINT=
- S3_BUCKET=udt-bucket
- S3_ACCESS_KEY=
- S3_SECRET_KEY=
- S3_REGION=us-east-1
- USE_S3=false

Tile server
- TILESERVER_IMAGE=tileserver/tileserver-gl
- TILESERVER_PORT=8081

Authentication (optional OIDC)
- OIDC_ISSUER=
- OIDC_CLIENT_ID=
- OIDC_CLIENT_SECRET=
- OIDC_REDIRECT_URI=http://localhost:3000/auth/callback
- OIDC_SCOPES=openid profile email

Logging / Monitoring
- PROMETHEUS_PORT=9090
- GRAFANA_PORT=3001
- GRAFANA_ADMIN_USER=admin
- GRAFANA_ADMIN_PASSWORD=admin

Worker / API settings
- WORKER_CONCURRENCY=4
- API_LOG_LEVEL=info
- DATA_IMPORT_BATCH_SIZE=500

Examples and templates for .env are included in .env.template. Keep secrets out of source control and inject via Docker secrets or your cloud provider for production.

## Development tips
- Use docker compose profiles to start only required services during development.
- Enable SQL and GeoServer dumps for reproducible test datasets.
- Use Kafka + schema registry for robust streaming schema evolution.

## Troubleshooting
- Check container logs: docker compose logs -f <service>
- DB connection errors: verify POSTGRES_* variables and network between services
- GeoServer missing layers: ensure PostGIS public schema has geometry columns and datastores configured

## License
Specify your project license (e.g., MIT). Third-party components have their own licenses; ensure compliance.

## Supporters

This project is part of the research done by the [Politecnico di Milano - GIS-GEOLab](https://www.gisgeolab.polimi.it/).

Partially funded by [EBWorld - s.r.l.](https://www.ebw.it/)

<div style="text-align:center; width:100%" >
<img src="https://res.cloudinary.com/dpcllcxnv/image/upload/v1763429227/UrbanDT/techs_dyk4nl.jpg" width="100%"
  ">
</div>