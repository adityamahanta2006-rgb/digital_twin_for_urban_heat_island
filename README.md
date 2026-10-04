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

    The list of all configuration parameters is available in section ["Configuration file parameters"](#configuration-file-parameters).

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


## Configuration file parameters 

UrbanDT offers various configuration parameters to control different aspects of the deployment and creation of UrbanDT instances. The configuration parameters can be modified in the configuration file ``.env``.

Example configuration files and a configuration file template can be found in the folder ``example-configs/``.

General configuration variables
- ``COMPOSE_PROJECT_NAME`` — Sets the name of the Docker container.
- ``EXTENT`` — The bounding box of the UrbanDT. Used for setting the limits of the data download and the map visualisation. The extent should be in the form form ``"min_lat,min_lng,max_lat,min_lng"``
- ``EXTENT_CRS`` — Code of the CRS in which the extent is.
- ``DOWNLOAD_BASE_DATA`` — Determine if default base data should be downloaded. If set to 0, a UrbanDT instance will be created without any data.
- ``BUILDING_DATASET`` — Select the open dataset from which to download building data. Should be either "globfp" or "microsoft".
- ``URBAN_AREA_NAME`` — Set the name of the urban area. This is used to name certain downloaded datasets.

Docker volume shared folders configuration variables
- ``HOST_OUTPUT_DIR`` — Location in the host of the shared output directory of ROSE-API processes.
- ``HOST_PROCESSING_DIR`` — Location in the host of the shared folder where custom processing scripts are stored.
- ``HOST_STORAGE_DIR`` — Location in the host of the shared data directory. This folder is shared with the GeoServer and ROSE-API services for data input and sharing.

ROSE-API configuration variables
- ``HOST_HTTP_WEB_PORT`` — Mapped port in the host for HTTP access to the ROSE-API instance.
- ``HOST_HTTPS_WEB_PORT`` — Mapped port in the host for HTTPS access to the ROSE-API instance.
- ``WEB_WORKERS`` — Number of Celery workers for asynchronous processing.
- ``WEB_TIMEOUT`` — Timeout of requests made to ROSE-API server.
- ``DEBUG`` — Determine if ROSE-API should be started in Debug mode.
- ``DJANGO_SECRET_KEY`` — Set the Django secret key.
- ``ROSE_API_BASE_URL`` — Set the base URL of ROSE-API in the host. E.g. "http://localhost:8000"
- ``CELERY_BROKER_URL`` — URL of the Celery broker for asynchronous processsing.
- ``DJANGO_SUPERUSER_USERNAME`` — Django Admin created superuser username.
- ``DJANGO_SUPERUSER_PASSWORD`` — Django Admin created superuser password.
- ``DJANGO_SUPERUSER_EMAIL`` — Django Admin email for the created superuser.

PostgreSQL database configuration variables
- ``POSTGRES_HOST`` — The address where the PostgreSQL database is hosted.
- ``POSTGRES_PORT`` — The PostgreSQL port.
- ``HOST_DB_PORT`` — Mapped PostgreSQL port in the host machine.
- ``POSTGRES_DB`` — The name of the maintenance database.
- ``POSTGRES_USER`` — PostgreSQL admin username.
- ``POSTGRES_PASSWORD`` — PostgreSQL admin password.

GeoServer configuration variables - Read more about GeoServer configuration variables in ["GeoServer Environment Variables"](https://github.com/kartoza/docker-geoserver?tab=readme-ov-file#environment-variables) 
- ``HOST_GEOSERVER_BASE_URL`` — Base GeoServer URL in host machine. E.g., http://localhost:8081.
- ``HOST_GEOSERVER_PORT`` — GeoServer port in host machine.
- ``GEOSERVER_ADMIN_PASSWORD`` — Set the GeoServer admin password.
- ``GEOSERVER_ADMIN_USER`` — Set the GeoServer admin username.
- ``STABLE_EXTENSIONS`` — List of enabled extensions for GeoServer.
- ``GEOSERVER_DATA_DIR`` — Internal data directory for GeoServer.

User Application configuration variables
- ``HOST_FRONTEND_BASE_URL`` — Base URL of the user application.
- ``HOST_FRONTEND_PORT`` — Mapped port in the host for the user application.
- ``HOST_FRONTEND_PROD`` — Set the Production flag for the user application.

UrbanDT automated data download configuration variables
- ``UDTDB_DB`` — The database name where the base UrbanDT data assembler downloaded data is stored.
- ``UDTDB_USER`` — The database username where the base UrbanDT data assembler downloaded data is stored.
- ``UDTDB_PASSWORD`` — The user password where the base UrbanDT data assembler downloaded data is stored.

Examples and templates for the configuration files are included in the ``.env.template`` file. Keep secrets out of source control and inject via Docker secrets or your cloud provider for production.

## Extending data 

Data in UrbanDT prototypes can be exteded and/or replaced with local and authoritative data. By using the shared data directory available at ``HOST_STORAGE_DIR`` users can insert custom datasets that can be then accessed and shared via GeoServer, added to the PostgreSQL database or streamed by ROSE-API OGC API - Features or EDR capabilities.

To add a new dataset, simply add your data into the shared directory and configure sharing and visualisation parameters through GeoServer!

## Creating processing pipelines

UrbanDT, through ROSE-API and leveraging OGC API - Processes interfaces, offers an extensible framework for creating your own processing pipelines as python scripts.

Check out the example process located in ``rose_api/geoapi/processes/processes/example.py`` for a reference on how to structure your own processing scripts.

Processing scripts can be added on-the-fly to UrbanDT through the processes shared folder. This folder can be defined with the configuration variable ``HOST_PROCESSING_DIR``.

All files located in ``HOST_PROCESSING_DIR`` are parsed and offered as OGC API - Processes interfaces. Processes are also listed in the Analysis menu of the Piero web application.

## License
Each of the components of the UrbanDT platform are based on open-source software.

UrbanDT is distributed under a MIT license.

Piero and ROSE-API are both distributed under MIT licenses.

GeoServer is distributed under a GNU General Public License Version 2.0.

## Supporters

This project is part of the research done by the [Politecnico di Milano - GIS-GEOLab](https://www.gisgeolab.polimi.it/).

Partially funded by [EBWorld - s.r.l.](https://www.ebw.it/)

<div style="text-align:center; width:100%" >
<img src="https://res.cloudinary.com/dpcllcxnv/image/upload/v1763429227/UrbanDT/techs_dyk4nl.jpg" width="100%"
  ">
</div>