import os
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def run_ftp_server():
    ip = "0.0.0.0"
    port = 21

    # Betiğin bulunduğu dizinin altındaki "upload" klasörü
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_dir = os.path.join(base_dir, "upload")
    os.makedirs(upload_dir, exist_ok=True)

    # Anonim kullanıcı: sadece yazma (upload) izni
    # izinler: e=list, l=dir list, r=read, a=append, d=delete, f=rename, m=create dir, w=write
    # sadece w (write) yeterli
    authorizer = DummyAuthorizer()
    authorizer.add_anonymous(upload_dir, perm='w')

    handler = FTPHandler
    handler.authorizer = authorizer

    # Listeleme ve indirmeyi engelle
    def block_list_download(handler_inst, file):
        return False

    handler.on_incomplete_file_sent = block_list_download
    handler.on_file_received = lambda inst, file: print(f"Yüklendi: {file}")

    server = FTPServer((ip, port), handler)
    server.max_cons = 10
    server.max_cons_per_ip = 3

    print(f"Anonim FTP sunucusu aktif: {ip}:{port}")
    print(f"Yüklemeler {upload_dir} dizinine kaydedilecek.")
    server.serve_forever()

if __name__ == "__main__":
    run_ftp_server()