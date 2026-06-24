import os
import sys
import subprocess

# Windows terminallerinde Türkçe karakter hatası almamak için UTF-8 zorlaması
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Gerekli kütüphanelerin kontrolü
try:
    import customtkinter
except ImportError:
    print("CustomTkinter bulunamadı.")
    sys.exit(1)

try:
    import PyInstaller
except ImportError:
    print("PyInstaller bulunamadı, sistem tarafından yükleniyor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    import PyInstaller

import PyInstaller.__main__

# CustomTkinter'ın tema dosyalarının exe içine dahil edilebilmesi için yolunu buluyoruz
customtkinter_path = os.path.dirname(customtkinter.__file__)

print("MCRcon Paneli derlenmeye hazırlanıyor...")

build_args = [
    'main.py',
    '--name=MCRconPanel',
    '--noconfirm',
    '--windowed',  # Arka plandaki siyah terminal penceresini gizler (sadece GUI açılır)
    '--onefile',   # Her şeyi tek bir .exe dosyasında toplar
    f'--add-data={customtkinter_path}{os.pathsep}customtkinter/',
    f'--add-data=version.json{os.pathsep}.'
]

# Kullanıcı "icon.ico" isimli bir dosya indirdiyse bunu exe ikonu olarak ekle
if os.path.exists("icon.ico"):
    print("[+] icon.ico bulundu! Programa ikon olarak ekleniyor...")
    build_args.append('--icon=icon.ico')
else:
    print("[-] icon.ico bulunamadı. Varsayılan ikon kullanılacak.")
    print("    (Kendi ikonunuzu eklemek isterseniz, indirdiğiniz ikonun adını 'icon.ico' yapıp")
    print("     bu klasöre atın ve bu scripti tekrar çalıştırın.)\n")

print("Derleme başlıyor... Lütfen bekleyin (1-2 dakika sürebilir)...")

# PyInstaller'ı çalıştır
PyInstaller.__main__.run(build_args)

print("\n[BAŞARILI] Derleme tamamlandı!")
print("Oluşturulan MCRconPanel.exe dosyasını 'dist' klasörü içerisinde bulabilirsiniz.")
