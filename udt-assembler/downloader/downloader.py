import os,sys, json
#sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import pandas as pd
import ast
import shutil
from concurrent.futures import ThreadPoolExecutor, wait
from basic_downloader import *
from customer_downloader import *
import getopt
from utils.path import make_sure_dir_exist

# get from environment variables or default
MAX_WORKERS = int(os.environ.get("MOLCAP_MAX_WORKERS", 5))
# download type
DTYPE_URL = 'URL'
DTYPE_URL_UNARCHIVE = 'URL_UNARCHIVE'
DTYPE_GEE = 'GEE'
DTYPE_GLC_FCS30D = 'GLC_FCS30D'
    
class DatasetFactory:
    def __init__(self, gee_serice_account_key_path):
        self.gee_serice_account_key_path = gee_serice_account_key_path

    def create_downloader(self, info: dict) -> DatasetDownloader:
        """choose the downloading method according to the given info

        Args:
            info (dict): the configuration of this downloader

        Returns:
            DatasetDownloader: _description_
        """
        url, dtype = info['url'], info['type'].upper()
        if dtype == DTYPE_GEE:
            return GEEDownloader(self.gee_serice_account_key_path)
        elif dtype == DTYPE_URL_UNARCHIVE:
            return URLUnArchiveDownloader()
        elif dtype == DTYPE_URL:
            if url.startswith("ftp://"):
                return FTPDownloader()
            elif url.startswith("http://") or url.startswith("https://"):
                return URLDownloader()
            else:
                raise ValueError(f"Unsupported URL scheme: {url}")
        elif dtype == DTYPE_GLC_FCS30D:
            return GLCFCS30DDownloader()
        else:
            raise ValueError(f"Unsupported downloader type: {dtype}")
    
class BatchDownloader:
    def __init__(self, factory: DatasetFactory):
        self.factory = factory
        
    def load_dataset_from_csv(self, csv_file):
        df = pd.read_csv(csv_file)
        for _, row in df.iterrows():
            data = dict(row)
            data.update({
                "type": row['type'].upper(),
                'aoi': ast.literal_eval(row['aoi']) if 'aoi' in row and not pd.isna(row['aoi']) else None,
                'gee_collection_extract_method': row['gee_collection_extract_method'] if 'gee_collection_extract_method' in row else '',
                'scale': row['scale'] if 'scale' in row else 0,
            })
            if 'bands' in data and data['bands']:
                data['bands'] = ast.literal_eval(data['bands'])
            yield data
            
    def download_by_csv(self, csv_file: str, base_dest_dir: str, dest_dir_generator) -> None:
        make_sure_dir_exist(base_dest_dir)
        duplicate_download_urls = {}
        fail_downloaded = set()
        
        all_task = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for row in self.load_dataset_from_csv(csv_file):
                dest_dir = dest_dir_generator(base_dest_dir, row)
                if row['type'].upper() == DTYPE_URL and row['url'] in duplicate_download_urls:
                    # to avoid duplicate
                    source_path = duplicate_download_urls[row['url']][-1]
                    print(f"We have {row['url']} which already downloaded and saved to {source_path}. Copy to {dest_dir} avoid duplicating downloading.")
                    dest_path = os.path.join(dest_dir, os.path.basename(source_path))
                    shutil.copyfile(source_path, dest_path)
                    continue
                # schedule the download task
                downloader = self.factory.create_downloader(row)
                def add_to_duplicate(future):
                    save_path = future.result()
                    if row['type'].upper() == DTYPE_URL:  
                        if save_path is None:
                            fail_downloaded.add(row["url"])
                            return
                        else:
                            duplicate_download_urls[row["url"]]=(row, save_path) 
                        
                future = executor.submit(downloader.download, row, dest_dir)
                all_task.append(future)
                future.add_done_callback(add_to_duplicate)
        
            # wait all thread to be done
            wait(all_task) 
        
        if fail_downloaded: print(f"Fail downloaded urls based on csv file {csv_file}\n", "\n".join(fail_downloaded))
        return {csv_file: list(fail_downloaded)}
 
    def is_exist_by_csv(self, csv_file: str) -> None:
        res = {}
        for row in self.load_dataset_from_csv(csv_file):
            # schedule the download task
            res[ str(row)] = downloader = self.factory.create_downloader(row)
            downloader.is_exist(row)
        return res
        
def default_dest_dir_generator(dir, row):
    """create the directory structure based on a csv record"""
    region = row['region']
    year = row['year']
    map_name, map_year = row['map_name'], row['map_year']
    dir_path = os.path.join(dir, region, str(year), f'{map_name}_{map_year}')
    make_sure_dir_exist(dir_path)
    return dir_path
     

def main(argv):
    csv_dir, csv_file = r"", r""
    dest_dir = r""
    gee_serice_account_key_path = r""
    
    # parse params
    USAGE = "downloader.py -d <input_dir> -o <output_dir> -k <gee_serice_account_key_path>"
    try:
        opts, args = getopt.getopt(argv, "hd:f:o:k:", ["input_dir=", "input_file=", "output_dir=", "gee_key="])
        #print(opts, '\n', args)
    except getopt.GetoptError:
        print(USAGE)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(USAGE)
            sys.exit()
        elif opt in ("-d", "--input_dir"):
            csv_dir = arg
        elif opt in ("-f", "--input_file"):
            csv_file = arg
        elif opt in ("-o", "--output_dir"):
            dest_dir = arg
        elif opt in ("-k", "--gee_key"):
            gee_serice_account_key_path = arg
    print(f"[Arguments] input_dir={csv_dir} | input_file={csv_file} | output_dir={dest_dir} | gee_key={gee_serice_account_key_path}")
    
    if not ((csv_dir == "") ^ (csv_file == "")):
        print("Args 'input_dir' and 'input_file' must provide one and only one")
        sys.exit(2)
    
    # let's work!
    print(f"[Downloader Configuration]\nCHUNK_SIZE = {CHUNK_SIZE}\nMAX_WORKERS = {MAX_WORKERS}")
    factory = DatasetFactory(gee_serice_account_key_path)
    downloader = BatchDownloader(factory)
    fail_results = {}
    if csv_dir:
        for f in os.listdir(csv_dir):
            print("Handle csv file:", f)
            fp = os.path.join(csv_dir, f)
            if os.path.isfile(fp) and fp.endswith(".csv"):
                print(f"Begin to handle {fp}....")
                csv_file = fp
                result = downloader.download_by_csv(csv_file, dest_dir, default_dest_dir_generator)
                fail_results.update(result)
    else:
        print(f"Begin to handle {csv_file}....")
        result = downloader.download_by_csv(csv_file, dest_dir, default_dest_dir_generator)
        fail_results.update(result)
    # save
    with open("fail_downloaded.json", "w") as f:
        json.dump(fail_results, f, indent=4)
        
if __name__ == '__main__':
    main(sys.argv[1:])