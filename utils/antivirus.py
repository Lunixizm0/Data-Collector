import os,logging,tempfile,re;from datetime import datetime

def setup_logging(clear_previous=True):
    """
    Log klasörünü hazırlar Eğer clear_previous True ise
    klasördeki önceki dosyalar silinir
    Dönen değer log dizini yolu
    """
    temp_dir = tempfile.gettempdir()
    log_dir = os.path.join(temp_dir, "lunix", "antivirus")
    os.makedirs(log_dir, exist_ok=True)

    if clear_previous:
        # Önceki log ve sonuç dosyalarını temizle
        try:
            for fname in os.listdir(log_dir):
                fpath = os.path.join(log_dir, fname)
                try:
                    if os.path.isfile(fpath) or os.path.islink(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        # eğer alt dizin varsa sil
                        import shutil
                        shutil.rmtree(fpath)
                except Exception:
                    # Temizleme başarısızsa devam et
                    pass
        except Exception:
            # log dizini okunamazsa atla
            pass

    # Log dosyasını açmadan önce eski loglaru sil
    log_file_path = os.path.join(log_dir, "antivirus.log")

    # logging yapılandırması
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logging.info("Günlük kaydı başlatıldı" if clear_previous else "Günlük kaydı başlatıldı.")
    return log_dir

def get_unique_antivirus_names():
    raw_list = [
        "Avast", "AVG", "Bitdefender", "Kaspersky", "McAfee", "Norton", "Sophos",
        "ESET", "Malwarebytes", "Avira", "Panda", "Trend Micro", "F-Secure",
        "Comodo", "BullGuard", "360 Total Security", "Ad-Aware", "Dr.Web", "G-Data",
        "Vipre", "ClamWin", "ZoneAlarm", "Cylance", "Webroot", "Palo Alto Networks",
        "Symantec", "SentinelOne", "CrowdStrike", "Emsisoft", "HitmanPro", "Fortinet",
        "FireEye", "Zemana", "Windows Defender"
    ]
    # Küçük harf duplike kontrolü yap
    uniq = {}
    for item in raw_list:
        key = item.strip()
        if key:
            uniq[key] = True
    return list(uniq.keys())

def build_detection_patterns():
    """
    Her antivirüs için kullanılan filename-base regex'lerini döndürür.
    Pattern'ler dosya adı (uzantı olmadan) üzerinde çalışacak şekilde hazırlanır.
    Özel durumlar (ör. Windows Defender) için bilinen .exe isimleri de eklenir.
    """
    av_names = get_unique_antivirus_names()

    patterns = {}  # av_name -> list of compiled regex
    for av in av_names:
        av_lower = av.lower()

        # Temel kural: tam kelime eşleşmesi veya başta başlama
        # Örneğin: 'eset' kelimesinin 'reset' içinde eşleşmesini önlemek için \b kullan
        basic = re.compile(r'\b' + re.escape(av_lower) + r'\b', re.IGNORECASE)

        # Ayrıca başta olma durumu (ör. 'avastui' 'avastsvc' vb.)
        starts = re.compile(r'^' + re.escape(av_lower), re.IGNORECASE)

        patterns[av] = [basic, starts]

    # Özel alias / exe isimleri: (antivirüs adı -> liste(exe_adı|regex))
    # Windows Defender için bilinen yürütülebilirleri
    special = {
        "Windows Defender": [
            re.compile(r'^msmpeng$', re.IGNORECASE),   # MsMpEng.exe
            re.compile(r'^msmpengservice$', re.IGNORECASE),
            re.compile(r'^mrt$', re.IGNORECASE),       # MRT (Microsoft Removal Tool)
            re.compile(r'^mpcmdrun$', re.IGNORECASE),  # Defender komut aracı
        ],
        "ESET": [
            # ESET için sık kullanılan exe isimler
            re.compile(r'^ekrn$', re.IGNORECASE),      # ekrn.exe (ESET kernel process)
            re.compile(r'^egui$', re.IGNORECASE),      # egui.exe (ESET GUI)
        ],
        "Malwarebytes": [
            re.compile(r'^mbam$', re.IGNORECASE),
            re.compile(r'^mbamservice$', re.IGNORECASE),
        ],
        "Avast": [
            re.compile(r'^avastui$', re.IGNORECASE),
            re.compile(r'^avastsvc$', re.IGNORECASE),
        ],
        "Bitdefender": [
            re.compile(r'^bdagent$', re.IGNORECASE),
            re.compile(r'^bdservicehost$', re.IGNORECASE),
        ],
    }

    # special içindekileri patternsa ekle
    for av_name, regex_list in special.items():
        if av_name not in patterns:
            patterns[av_name] = []
        patterns[av_name].extend(regex_list)

    return patterns

def filename_without_ext(fname):
    return os.path.splitext(fname)[0]

def find_antivirus_executables(base_folder, max_dirs=None):
    """
    base_folder altında recursive olarak .exe dosyalarını arar
    Regex kurallarına göre tespit yapar
    max_dirs (opsiyonel) kaç kök dizin gezilecek (performans kontrolü amacıyla)
              None ise sınırsız.
    Döner dict(antivirus_name -> tam_exe_yolu)
    """
    logging.info(f"'{base_folder}' içinde antivirüs .exe dosyaları aranıyor...")
    patterns = build_detection_patterns()
    found = {}
    visited_roots = 0

    for root, _, files in os.walk(base_folder):
        visited_roots += 1
        if max_dirs is not None and visited_roots > max_dirs:
            logging.info(f"Maksimum kök dizin sayısına ({max_dirs}) ulaşıldı, tarama sonlandırılıyor.")
            break

        try:
            for file in files:
                # Sadece .exe dosyalarını kontrol et
                if not file.lower().endswith(".exe"):
                    continue

                name_no_ext = filename_without_ext(file).lower()

                # Her antivirüs için tanımlı tüm pattern'leri test et
                for av_name, regs in patterns.items():
                    # Eğer zaten bulunduysa atla
                    if av_name in found:
                        continue

                    matched = False
                    for rg in regs:
                        try:
                            if rg.search(name_no_ext):
                                matched = True
                                break
                        except re.error:
                            # Regex hatası olursa o regexi atla
                            continue

                    if matched:
                        exe_path = os.path.join(root, file)
                        logging.info(f"Antivirüs yürütülebilir dosyası bulundu: '{file}' -> {exe_path}")
                        found[av_name] = exe_path
                        break  # regs döngüsünden çık
        except Exception as e:
            logging.warning(f"'{root}' dizini taranırken hata oluştu veya erişim reddedildi: {e}")
            continue

    return found

def write_results(log_dir, found):
    """
    found sözlüğünü antivirusler.txt dosyasına yazar Eğer antivirüs daha önce bulunmuşsa tekrar yazmaz
    """
    output_file = os.path.join(log_dir, "antivirusler.txt")
    existing_avs = set()
    
    # Mevcut antivirusler.txt dosyasını oku ve var olan antivirüsleri kontrol et
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                for line in f:
                    if ":" in line:
                        av_name = line.split(":")[0].strip()
                        existing_avs.add(av_name)
        except Exception:
            pass

    try:
        # Sadece yeni bulunan antivirüsleri ekle
        with open(output_file, "a", encoding="utf-8") as f:
            if not found:
                if not existing_avs:  # Dosya boşsa veya yoksa
                    f.write("Hiçbir antivirüs yürütülebilir dosyası bulunamadı.\n")
            else:
                for av_name, path in found.items():
                    if av_name not in existing_avs:
                        f.write(f"{av_name}: {path}\n")

        logging.info(f"Sonuçlar '{output_file}' dosyasına kaydedildi.")
    except Exception as e:
        logging.error(f"Sonuçlar dosyaya yazılamadı: {e}")

def main(folders_to_scan=None, clear_logs=True, max_dirs_per_root=None):
    """
    Ana fonksiyon. Launcher tarafından antivirus.main() olarak çağrılacak
    - folders_to_scan : list of folders to scan. Eğer None ise varsayılan C:\\ olarak ayarlanır
    - clear_logs : True ise önceki loglar silinir
    - max_dirs_per_root : opsiyonel sınırlama (performans için)

    Döner: found sözlüğü (antivirus_name -> exe path)
    """
    try:
        log_dir = setup_logging(clear_previous=clear_logs)

        if folders_to_scan is None:
            # Varsayılan: kök taraması
            folders_to_scan = ["C:\\"]

        all_found = {}

        for folder in folders_to_scan:
            if os.path.exists(folder):
                logging.info(f"Tarama başlıyor: {folder}")
                try:
                    found = find_antivirus_executables(folder, max_dirs=max_dirs_per_root)
                    # update: eğer aynı antivirüs farklı yerde bulunduysa ilk bulunanı koru
                    for k, v in found.items():
                        if k not in all_found:
                            all_found[k] = v
                except Exception as e:
                    logging.error(f"'{folder}' taranırken hata oluştu: {e}")
            else:
                logging.warning(f"'{folder}' klasörü bulunamadı veya erişilemedi, atlanıyor.")

        if all_found:
            logging.info("Antivirüs yürütülebilir dosyaları tespit edildi.")
            print("Antivirüs yürütülebilir dosyaları bulundu:\n")
            for av_name, path in all_found.items():
                print(f"{av_name}: {path}")
        else:
            logging.warning("Hiçbir antivirüs yürütülebilir dosyası bulunamadı.")
            print("Hiçbir antivirüs yürütülebilir dosyası bulunamadı.")

        write_results(log_dir, all_found)
        return all_found
    except Exception as e:
        logging.critical(f"Beklenmeyen hata: {e}")
        print(f"Beklenmeyen bir hata oluştu: {e}")
        return {}

if __name__ == "__main__":
    # Yerel test için
    main()
