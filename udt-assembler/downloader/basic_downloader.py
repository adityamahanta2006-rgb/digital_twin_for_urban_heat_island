import os
import json
#sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from abc import ABC, abstractmethod
import requests
import json
import ee
import time

import io

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

# Global default value
DEFAULT_CRS_EPSG_CODE = 4326
DEFAULT_CRS = f'EPSG:{DEFAULT_CRS_EPSG_CODE}'

GEE_CLEAN_AFTER_DOWNLOAD = bool(os.environ.get('MOLCAP_GEE_CLEAN_AFTER_DOWNLOAD', True))
GEE_POLL_INTERVAL = int(os.environ.get('GEE_POLL_INTERVAL', 60))
CHUNK_SIZE = int(os.environ.get("MOLCAP_DOWNLOAD_CHUNK_SIZE", 8192))
GEE_TILE_SIZE = int(os.environ.get('GEE_TILE_SIZE', 5))

class DatasetDownloader(ABC):
    @abstractmethod
    def download(self, info: dict, dest_dir: str) -> str:
        pass
    
    @abstractmethod
    def is_exist(self, info: dict) -> bool:
        pass
    
class GEEDownloader(DatasetDownloader):
    def __init__(self, key_path):
        super().__init__()
        self.g_key_path = key_path # path of authentication file (json file)
        self.drive_service = None
        
        self.init_google_service()
        
    def init_google_service(self):
        """Authenticate and initialize the Google service like Earth Engine using service account credential"""

        # For google earth engine
        # obtain the email of service account from authentication file
        # authenticate using the credentials
        service_account_email = json.load(open(self.g_key_path))['client_email']
        credentials = ee.ServiceAccountCredentials(service_account_email, self.g_key_path)
        ee.Initialize(credentials)

        # initialize the Earth Engine API
        # ee.Authenticate()
        # ee.Initialize(project="ee-juanpduque6")
        print('GEE Initialized.')

        # For google drive
        SCOPES = ['https://www.googleapis.com/auth/drive']
        CREDENTIALS = service_account.Credentials.from_service_account_file(self.g_key_path, scopes=SCOPES)

        # Initialize Google Drive API client
        self.drive_service = build('drive', 'v3', credentials=CREDENTIALS)

    def make_sure_gdf_exist(self, fpath, parent_folder_id='root'):
        """Make sure the folder in google driver specified by 'fpath' exists"""
        folder_names = [name.strip() for name in fpath.strip('/').split('/') if name.strip()]
        current_folder_id = parent_folder_id

        for folder_name in folder_names:
            current_folder_id = self.create_folder_if_not_exists(folder_name, current_folder_id)

        return current_folder_id
    
    def create_folder_if_not_exists(self, folder_name, parent_folder_id):
        # CHECK IF FOLDER EXIST
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        # Query the folder
        results = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        if items:
            # If the folder exists, return its id
            return items[0]['id']
        else:
            # If the folder does not exist, create a new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id] if parent_folder_id else []
            }
            folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
            print(f"Created folder '{folder_name}' with ID: {folder['id']}")
            return folder['id']
        
    # Search folder based on folder name
    def search_folders(self, folder_name):
        # search folder id based on folder name
        query = f"name='{folder_name}' and mimeType = 'application/vnd.google-apps.folder'"
        results = self.drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
        print(f"Find folder by name {folder_name} results:", results)
        folders = results.get("files", [])
        if len(folders) == 0:
            print(f"The folder {folder_name} cannot be found.")
        return folders
    
    # Search files in specific folder
    def search_files(self, folder_name):
        folders = self.search_folders(folder_name)
        if len(folders) == 0: return
        files = []
        for folder in folders:
            folder_id = folder["id"]
            
            # search files under folder
            query = f"'{folder_id}' in parents"
            results = self.drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
            print(f"Search files in {folder_name} results: {results}")
            items = results.get('files', [])
            if not items:
                print(f'No files found in folder {folder_name} with id={folder_id}')
                continue
            else:
                files.extend(items)
        return files
    
    # Download files in specific folder of google driver 
    def download_file_from_google_drive_folder(self, folder_name, dest_dir, fileNamePrefix=""):
        files = []
        items = self.search_files(folder_name)
        if items:
            for item in items:
                if (fileNamePrefix and item['name'].startswith(fileNamePrefix)) or not fileNamePrefix:
                    self.download_file_from_google_drive(item['id'], item['name'], dest_dir)
                    files.append(item)
        return files
        
    def download_file_from_google_drive(self, file_id, file_name, dest_dir):
        request = self.drive_service.files().get_media(fileId=file_id)
        with open(os.path.join(dest_dir, file_name), 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {file_name} {int(status.progress() * 100)}%.")

    def _delete_files_from_google_drive_forever(self, files):
        for file in files:
            self.drive_service.files().delete(fileId=file['id']).execute()
    
    def _delete_folder_from_google_drive_forever(self, folder_name):
        folders = self.search_folders(folder_name)
        for folder in folders:
             self.drive_service.files().delete(fileId=folder['id']).execute()
        
    def is_exist(self, info: dict) -> bool:
        try:
            #print(f"the information we get: {info}") # for debug
            dataset_name = info['url']
            year = info['map_year']
            aoi = ee.Geometry.Polygon(coords=info['aoi'], proj=ee.Projection(DEFAULT_CRS))
            
            # get the dataset from GEE
            if not ee.data._credentials or self.drive_service is None:
                self.init_google_service()
            ds = ee.ImageCollection(dataset_name).filterBounds(aoi).filter(ee.Filter.calendarRange(year, year, 'year'))
            num_images = ds.size().getInfo()
            #print(f"Number of images:", num_images)
            if num_images != 0: return True
        except Exception as e:
            print(f"Failed to check existing status {info}. Error: {e}")
        return False
        
    def _show_hist(self, aoi, image, band_name):
        # 1. Use frequencyHistogram to calculate the pixel counts per class
        hist_dict = image.select(band_name) \
            .reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=aoi,
                scale=10,
                maxPixels=1e13
            ) \
            .get(band_name) \
            .getInfo()

        # 2. print the histogram
        print("Category histogram:", hist_dict)
        
    def download(self, info:dict, dest_dir: str) -> str:
        """download data in GEE

        Args:
            info (dict): it should contain an item with key "url"
            dest_dir (str): _description_
        """
        try:
            print(f"the information we get: {info}") # for debug
            dataset_name = info['url']
            year = info['map_year']
            aoi = ee.Geometry.Polygon(coords=info['aoi'], proj=ee.Projection(DEFAULT_CRS))
            gee_collection_extract_method = info['gee_collection_extract_method'].upper()
            scale = info['scale']
            file_name = "_".join(dataset_name.split('/')) + f"_{year}.tif"
            output_path = os.path.join(dest_dir, file_name)
            
            # check if the file already exists
            if not os.path.exists(output_path):
                # get the dataset from GEE
                if not ee.data._credentials or self.drive_service is None:
                    self.init_google_service()

                #ds = ee.ImageCollection(dataset_name).filterBounds(aoi).filter(ee.Filter.calendarRange(year, year, 'year'))
                #print(f"Number of images:", ds.size().getInfo())
                
                ds = ee.Image(dataset_name).clip(aoi)
                print(f"Image info:", ds.getInfo())
                
                if "bands" in info: # get selected bands
                    ds = ds.select(info['bands'])
                # Print to check image id and bands
                # print("First image bands:", ds.first().bandNames().getInfo())
                print("First image bands:", ds.bandNames().getInfo())
                    
                compo_img = None
                if gee_collection_extract_method == 'MODE':
                    compo_img = ds.reduce(ee.Reducer.mode())
                elif gee_collection_extract_method == 'MEDIAN':
                    compo_img = ds.reduce(ee.Reducer.median())
                elif gee_collection_extract_method == 'MEAN':
                    compo_img = ds.reduce(ee.Reducer.mean())
                elif gee_collection_extract_method == 'SINGLE':
                    compo_img = ds
                else:
                    compo_img = ds.first()
                compo_img = compo_img.rename("composition").clip(aoi)
                # check composition result
                print("Composition image bands:", compo_img.bandNames().getInfo())
                #self._show_hist(aoi, compo_img, "composition")

                projection = compo_img.projection().getInfo()
                    
                # create the folder if not exist
                folder_name = f"udt-assembler-data"
                #self.make_sure_gdf_exist(folder_name)
                # export image to Google Drive
                fileNamePrefix = f'dem'
                #print(f"AOI Projection: {aoi.projection().getInfo()}\nImage Projection: {projection}\nExported Image Projection: {ds.double().projection().getInfo()}")
                task = ee.batch.Export.image.toDrive(
                    image=compo_img,
                    description=f'{info["map_name"]} image in year {info["map_year"]}',
                    fileNamePrefix=fileNamePrefix,
                    scale=scale,
                    region=aoi,
                    crs=projection['crs'],
                    maxPixels=1e13,
                    folder=folder_name
                )

                task.start()
                
                print(f"Download GEE datast {file_name} (CRS={projection['crs']}) to Google Drive with fileNamePrefix {fileNamePrefix}, task started...")
                while task.active():
                    print(f"Waiting for the export task (fileNamePrefix {fileNamePrefix}) to complete...")
                    time.sleep(GEE_POLL_INTERVAL)

                task_status = task.status()
                print(f"Download GEE datast {file_name} to Google Drive with fileNamePrefix {fileNamePrefix}, task completed (status={task_status}). Now begin to download to local")

                # Download to local
                if task_status.get('state') != 'COMPLETED':
                    print(f'We cannot download because the export task is {task_status.get("state")}')
                else:
                    files = self.download_file_from_google_drive_folder(folder_name, dest_dir, fileNamePrefix)
                    if GEE_CLEAN_AFTER_DOWNLOAD:
                        self._delete_files_from_google_drive_forever(files)
                        self._delete_folder_from_google_drive_forever(folder_name)
                
            else:
                print(f"File {output_path} already exists. Skipping download.")
                
            return output_path
        except Exception as e:
            print(f"Failed to download {info}. Error: {e}")


    def download_only_cloud(self, info:dict, dest_dir: str) -> str:
        """download data in GEE

        Args:
            info (dict): it should contain an item with key "url"
            dest_dir (str): _description_
        """
        try:
            print(f"the information we get: {info}") # for debug
            dataset_name = info['url']
            year = info['map_year']
            aoi = ee.Geometry.Polygon(coords=info['aoi'], proj=ee.Projection(DEFAULT_CRS))
            gee_collection_extract_method = info['gee_collection_extract_method'].upper()
            scale = info['scale']

            if "output_name" in info:
                file_name = info['output_name']
            else:
                file_name = "_".join(dataset_name.split('/')) + f"_{year}.tif"

            output_path = os.path.join(dest_dir, file_name)
            
            # check if the file already exists
            if not os.path.exists(output_path):
                # get the dataset from GEE
                if not ee.data._credentials or self.drive_service is None:
                    self.init_google_service()

                #ds = ee.ImageCollection(dataset_name).filterBounds(aoi).filter(ee.Filter.calendarRange(year, year, 'year'))
                #print(f"Number of images:", ds.size().getInfo())
                
                if gee_collection_extract_method == 'SINGLE':
                    ds = ee.Image(dataset_name).clip(aoi)

                elif gee_collection_extract_method == 'MOSAIC':
                    start_date = ee.Date(f"{info['start_date']}")
                    end_date = ee.Date(f"{info['end_date']}")
                    ds = ee.ImageCollection(dataset_name).filterBounds(aoi).filter(ee.Filter.date(start_date, end_date))

                else:
                    ds = ee.ImageCollection(dataset_name).filterBounds(aoi).filter(ee.Filter.calendarRange(year, year, 'year'))
                
                if "bands" in info: # get selected bands
                    ds = ds.select(info['bands'])
                    
                compo_img = None
                if gee_collection_extract_method == 'MOSAIC':
                    reducer = info['gee_collection_reducer'].upper()
                    if reducer == 'MODE':
                        compo_img = ds.reduce(ee.Reducer.mode())
                    elif reducer == 'MEDIAN':
                        compo_img = ds.reduce(ee.Reducer.median())
                    elif reducer == 'MEAN':
                        compo_img = ds.reduce(ee.Reducer.mean())
                    elif reducer == 'MAX':
                        compo_img  = ds.reduce(ee.Reducer.max())
                    else:
                        compo_img = ds.first()
                else:
                    compo_img = ds

                compo_img = compo_img.rename("composition").clip(aoi)
                # check composition result
                print("Composition image bands:", compo_img.bandNames().getInfo())
                #self._show_hist(aoi, compo_img, "composition")

                # Export to Google Cloud Storage
                export_projection = info['export_projection'] if 'export_projection' in info else None
                if export_projection is None:
                    export_projection = compo_img.projection().getInfo()

                compo_img.reproject("EPSG:4326")
                
                url = ee.Image.getDownloadURL(compo_img, {
                    'format': 'GeoTIFF',
                    'crs': "EPSG:4326",
                    'region': aoi,
                    'scale': scale,
                })

                # Download to local file
                response = requests.get(url, stream=True)

                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                print("✅ Downloaded directly to local path")
                
            else:
                print(f"File {output_path} already exists. Skipping download.")
                
            return output_path
        except Exception as e:
            print(f"Failed to download {info}. Error: {e}")
        