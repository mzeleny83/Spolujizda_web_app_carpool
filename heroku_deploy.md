# Nasazení na Heroku s vlastní doménou

## 1. Vytvoření Heroku aplikace
```bash
heroku create sveztese-app
```

## 2. Deploy aplikace
```bash
git add .
git commit -m "Deploy spolujizda app"
git push heroku main
```

## 3. Nastavení vlastní domény
```bash
# Přidání domény do Heroku
heroku domains:add sveztese.cz
heroku domains:add www.sveztese.cz

# Získání DNS targetu
heroku domains
```

## 4. DNS nastavení u registrátora
```
Typ: CNAME
Název: www
Hodnota: [heroku-dns-target].herokudns.com

Typ: ALIAS/ANAME (nebo A record)
Název: @
Hodnota: [heroku-dns-target].herokudns.com
```

## 5. SSL certifikát
```bash
heroku certs:auto:enable
```

## 6. Výsledek
- Aplikace běží na: https://sveztese-app.herokuapp.com
- Vlastní doména: https://sveztese.cz
- Automatické HTTPS přesměrování