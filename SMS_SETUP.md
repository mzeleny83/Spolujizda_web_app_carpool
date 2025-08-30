# 📱 SMS ověření

## Vonage SMS API:

1. Registrujte se na https://www.vonage.com/
2. Získejte API key a secret
3. V `app.py` nahraďte:
   - `api_key = "your_vonage_api_key"`
   - `api_secret = "your_vonage_api_secret"`

## Jak to funguje:
1. Uživatel zadá své telefonní číslo
2. Server pošle SMS s kódem na jeho telefon
3. Uživatel zadá kód a dokončí registraci

## Cena: ~0.05€ za SMS