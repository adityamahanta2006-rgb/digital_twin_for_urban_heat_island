FROM python:3.11.13-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      postgis \
      postgresql-client-15 

COPY ./downloader /udt_assembler/downloader
COPY ./street_network_download /udt_assembler/street_network_download
COPY ./download_utils /udt_assembler/download_utils
COPY ./.passfile /udt_assembler
COPY ./__init__.py /udt_assembler
COPY ./data_download_process.py /udt_assembler
COPY ./gee-key.json /udt_assembler
COPY ./requirements.txt /udt_assembler
COPY ./base_piero_config.json /udt_assembler
COPY ./save_to_database.py /udt_assembler
COPY ./build_piero_config.py /udt_assembler
COPY ./init_geoserver_layers.py /udt_assembler
COPY ./entrypoint.sh /udt_assembler

WORKDIR /udt_assembler

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN chmod +x /udt_assembler/entrypoint.sh
ENTRYPOINT "/udt_assembler/entrypoint.sh"