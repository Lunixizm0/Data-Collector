from playwright.sync_api import sync_playwright
import json
import time
import subprocess
import sys
import os
from datetime import datetime

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
    lunix_dir = os.path.join(temp_base, 'lunix', 'ipdata')
    os.makedirs(lunix_dir, exist_ok=True)
    return lunix_dir

# Log dosyası
LOG_FILE = os.path.join(ensure_lunix_dir(), "ipdata.log.txt")

def log(message):
    """Log mesajını TEMP dizinindeki dosyaya yaz"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message)
    except Exception as e:
        pass  # Sessizce devam et

def check_and_install_playwright():
    """
    Playwright ve Chromium'un yüklü olup olmadığını kontrol eder
    Yüklü değilse otomatik olarak yükler
    """
    log("=" * 60)
    log("Playwright kurulum kontrolü başlatılıyor...")
    
    try:
        # Playwright'ın yüklü olup olmadığını kontrol et
        import playwright
        log("✓ Playwright kütüphanesi zaten yüklü")
    except ImportError:
        log("⚠️  Playwright kütüphanesi bulunamadı, yükleme başlatılıyor...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "playwright"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            log("✓ Playwright başarıyla yüklendi")
        except subprocess.CalledProcessError as e:
            log(f"❌ Playwright yükleme hatası: {e}")
            return False
        except Exception as e:
            log(f"❌ Beklenmeyen Playwright kurulum hatası: {e}")
            return False
    
    # Chromium tarayıcısının yüklü olup olmadığını kontrol et
    try:
        log("Chromium varlığı kontrol ediliyor...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_type = p.chromium
            executable_path = browser_type.executable_path
            
            if not os.path.exists(executable_path):
                raise FileNotFoundError(f"Chromium bulunamadı: {executable_path}")
            
        log(f"✓ Chromium mevcut: {executable_path}")
        return True
        
    except FileNotFoundError as e:
        log(f"⚠️  Chromium bulunamadı: {e}")
        log("Chromium indiriliyor... (Bu işlem birkaç dakika sürebilir)")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            log("✓ Chromium başarıyla indirildi")
            return True
        except subprocess.CalledProcessError as e:
            log(f"❌ Chromium indirme hatası: {e}")
            return False
        except Exception as e:
            log(f"❌ Beklenmeyen Chromium kurulum hatası: {e}")
            return False
    except Exception as e:
        log(f"❌ Chromium kontrol hatası: {e}")
        return False

def scrape_ipdata():
    """
    Playwright kullanarak ipdata.co'dan veri scrape eder
    """
    log("=" * 60)
    log("Web scraping işlemi başlatılıyor...")
    
    with sync_playwright() as p:
        browser = None
        try:
            log("Chromium tarayıcısı başlatılıyor (headless mode)...")
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            log("✓ Tarayıcı başarıyla başlatıldı")
            
            log("Yeni browser context oluşturuluyor...")
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            log("✓ Context oluşturuldu")
            
            log("Yeni sayfa açılıyor...")
            page = context.new_page()
            log("✓ Sayfa oluşturuldu")
            
            log("URL'ye gidiliyor: https://ipdata.co/")
            page.goto("https://ipdata.co/", wait_until="networkidle")
            log("✓ Sayfa başarıyla yüklendi (networkidle)")
            
            log("Sayfa render edilmesi için 2 saniye bekleniyor...")
            time.sleep(2)
            log("✓ Bekleme tamamlandı")
            
            log("'Raw Data' butonu aranıyor (selector: #raw-data)...")
            raw_data_button = page.locator('#raw-data')
            raw_data_button.wait_for(state="visible", timeout=10000)
            log("✓ 'Raw Data' butonu bulundu")
            
            log("'Raw Data' butonuna tıklanıyor...")
            raw_data_button.click()
            log("✓ Butona başarıyla tıklandı")
            
            log("JSON verisinin yüklenmesi için 1 saniye bekleniyor...")
            time.sleep(1)
            log("✓ Bekleme tamamlandı")
            
            log("JSON code elementi aranıyor (selector: code.raw-data.json.hljs)...")
            code_element = page.locator('code.raw-data.json.hljs')
            code_element.wait_for(state="visible", timeout=10000)
            log("✓ JSON code elementi bulundu")
            
            log("JSON HTML içeriği alınıyor...")
            json_html = code_element.inner_html()
            log(f"✓ HTML içeriği alındı ({len(json_html)} karakter)")
            
            log("HTML temizleme işlemi başlatılıyor...")
            import re
            # HTML taglerini kaldır
            json_text = re.sub(r'<[^>]+>', '', json_html)
            log(f"  - HTML tagleri temizlendi, kalan uzunluk: {len(json_text)}")
            
            # HTML entities'leri decode et
            json_text = json_text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            log("  - HTML entities decode edildi")
            
            # Baştaki/sondaki boşlukları temizle
            json_text = json_text.strip()
            log(f"✓ Temizleme tamamlandı, final uzunluk: {len(json_text)} karakter")
            
            # İlk ve son 100 karakteri logla
            log(f"JSON önizleme (ilk 100 karakter): {json_text[:100]}")
            log(f"JSON önizleme (son 100 karakter): {json_text[-100:]}")
            
            log("JavaScript object notation'dan geçerli JSON'a dönüştürme işlemi başlatılıyor...")
            # Key'leri tırnak içine al
            def add_quotes_to_keys(match):
                key = match.group(1)
                return f'"{key}":'
            
            # Key pattern: satır başı + boşluk + kelime + : 
            original_length = len(json_text)
            json_text = re.sub(r'\n\s+(\w+):', add_quotes_to_keys, json_text)
            json_text = re.sub(r'^\s*(\w+):', add_quotes_to_keys, json_text, flags=re.MULTILINE)
            log(f"  - Key'lere tırnak eklendi (uzunluk değişimi: {original_length} -> {len(json_text)})")
            
            log("JSON parse işlemi başlatılıyor...")
            data = json.loads(json_text)
            log(f"✓ JSON başarıyla parse edildi, {len(data)} anahtar bulundu")
            
            # JSON içeriğinin özetini logla
            if isinstance(data, dict):
                log(f"JSON anahtarları: {', '.join(list(data.keys())[:10])}{'...' if len(data) > 10 else ''}")
                if 'ip' in data:
                    log(f"  - IP adresi bulundu: {data['ip']}")
                if 'country_name' in data:
                    log(f"  - Ülke bulundu: {data['country_name']}")
                if 'city' in data:
                    log(f"  - Şehir bulundu: {data['city']}")
            
            log("Tarayıcı kapatılıyor...")
            browser.close()
            log("✓ Tarayıcı başarıyla kapatıldı")
            
            log("✓ Scraping işlemi başarıyla tamamlandı!")
            return data
            
        except TimeoutError as e:
            log(f"❌ Timeout hatası: {e}")
            log(f"   Detay: Element beklenen sürede yüklenmedi")
            if browser:
                try:
                    browser.close()
                    log("  - Tarayıcı kapatıldı")
                except:
                    pass
            return None
            
        except json.JSONDecodeError as e:
            log(f"❌ JSON parse hatası: {e}")
            log(f"   Detay: {e.msg} (satır {e.lineno}, kolon {e.colno})")
            log(f"   Sorunlu JSON bölümü: {json_text[max(0, e.pos-50):e.pos+50]}")
            if browser:
                try:
                    browser.close()
                    log("  - Tarayıcı kapatıldı")
                except:
                    pass
            return None
            
        except Exception as e:
            log(f"❌ Beklenmeyen hata: {type(e).__name__}: {e}")
            import traceback
            log(f"   Stack trace:\n{traceback.format_exc()}")
            if browser:
                try:
                    browser.close()
                    log("  - Tarayıcı kapatıldı")
                except:
                    pass
            return None

def save_to_file(data, filename="ipdata_result.json"):
    """Veriyi pretty JSON formatında TEMP dizinine kaydet"""
    log("=" * 60)
    
    # Lunix dizinini kullan
    output_dir = ensure_lunix_dir()
    # Tam dosya yolunu oluştur
    filepath = os.path.join(output_dir, filename)
    
    log(f"JSON dosyasına kaydetme işlemi başlatılıyor: {filepath}")
    
    try:
        log(f"Dosya açılıyor: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            log("JSON formatlanıyor (indent=4, ensure_ascii=False)...")
            json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=False)
        
        # Dosya boyutunu kontrol et
        file_size = os.path.getsize(filepath)
        log(f"✓ Veri başarıyla kaydedildi")
        log(f"  - Dosya yolu: {filepath}")
        log(f"  - Dosya boyutu: {file_size} bytes ({file_size/1024:.2f} KB)")
        return True
        
    except IOError as e:
        log(f"❌ Dosya yazma hatası: {e}")
        return False
    except Exception as e:
        log(f"❌ Beklenmeyen kaydetme hatası: {type(e).__name__}: {e}")
        return False

def run_ipdata():
    clear_log()
    """
    Tek fonksiyon çağrımı ile tüm scraping işlemini yapar
    Threading ile çağrılabilir
    Returns: dict veya None
    """
    log("\n" + "=" * 60)
    log("IPData.co Portable Web Scraper")
    log(f"Başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # Playwright kurulum kontrolü
    if not check_and_install_playwright():
        log("❌ Playwright kurulumu başarısız, işlem sonlandırılıyor")
        log("=" * 60 + "\n")
        return None
    
    # Web scraping
    data = scrape_ipdata()
    
    if data:
        # Dosyaya kaydet
        success = save_to_file(data)
        
        if success:
            log("=" * 60)
            log("✓✓✓ TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI ✓✓✓")
            log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log("=" * 60 + "\n")
            return data
        else:
            log("=" * 60)
            log("⚠️  Scraping başarılı ama dosya kaydedilemedi")
            log("=" * 60 + "\n")
            return data
    else:
        log("=" * 60)
        log("❌ Scraping işlemi başarısız oldu")
        log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("=" * 60 + "\n")
        return None

def main():
    log("\n" + "=" * 60)
    log("IPData.co Portable Web Scraper")
    log(f"Başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # Playwright kurulum kontrolü
    if not check_and_install_playwright():
        log("❌ Playwright kurulumu başarısız, işlem sonlandırılıyor")
        log("=" * 60 + "\n")
        return None
    
    # Web scraping
    data = scrape_ipdata()
    
    if data:
        # Dosyaya kaydet
        success = save_to_file(data)
        
        if success:
            log("=" * 60)
            log("✓✓✓ TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI ✓✓✓")
            log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log("=" * 60 + "\n")
            return data
        else:
            log("=" * 60)
            log("⚠️  Scraping başarılı ama dosya kaydedilemedi")
            log("=" * 60 + "\n")
            return data
    else:
        log("=" * 60)
        log("❌ Scraping işlemi başarısız oldu")
        log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("=" * 60 + "\n")
        return None

if __name__ == "__main__":
    main()