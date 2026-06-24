import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
from mcrcon import MCRcon, MCRconException
import socket
import re
import os
import sys
import json
import urllib.request
import webbrowser

# Varsayılan temanın ve renk paletinin ayarlanması
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolTip:
    """Tkinter ve CustomTkinter widget'ları için basit Tooltip (İpucu) Sınıfı"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        # Fare widget üzerinde durduğunda 0.6 saniye sonra göster
        self.id = self.widget.after(600, lambda: self.show_tooltip(event))

    def leave(self, event=None):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hide_tooltip()

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        
        # Eğer buton deaktif ise tooltip göstermeyelim (isteğe bağlı)
        if hasattr(self.widget, "cget") and self.widget.cget("state") == "disabled" and "Bukkit" not in self.text:
            return

        # Farenin ekran üzerindeki koordinatını al
        if event:
            x, y = event.x_root + 15, event.y_root + 15
        else:
            x, y = self.widget.winfo_rootx() + 20, self.widget.winfo_rooty() + 20
            
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes("-topmost", True)
        
        # Tooltip tasarımı
        label = tk.Label(self.tooltip_window, text=self.text, background="#2b2b2b", foreground="#e0e0e0", 
                         relief="solid", borderwidth=1, font=("Arial", 10), justify=tk.LEFT)
        label.pack(ipadx=6, ipady=3)

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class MinecraftRconGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Pencere Ayarları ---
        self.title("Minecraft RCON Paneli (Pro)")
        self.geometry("950x600")
        self.minsize(850, 500)

        self.rcon = None
        self.is_bukkit = False  # Sunucunun paper/bukkit olup olmadığını tutar
        
        # Komut Geçmişi
        self.command_history = []
        self.history_index = -1

        # Grid Ayarları
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_screen()
        
        # Açılışta güncellemeleri kontrol et
        self.check_for_updates()

    def _build_sidebar(self):
        # --- Sol Menü (Sidebar) Çerçevesi ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1)

        # Başlık
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="RCON Yönetimi", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # IP Adresi Girişi
        self.ip_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Sunucu IP")
        self.ip_entry.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Port Girişi
        self.port_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="Port (25575)")
        self.port_entry.insert(0, "25575")
        self.port_entry.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Şifre Girişi
        self.password_entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text="RCON Şifresi", show="*")
        self.password_entry.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Bağlan Butonu
        self.connect_btn = ctk.CTkButton(self.sidebar_frame, text="Bağlan", command=self.connect_to_server, 
                                         fg_color="#28a745", hover_color="#218838")
        self.connect_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Bağlantıyı Kes Butonu
        self.disconnect_btn = ctk.CTkButton(self.sidebar_frame, text="Bağlantıyı Kes", command=self.disconnect_from_server, 
                                            state="disabled", fg_color="#dc3545", hover_color="#c82333")
        self.disconnect_btn.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        # Hızlı İşlemler
        self.quick_actions_label = ctk.CTkLabel(self.sidebar_frame, text="Hızlı Komutlar", font=ctk.CTkFont(size=14, weight="bold"))
        self.quick_actions_label.grid(row=6, column=0, padx=20, pady=(30, 0))

        self.btn_save = ctk.CTkButton(self.sidebar_frame, text="Dünyayı Kaydet (Save-All)", state="disabled", 
                                      command=lambda: self.send_command_thread("save-all"))
        self.btn_save.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        ToolTip(self.btn_save, "Sunucudaki harita ve envanter verilerini kaydeder.")

    def _build_main_screen(self):
        # --- Sağ Ana Ekran (Sekmeli Yapı) ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Sekmeleri Ekle
        self.tab_console = self.tabview.add("Konsol")
        self.tab_server = self.tabview.add("Sunucu Araçları")
        self.tab_admin = self.tabview.add("Yönetici Araçları")

        self._build_console_tab()
        self._build_server_tab()
        self._build_admin_tab()

    def _build_console_tab(self):
        self.tab_console.grid_rowconfigure(0, weight=1)
        self.tab_console.grid_columnconfigure(0, weight=1)

        # Konsol Textbox
        self.console_textbox = ctk.CTkTextbox(self.tab_console, state="disabled", font=ctk.CTkFont(family="Consolas", size=13))
        self.console_textbox.grid(row=0, column=0, columnspan=2, padx=5, pady=(5, 0), sticky="nsew")

        # Komut Giriş Alanı
        self.command_entry = ctk.CTkEntry(self.tab_console, placeholder_text="Gönderilecek komutu buraya yazın... (Eski komutlar için YUKARI OK)", state="disabled")
        self.command_entry.grid(row=1, column=0, padx=(5, 0), pady=10, sticky="ew")
        
        # Event Bindings
        self.command_entry.bind("<Return>", self.send_command_thread)
        self.command_entry.bind("<Up>", self.history_up)
        self.command_entry.bind("<Down>", self.history_down)

        # Gönder Butonu
        self.send_btn = ctk.CTkButton(self.tab_console, text="Gönder", width=80, state="disabled", command=self.send_command_thread)
        self.send_btn.grid(row=1, column=1, padx=10, pady=10)
        ToolTip(self.send_btn, "Yazılan komutu sunucuya gönderir.")

        self.log_to_console("Minecraft RCON Paneline Hoş Geldiniz!", "command")
        self.log_to_console("Lütfen sol taraftan sunucu bilgilerinizi girip bağlanın.\n", "info")

    def _build_server_tab(self):
        self.tab_server.grid_columnconfigure(0, weight=1)
        self.tab_server.grid_columnconfigure(1, weight=1)

        # Zaman Ayarları
        time_frame = ctk.CTkFrame(self.tab_server)
        time_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(time_frame, text="Zaman Ayarları", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        btn_day = ctk.CTkButton(time_frame, text="Gündüz Yap", command=lambda: self.send_command_thread("time set day"))
        btn_day.pack(pady=5, padx=10, fill="x")
        btn_night = ctk.CTkButton(time_frame, text="Gece Yap", command=lambda: self.send_command_thread("time set midnight"))
        btn_night.pack(pady=5, padx=10, fill="x")
        ToolTip(btn_day, "Sunucu zamanını sabah yapar.")
        ToolTip(btn_night, "Sunucu zamanını gece yarısı yapar.")

        # Hava Durumu
        weather_frame = ctk.CTkFrame(self.tab_server)
        weather_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(weather_frame, text="Hava Durumu", font=ctk.CTkFont(weight="bold")).pack(pady=5)

        btn_clear = ctk.CTkButton(weather_frame, text="Açık (Clear)", command=lambda: self.send_command_thread("weather clear"))
        btn_clear.pack(pady=5, padx=10, fill="x")
        btn_rain = ctk.CTkButton(weather_frame, text="Yağmur (Rain)", command=lambda: self.send_command_thread("weather rain"))
        btn_rain.pack(pady=5, padx=10, fill="x")
        btn_storm = ctk.CTkButton(weather_frame, text="Fırtına (Thunder)", command=lambda: self.send_command_thread("weather thunder"))
        btn_storm.pack(pady=5, padx=10, fill="x")

        # Sistem İşleyişi
        sys_frame = ctk.CTkFrame(self.tab_server)
        sys_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(sys_frame, text="Oyun Akışı (Tick)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        btn_freeze = ctk.CTkButton(sys_frame, text="Zamanı Dondur", command=lambda: self.send_command_thread("tick freeze"))
        btn_freeze.pack(pady=5, padx=10, fill="x")
        btn_unfreeze = ctk.CTkButton(sys_frame, text="Zamanı Akıt", command=lambda: self.send_command_thread("tick unfreeze"))
        btn_unfreeze.pack(pady=5, padx=10, fill="x")
        ToolTip(btn_freeze, "Sunucudaki zamanı, mobları ve block güncellemelerini durdurur.")

        # Tehlikeli Bölge
        danger_frame = ctk.CTkFrame(self.tab_server, fg_color="#3a1e1e") # Hafif kırmızımsı
        danger_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(danger_frame, text="Güç Kontrolleri", font=ctk.CTkFont(weight="bold"), text_color="#ff4d4d").pack(pady=5)
        
        btn_reload = ctk.CTkButton(danger_frame, text="Sunucuyu Yenile (Reload)", command=lambda: self.send_command_thread("reload"))
        btn_reload.pack(pady=5, padx=10, fill="x")
        ToolTip(btn_reload, "Plugin konfigürasyonlarını yeniden yükler.")

        self.btn_restart = ctk.CTkButton(danger_frame, text="Yeniden Başlat (Restart)", command=self.ask_restart)
        self.btn_restart.pack(pady=5, padx=10, fill="x")
        ToolTip(self.btn_restart, "Sadece Bukkit/Paper sunucularında desteklenir.")

        btn_stop = ctk.CTkButton(danger_frame, text="Güvenli Kapat (Stop)", fg_color="#dc3545", hover_color="#c82333", command=self.ask_stop)
        btn_stop.pack(pady=5, padx=10, fill="x")
        ToolTip(btn_stop, "Sunucuyu tamamen kapatır.")

        # Başlangıçta tüm sekmeyi deaktif gibi ayarlamak için buton referanslarını bir listeye alalım
        self.server_buttons = [btn_day, btn_night, btn_clear, btn_rain, btn_storm, btn_freeze, btn_unfreeze, btn_reload, self.btn_restart, btn_stop]
        for btn in self.server_buttons:
            btn.configure(state="disabled")

    def _build_admin_tab(self):
        self.tab_admin.grid_columnconfigure(0, weight=1)

        # 1. Satır: Oyuncu Seçimi
        player_frame = ctk.CTkFrame(self.tab_admin)
        player_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        player_frame.grid_columnconfigure(1, weight=1)

        self.btn_refresh_players = ctk.CTkButton(player_frame, text="Oyuncuları Yenile", width=120, state="disabled", command=self.fetch_players)
        self.btn_refresh_players.grid(row=0, column=0, padx=10, pady=10)
        ToolTip(self.btn_refresh_players, "Sunucudaki aktif oyuncu listesini çeker.")

        self.admin_dropdown = ctk.CTkOptionMenu(player_frame, values=["(Boş)"], state="disabled")
        self.admin_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ToolTip(self.admin_dropdown, "İşlem yapılacak Hedef Oyuncu (Admin)")

        # 2. Satır: Seçili Yönetici İşlemleri
        actions_frame = ctk.CTkFrame(self.tab_admin)
        actions_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        actions_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(actions_frame, text="Hızlı Aksiyonlar:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.btn_tp_all = ctk.CTkButton(actions_frame, text="Herkesi Bana Çek (TP @a)", state="disabled", command=self.action_tp_all)
        self.btn_tp_all.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        ToolTip(self.btn_tp_all, "Sunucudaki herkesi seçili oyuncuya ışınlar.")

        self.btn_punisher = ctk.CTkButton(actions_frame, text="Cezalandırıcı Çubuk (Knockback 50)", state="disabled", command=self.action_give_punisher)
        self.btn_punisher.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ToolTip(self.btn_punisher, "Seçili oyuncuya Savurma 50 basılı, kırmızı renkli 'Cezalandırıcı' çubuğu verir.")

        event_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        event_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.btn_event = ctk.CTkButton(event_frame, text="Event Alanı Kur (Bedrock Box)", state="disabled", command=self.action_event_area)
        self.btn_event.pack(side="left")
        ToolTip(self.btn_event, "Seçili oyuncunun konumuna üstü açık, içi boş bir Bedrock arenası kurar.")

        ctk.CTkLabel(event_frame, text="Boyut:").pack(side="left", padx=(20, 5))
        self.event_size_entry = ctk.CTkEntry(event_frame, width=50, state="disabled")
        self.event_size_entry.insert(0, "20")
        self.event_size_entry.pack(side="left")

        # 3. Satır: Duyuru Modülü
        broadcast_frame = ctk.CTkFrame(self.tab_admin)
        broadcast_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        broadcast_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(broadcast_frame, text="Ekrana Duyuru Gönder (Title / Broadcast)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.broadcast_entry = ctk.CTkEntry(broadcast_frame, placeholder_text="Duyuru mesajını yazın...", state="disabled")
        self.broadcast_entry.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.btn_broadcast = ctk.CTkButton(broadcast_frame, text="Duyur", width=80, state="disabled", command=self.action_broadcast)
        self.btn_broadcast.grid(row=1, column=1, padx=10, pady=10)
        ToolTip(self.btn_broadcast, "Tüm oyuncuların ekranının tam ortasına büyük ve sarı renkte duyuru çıkarır.")

    # --- KOMUT GEÇMİŞİ YÖNETİMİ ---
    def history_up(self, event):
        if not self.command_history:
            return
        # Yukarı ok ile geçmişe git
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
        
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, self.command_history[-(self.history_index + 1)])

    def history_down(self, event):
        if not self.command_history:
            return
        # Aşağı ok ile günümüze gel
        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, "end")
            self.command_entry.insert(0, self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.command_entry.delete(0, "end") # En aşağındayken boşalt

    def add_to_history(self, command):
        if not command: return
        # Aynı komutu art arda spamladıysa ekleme
        if len(self.command_history) > 0 and self.command_history[-1] == command:
            self.history_index = -1
            return
            
        self.command_history.append(command)
        # Son 10 elemanı tut
        if len(self.command_history) > 10:
            self.command_history.pop(0)
        self.history_index = -1

    # --- TEHLİKELİ BUTON ONAYLARI ---
    def ask_restart(self):
        if messagebox.askyesno("Uyarı", "Sunucuyu yeniden başlatmak istediğinize emin misiniz?"):
            self.send_command_thread("restart")

    def ask_stop(self):
        # 3 Adım Onaylı Stop
        if messagebox.askyesno("1. Onay", "Sunucuyu KAPANMA moduna almak istediğinize emin misiniz?"):
            if messagebox.askyesno("2. Onay", "Sunucu kapanırsa RCON bağlantınız kesilir ve manuel olarak başlatmanız gerekir. Devam mı?"):
                if messagebox.askyesno("3. Son Karar!", "SON KARARINIZ MI? Sunucu kapatılacak!"):
                    self.send_command_thread("stop")

    # --- YÖNETİCİ AKSİYONLARI ---
    def fetch_players(self):
        """Arkaplanda oyuncu listesini çeker."""
        threading.Thread(target=self._fetch_players_task, daemon=True).start()

    def _fetch_players_task(self):
        try:
            response = self.rcon.command("list")
            # Örnek dönüş: "There are X of a max of Y players online: Admin, Oyuncu2"
            if ":" in response:
                players_str = response.split(":", 1)[1]
                # İsimleri temizle ve diziye çevir
                players = [p.strip() for p in players_str.split(",") if p.strip()]
                if not players:
                    players = ["(Oyuncu Yok)"]
                self.after(0, lambda: self._update_dropdown(players))
            else:
                self.after(0, lambda: self._update_dropdown(["(Liste Alınamadı)"]))
        except Exception as e:
            self.after(0, lambda: self.log_to_console(f"[!] Liste çekilemedi: {e}", "error"))

    def _update_dropdown(self, players):
        self.admin_dropdown.configure(values=players)
        self.admin_dropdown.set(players[0])
        self.log_to_console("[*] Oyuncu listesi güncellendi.", "info")

    def action_tp_all(self):
        target = self.admin_dropdown.get()
        if target and target not in ["(Boş)", "(Oyuncu Yok)", "(Liste Alınamadı)"]:
            self.send_command_thread(f"tp @a {target}")
        else:
            self.log_to_console("[!] Lütfen geçerli bir oyuncu seçin.", "error")

    def action_give_punisher(self):
        target = self.admin_dropdown.get()
        if not target or target in ["(Boş)", "(Oyuncu Yok)", "(Liste Alınamadı)"]:
            self.log_to_console("[!] Lütfen geçerli bir oyuncu seçin.", "error")
            return
        
        # 1.20.5+ syntax
        cmd_new = f"""give {target} stick[custom_name='{{"text":"Cezalandırıcı","color":"red","bold":true}}',enchantments={{levels:{{"minecraft:knockback":50}}}}] 1"""
        # 1.20.4 and older syntax
        cmd_old = f"""give {target} stick{{display:{{Name:'{{"text":"Cezalandırıcı","color":"red","bold":true}}'}},Enchantments:[{{id:"minecraft:knockback",lvl:50}}]}} 1"""
        
        threading.Thread(target=self._give_punisher_task, args=(cmd_old, cmd_new), daemon=True).start()

    def _give_punisher_task(self, cmd_old, cmd_new):
        try:
            # Try new syntax first
            res = self.rcon.command(cmd_new)
            # If error indicative of older version, try old syntax
            if "Unknown or incomplete command" in res or "Expected whitespace" in res or "Incorrect argument" in res:
                res = self.rcon.command(cmd_old)
            
            clean_res = re.sub(r'§[0-9a-fk-or]', '', res)
            self.after(0, lambda: self.log_to_console(f"[*] Cezalandırıcı verildi: {clean_res}", "success"))
        except Exception as e:
            self.after(0, lambda: self._on_send_error(str(e)))

    def action_event_area(self):
        target = self.admin_dropdown.get()
        if not target or target in ["(Boş)", "(Oyuncu Yok)", "(Liste Alınamadı)"]:
            self.log_to_console("[!] Lütfen geçerli bir oyuncu seçin.", "error")
            return
            
        try:
            size = int(self.event_size_entry.get().strip())
        except ValueError:
            self.log_to_console("[!] Lütfen etkinlik alanı boyutu için rakam girin (örn: 20).", "error")
            return

        r = size // 2
        # Algoritma: 
        # 1. Alt zemin döşe (Y = -1 seviyesi)
        # 2. Dış kutuyu outline ile döşe (Y = 0 ile 10 arası) - Bu dış duvarları ve çatıyı yaratır.
        # 3. İçeriyi (çatı dahil, yerin 1 blok üstünden) air ile doldurarak içi boş üstü açık arena yap.
        cmd1 = f"execute at {target} run fill ~-{r} ~-1 ~-{r} ~{r} ~-1 ~{r} bedrock"
        cmd2 = f"execute at {target} run fill ~-{r} ~0 ~-{r} ~{r} ~10 ~{r} bedrock outline"
        cmd3 = f"execute at {target} run fill ~-{r-1} ~0 ~-{r-1} ~{r-1} ~10 ~{r-1} air"

        # Komutları ardışık göndermek için ayrı bir thread (execute komutları sırasıyla işlenmeli)
        threading.Thread(target=self._build_event_area_task, args=(cmd1, cmd2, cmd3), daemon=True).start()

    def _build_event_area_task(self, cmd1, cmd2, cmd3):
        try:
            self.after(0, lambda: self.log_to_console("[*] Etkinlik alanı oluşturuluyor, lütfen bekleyin...", "info"))
            self.rcon.command(cmd1)
            self.rcon.command(cmd2)
            res = self.rcon.command(cmd3)
            self.after(0, lambda: self.log_to_console(f"[+] Arena oluşturuldu! ({res})", "success"))
        except Exception as e:
            self.after(0, lambda: self._on_send_error(str(e)))

    def action_broadcast(self):
        msg = self.broadcast_entry.get().strip()
        if not msg:
            return
        
        # Ekranın ortasına büyük sarı title gönder
        title_cmd = 'title @a title {"text":"' + msg + '","color":"yellow","bold":true}'
        self.send_command_thread(title_cmd)
        
        # Sohbetten duyuru gönder
        say_cmd = f"say [DUYURU] {msg}"
        self.send_command_thread(say_cmd)
        
        self.broadcast_entry.delete(0, "end")


    # --- GENEL YARDIMCI FONKSİYONLAR ---
    def log_to_console(self, message, message_type="info"):
        self.console_textbox.configure(state="normal")
        self.console_textbox.tag_config("error", foreground="#ff4d4d")
        self.console_textbox.tag_config("success", foreground="#00e676")
        self.console_textbox.tag_config("info", foreground="#cccccc")
        self.console_textbox.tag_config("command", foreground="#4dabf7")

        self.console_textbox.insert("end", message + "\n", message_type)
        self.console_textbox.see("end")
        self.console_textbox.configure(state="disabled")

    def set_gui_state(self, connected):
        state = "normal" if connected else "disabled"
        entry_state = "disabled" if connected else "normal"

        self.ip_entry.configure(state=entry_state)
        self.port_entry.configure(state=entry_state)
        self.password_entry.configure(state=entry_state)
        
        self.connect_btn.configure(state="disabled" if connected else "normal")
        self.disconnect_btn.configure(state="normal" if connected else "disabled")

        self.btn_save.configure(state=state)
        self.command_entry.configure(state=state)
        self.send_btn.configure(state=state)

        # Sunucu tabı
        for btn in self.server_buttons:
            if btn == self.btn_restart and connected and not self.is_bukkit:
                continue # Bukkit değilse restart hep kapalı kalır
            btn.configure(state=state)
            
        # Admin tabı
        self.btn_refresh_players.configure(state=state)
        self.admin_dropdown.configure(state=state)
        self.btn_tp_all.configure(state=state)
        self.btn_punisher.configure(state=state)
        self.btn_event.configure(state=state)
        self.event_size_entry.configure(state=state)
        self.broadcast_entry.configure(state=state)
        self.btn_broadcast.configure(state=state)

    # --- AĞ (RCON) İŞLEMLERİ ---
    def connect_to_server(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        password = self.password_entry.get()

        if not ip or not port_str or not password:
            self.log_to_console("[!] Lütfen IP, Port ve Şifre alanlarının tamamını doldurun.", "error")
            return

        try:
            port = int(port_str)
        except ValueError:
            self.log_to_console("[!] Port numarası sadece rakamlardan oluşmalıdır.", "error")
            return

        self.log_to_console(f"[*] {ip}:{port} adresine bağlanılıyor...", "info")
        self.connect_btn.configure(state="disabled", text="Bağlanıyor...")

        threading.Thread(target=self._connect_thread_task, args=(ip, port, password), daemon=True).start()

    def _connect_thread_task(self, ip, port, password):
        try:
            self.rcon = MCRcon(ip, password, port=port, timeout=5)
            self.rcon.connect()
            self.after(0, self._on_connect_success)
        except MCRconException as e:
            self.after(0, self._on_connect_error, f"RCON Hatası: {str(e)}")
        except ConnectionRefusedError:
            self.after(0, self._on_connect_error, "Bağlantı Reddedildi (Sunucu kapalı veya port yanlış olabilir).")
        except socket.timeout:
            self.after(0, self._on_connect_error, "Zaman Aşımı (Sunucu yanıt vermedi. IP veya Port hatalı olabilir).")
        except Exception as e:
            self.after(0, self._on_connect_error, f"Beklenmeyen Hata: {str(e)}")

    def _on_connect_success(self):
        self.log_to_console("[+] Bağlantı başarılı! Komut gönderebilirsiniz.", "success")
        self.connect_btn.configure(text="Bağlan")
        self.set_gui_state(connected=True)
        self.command_entry.focus()
        
        # Sunucu sürümünü kontrol et (Paper / Bukkit)
        threading.Thread(target=self._check_server_version_task, daemon=True).start()

    def _check_server_version_task(self):
        import time
        time.sleep(1) # RCON bağlantısı tam oturmadan ilk komutun boş dönmesini engellemek için 1 saniye bekle
        try:
            raw_ver = self.rcon.command("version")
            ver = raw_ver.lower()
            if any(k in ver for k in ["paper", "spigot", "bukkit", "purpur"]):
                self.is_bukkit = True
                self.after(0, lambda: self.btn_restart.configure(state="normal"))
                self.after(0, lambda: self.log_to_console("[*] Bukkit/Paper sunucu algılandı. Yeniden Başlatma aktif.", "success"))
            else:
                self.is_bukkit = False
                self.after(0, lambda: self.btn_restart.configure(state="disabled"))
                # Gelen yanıtı da yazdıralım ki bir daha olursa ne geldiğini görelim
                clean_ver = re.sub(r'§[0-9a-fk-or]', '', raw_ver).strip()
                self.after(0, lambda: self.log_to_console(f"[*] Vanilla sunucu algılandı. (Sunucunun yanıtı: {clean_ver or 'Boş Yanıt'})", "info"))
        except:
            pass

    def _on_connect_error(self, error_msg):
        self.log_to_console(f"[-] Bağlantı hatası: {error_msg}", "error")
        self.connect_btn.configure(state="normal", text="Bağlan")
        if self.rcon:
            self.rcon.disconnect()
            self.rcon = None

    def disconnect_from_server(self):
        if self.rcon:
            try:
                self.rcon.disconnect()
            except Exception:
                pass
            self.rcon = None
            self.log_to_console("[*] Sunucu ile bağlantı kesildi.", "info")
            self.is_bukkit = False
            self.set_gui_state(connected=False)

    def send_command_thread(self, event_or_cmd=None):
        command = ""
        
        if hasattr(event_or_cmd, 'widget') or event_or_cmd is None:
            command = self.command_entry.get().strip()
            if command:
                self.add_to_history(command)
                self.command_entry.delete(0, "end") 
        else:
            command = event_or_cmd

        if not command:
            return

        if not self.rcon:
            self.log_to_console("[!] Sunucuya bağlı değilsiniz. Önce bağlanın!", "error")
            return

        self.log_to_console(f"> /{command}", "command")
        threading.Thread(target=self._send_thread_task, args=(command,), daemon=True).start()

    def _send_thread_task(self, command):
        try:
            response = self.rcon.command(command)
            # RCON dönüşündeki Minecraft renk kodlarını (Section Sign §) temizleyelim
            response = re.sub(r'§[0-9a-fk-or]', '', response)
            
            if response:
                self.after(0, self.log_to_console, response, "info")
            else:
                self.after(0, self.log_to_console, "(Komut uygulandı, sunucudan boş yanıt döndü.)", "info")
                
        except (socket.timeout, socket.error, MCRconException) as e:
            self.after(0, self._on_send_error, str(e))
            
    def _on_send_error(self, error_msg):
        self.log_to_console(f"[-] Komut gönderilirken ağ hatası oluştu: {error_msg}", "error")
        self.log_to_console("[!] Bağlantınız kopmuş olabilir.", "error")
        self.disconnect_from_server()

    # --- GÜNCELLEME KONTROLÜ ---
    def get_local_version(self):
        try:
            # PyInstaller ile derlendiğinde dosyalar sys._MEIPASS içine çıkartılır
            base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(__file__)
            with open(os.path.join(base_path, 'version.json'), 'r', encoding='utf-8') as f:
                return json.load(f).get('tag', 'v0.0.0')
        except Exception:
            return 'v0.0.0'

    def check_for_updates(self):
        threading.Thread(target=self._update_task, daemon=True).start()

    def _update_task(self):
        try:
            local_v = self.get_local_version()
            req = urllib.request.Request(
                "https://api.github.com/repos/Ciaodar/McrconPyPanel/releases/latest",
                headers={'User-Agent': 'MCRconPanel-Updater'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                remote_v = data.get("tag_name")
                # Eğer Github'daki versiyon lokalden farklı ise (ve dev env değilse)
                if remote_v and local_v != 'v0.0.0' and remote_v != local_v:
                    # Arayüzün kilitlenmemesi için Tkinter thread'ine gönder
                    self.after(2000, lambda: self.show_update_dialog(remote_v, data.get("body", "")))
        except Exception:
            pass # İnternet yoksa sessizce geç

    def show_update_dialog(self, new_version, release_notes):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Güncelleme Mevcut!")
        dialog.geometry("450x300")
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"🎉 Yeni Sürüm Mevcut! ({new_version})", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        
        textbox = ctk.CTkTextbox(dialog, width=400, height=120)
        textbox.pack(pady=10)
        textbox.insert("0.0", release_notes)
        textbox.configure(state="disabled")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_download = ctk.CTkButton(btn_frame, text="Şimdi İndir", fg_color="#28a745", hover_color="#218838",
                                     command=lambda: [webbrowser.open("https://ciaodar.github.io/McrconPyPanel/download"), dialog.destroy()])
        btn_download.pack(side="left", padx=10)

        btn_later = ctk.CTkButton(btn_frame, text="Daha Sonra", fg_color="#6c757d", hover_color="#5a6268", command=dialog.destroy)
        btn_later.pack(side="left", padx=10)

if __name__ == "__main__":
    app = MinecraftRconGUI()
    app.mainloop()
