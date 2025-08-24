# Migrace na sveztese.cz

## 1. Příprava souborů
Zkopírujte tyto soubory na server:
- main_app.py
- spolujizda.db
- requirements.txt
- templates/ (celá složka)
- static/ (celá složka)

## 2. Instalace na serveru
```bash
cd /var/www/sveztese.cz
pip3 install flask
python3 main_app.py
```

## 3. Nginx konfigurace
```nginx
server {
    listen 80;
    server_name sveztese.cz www.sveztese.cz;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 4. SSL certifikát
```bash
certbot --nginx -d sveztese.cz -d www.sveztese.cz
```

## 5. Systemd služba
```ini
[Unit]
Description=Sveztese Flask App
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/sveztese.cz
ExecStart=/usr/bin/python3 main_app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 6. Spuštění
```bash
sudo systemctl enable sveztese
sudo systemctl start sveztese
```