# MCRcon Panel Pro 🚀

Minecraft sunucularınızı RCON protokolü üzerinden profesyonel, modern ve güvenli bir şekilde yönetmek için geliştirilmiş Python tabanlı masaüstü uygulamasıdır.

<p align="center">
  <img src="docs/screenshot.png" alt="MCRcon Panel">
</p>

## ✨ Özellikler

* **Modern Arayüz (Dark Mode):** `CustomTkinter` ile hazırlanmış, donmayan (Non-blocking) ve göze hitap eden sekmeli tasarım.
* **Akıllı Sürüm Dedektörü:** Sunucuya bağlandığında Vanilla/Paper/Bukkit ayrımını yaparak kullanılamayacak komutları (örn: `/restart`) otomatik gizler.
* **Zengin Yönetici Araçları:**
  * **Event Alanı İnşası:** Tek tuşla seçili yöneticinin etrafına üstü açık Bedrock kutusu döşer. (Matematiksel `/fill` algoritmaları kullanır).
  * **Cezalandırıcı Sopa:** Seçili oyuncuya "Savurma 50" (Knockback 50) basılı, "Cezalandırıcı" adında bir sopa verir.
  * **Herkesi Çek:** Tüm oyuncuları anında belirlediğiniz adminin yanına çeker (`/tp @a`).
  * **Duyuru (Broadcast):** Ekranın ortasına büyük (Title) ve sohbete mesaj gönderir.
* **Komut Geçmişi:** Tıpkı oyun içindeki gibi Yukarı (↑) ok tuşuyla yazdığınız son 10 komuta ulaşabilirsiniz.
* **Güvenli Aksiyonlar:** Yanlışlıkla sunucuyu kapatmanızı engellemek için 3 aşamalı (Onay) Stop butonu.

## 📥 Kurulum & Kullanım

MCRcon Panel'i kullanmanın iki yolu vardır:

### 1. Yol: Hazır Uygulama Olarak (En Kolayı)
Eğer Python kurmakla uğraşmak istemiyorsanız, projenin **GitHub Releases** veya **Actions** sekmesinden işletim sisteminize uygun olan sürümü (`.exe` vb.) indirebilirsiniz. Sadece çift tıklayarak çalışır.

### 2. Yol: Kaynak Koddan (Geliştiriciler İçin)
1. Bilgisayarınızda Python 3.10 veya üzeri bir sürüm kurulu olduğundan emin olun.
2. Repoyu bilgisayarınıza klonlayın:
   ```bash
   git clone https://github.com/USERNAME/MCRconPyPanel.git
   cd MCRconPyPanel
   ```
3. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install customtkinter mcrcon
   ```
4. Uygulamayı başlatın:
   ```bash
   python main.py
   ```

## 🛠️ Kendi `.exe` Dosyanı Derle
Kendi ikonunuzu ekleyerek bu paneli `.exe` haline getirebilirsiniz:
1. Proje klasörüne `icon.ico` adında bir resim atın.
2. `python build_exe.py` komutunu çalıştırın.
3. Arkanıza yaslanın. `dist/` klasörü içinde yeni exe dosyanız belirecektir!

## 🌐 Tanıtım Sitesi
Bu projenin GitHub Pages ile yayınlanabilen modern bir tanıtım sitesi `/docs` klasörü altında bulunmaktadır. Repo ayarlarınızdan `docs` klasörünü Pages kaynağı olarak seçerseniz siteniz anında aktif olur.

## 🤝 Katkıda Bulunma
Her türlü Pull Request (PR) veya Hata Bildirimi (Issue) memnuniyetle kabul edilir. Lütfen büyük değişiklikler için önce bir "Issue" açarak tartışmaya sunun.

---
*MCRcon Panel Pro - Sunucunun kontrolü artık tam ellerinde.*
