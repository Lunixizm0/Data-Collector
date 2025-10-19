import subprocess
import os
from datetime import datetime
import time

def clear_log():
    """Log dosyasını temizle"""
    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except Exception as e:
        pass

# Lunix dizinini oluştur
def ensure_lunix_dir():
    """Lunix dizinini oluştur"""
    temp_base = os.environ.get('TEMP', os.environ.get('TMP', os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')))
    lunix_dir = os.path.join(temp_base, 'lunix', 'msinfo')
    os.makedirs(lunix_dir, exist_ok=True)
    return lunix_dir

def log(message):
    """Log mesajını dosyaya yaz"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message)
    except Exception as e:
        pass

# Log dosyası
LOG_FILE = os.path.join(ensure_lunix_dir(), "msinfo.log.txt")

def export_msinfo():
    """msinfo32'yi GUI olmadan export et"""
    log("=" * 60)
    log("MSInfo32 export işlemi başlatılıyor...")
    
    # Export dosya adı
    output_file = "msinfo_result.nfo"
    abs_output_path = os.path.join(ensure_lunix_dir(), output_file)
    
    try:
        log(f"Output dosyası: {abs_output_path}")
        
        # Eğer önceki dosya varsa sil
        if os.path.exists(output_file):
            log(f"Önceki dosya bulundu, siliniyor...")
            os.remove(output_file)
            log("✓ Önceki dosya silindi")
        
        # msinfo32 komutunu oluştur
        # /nfo = NFO formatında export et
        # /report = GUI göstermeden export et
        command = ["msinfo32", "/nfo", abs_output_path]
        
        log(f"Komut: {' '.join(command)}")
        log("msinfo32 çalıştırılıyor...")
        log("  (Bu işlem 30-60 saniye sürebilir)")
        
        # msinfo32'yi çalıştır
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        log(f"✓ Process başlatıldı (PID: {process.pid})")
        log("Process'in tamamlanması bekleniyor...")
        
        # Process'in bitmesini bekle (max 180 saniye)
        try:
            process.wait(timeout=180)
            log(f"✓ Process tamamlandı (return code: {process.returncode})")
        except subprocess.TimeoutExpired:
            log("⚠️  Process timeout'a uğradı (180 saniye)")
            process.kill()
            log("  Process sonlandırıldı")
            return None
        
        # Dosyanın oluşmasını bekle
        log("Export dosyası kontrol ediliyor...")
        max_wait = 300
        wait_count = 0
        
        while not os.path.exists(abs_output_path) and wait_count < max_wait:
            time.sleep(1)
            wait_count += 1
            if wait_count % 5 == 0:
                log(f"  Bekleniyor... ({wait_count}/{max_wait} saniye)")
        
        # Dosya kontrolü
        if os.path.exists(abs_output_path):
            file_size = os.path.getsize(abs_output_path)
            log("✓ Export dosyası başarıyla oluşturuldu")
            log(f"  - Dosya adı: {output_file}")
            log(f"  - Dosya yolu: {abs_output_path}")
            log(f"  - Dosya boyutu: {file_size} bytes ({file_size/1024:.2f} KB / {file_size/1024/1024:.2f} MB)")
            
            # Dosya içeriğini kontrol et (boş mu?)
            if file_size == 0:
                log("⚠️  Dosya boş!")
                return None
            
            log("=" * 60)
            log("✓✓✓ MSInfo32 EXPORT BAŞARILI ✓✓✓")
            log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log("=" * 60 + "\n")
            
            return {
                "file": output_file,
                "path": abs_output_path,
                "size": file_size,
                "size_readable": f"{file_size/1024/1024:.2f} MB"
            }
        else:
            log("❌ Export dosyası oluşturulamadı")
            log(f"  Beklenen dosya: {abs_output_path}")
            return None
            
    except FileNotFoundError:
        log("❌ msinfo32 bulunamadı!")
        log("  msinfo32 sadece Windows sistemlerde mevcuttur")
        return None
        
    except PermissionError as e:
        log(f"❌ İzin hatası: {e}")
        log("  Yönetici olarak çalıştırmayı deneyin")
        return None
        
    except Exception as e:
        log(f"❌ Beklenmeyen hata: {type(e).__name__}: {e}")
        import traceback
        log(f"Stack trace:\n{traceback.format_exc()}")
        return None

def run_msinfo_scraper():
    clear_log()
    """
    Tek fonksiyon çağrımı ile MSInfo32 export işlemini yapar
    Threading ile çağrılabilir
    Returns: dict veya None
    """
    log("\n" + "=" * 60)
    log("MSInfo32 Scraper")
    log(f"Başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # msinfo32'yi export et
    result = export_msinfo()
    
    if result:
        log("=" * 60)
        log("✓ Scraper başarıyla tamamlandı")
        log("=" * 60 + "\n")
        return result
    else:
        log("=" * 60)
        log("❌ Scraper başarısız oldu")
        log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("=" * 60 + "\n")
        return None

def main():
    """CLI'dan çağrıldığında çalışır"""
    return run_msinfo_scraper()

if __name__ == "__main__":
    main()