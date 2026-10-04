import os, shutil
from basic_downloader import URLUnArchiveDownloader

# Downloader for GLC_FCS30D
class GLCFCS30DDownloader(URLUnArchiveDownloader):
    def download(self, info: dict, dest_dir: str) -> str:
        save_path = self._download_from_url(info, dest_dir)
        if save_path is None:
            print(f"No downloaded for {info}!!!")
            return None
        # unarhive
        unarchive_dir = self._unarchive(save_path)
        if unarchive_dir is None: return None
        # filter correct year
        prefix = "GLC_FCS30_19852000_5yearsMap" if info['map_year'] in (1985,1990,1995) else "GLC_FCS30D_20002022"
        for root, dirs, files in os.walk(unarchive_dir):
            for file in files:
                if not file.startswith(prefix):
                    os.remove(os.path.join(root, file))                
        # filter those useful
        dest_dir = os.path.dirname(save_path)
        self._filter(unarchive_dir, dest_dir, info['aoi'])
        # clean
        shutil.rmtree(unarchive_dir)
        #os.remove(save_path) #command to debug
        return None
        

     
    def download(self, info: dict, dest_dir: str) -> str:
        save_path = self._download_from_url(info, dest_dir)
        if save_path is None:
            print(f"No downloaded for {info}!!!")
            return None
        # unarhive
        unarchive_dir = self._unarchive(save_path)
        if unarchive_dir is None: return None
        # filter correct year
        prefix = "GLC_FCS30_19852000_5yearsMap" if info['map_year'] in (1985,1990,1995) else "GLC_FCS30D_20002022"
        for root, dirs, files in os.walk(unarchive_dir):
            for file in files:
                if not file.startswith(prefix):
                    os.remove(os.path.join(root, file))                
        # filter those useful
        dest_dir = os.path.dirname(save_path)
        self._filter(unarchive_dir, dest_dir, info['aoi'])
        # clean
        shutil.rmtree(unarchive_dir)
        #os.remove(save_path) #command to debug
        return None