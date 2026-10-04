import os
import tarfile
import rarfile
import zipfile
import shutil

def extract_archive(file_path, dest_dir):
    """
    解压缩压缩包文件到指定目录，支持 tar, tar.gz, zip 等常见格式。
    :param file_path: 压缩包文件路径
    :param dest_dir: 解压到的目标文件夹
    """
    # 创建目标解压目录（如果不存在）
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    # 获取文件扩展名，判断文件类型
    if tarfile.is_tarfile(file_path):
        with tarfile.open(file_path) as tar:
            tar.extractall(path=dest_dir)  
    elif zipfile.is_zipfile(file_path):
        # 处理长路径，Windows 需要加 "\\?\" 前缀
        if os.name == 'nt':  # 仅 Windows 需要
            file_path = r"\\?\\" + os.path.abspath(file_path)
            dest_dir = r"\\?\\" + os.path.abspath(dest_dir)
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
    elif rarfile.is_rarfile(file_path):
        with rarfile.RarFile(file_path) as rf:
            rf.extractall(dest_dir)
    else:
        # 其他格式可以使用 shutil 自带的 unpack_archive
        try:
            shutil.unpack_archive(file_path, dest_dir)
        except shutil.ReadError as e:
            print(f"Unsupported archive format: {file_path} with error {e}")
            return False
        
    print(f"Extracted {file_path} to {dest_dir}")
    return True
