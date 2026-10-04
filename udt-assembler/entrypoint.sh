
# Download base data if flag is set
if [ "${DOWNLOAD_BASE_DATA:-0}" = "1" ]; then
  python3 data_download_process.py
  python3 save_to_database.py
  python3 init_geoserver_layers.py
  python3 build_piero_config.py
  
fi