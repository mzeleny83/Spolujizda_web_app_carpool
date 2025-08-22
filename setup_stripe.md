# 💳 Nastavení Stripe plateb

## 1. Registrace na Stripe

1. Jdi na **stripe.com**
2. **Sign up** → Vytvoř účet
3. **Activate account** → Ověř email a telefon

## 2. Získání API klíčů

1. V Stripe dashboardu jdi na **Developers → API keys**
2. Zkopíruj:
   - **Publishable key** (pk_test_...)
   - **Secret key** (sk_test_...)

## 3. Nastavení v aplikaci

### Pro lokální testování:
```bash
# Windows
set STRIPE_SECRET_KEY=sk_test_tvuj_secret_key
set STRIPE_PUBLISHABLE_KEY=pk_test_tvuj_publishable_key
python main_app.py
```

### Pro Railway nasazení:
1. V Railway projektu jdi na **Variables**
2. Přidej:
   - `STRIPE_SECRET_KEY` = `sk_test_...`
   - `STRIPE_PUBLISHABLE_KEY` = `pk_test_...`

## 4. Testovací karty

Pro testování použij tyto karty:
- **Úspěšná platba**: 4242 4242 4242 4242
- **Odmítnutá platba**: 4000 0000 0000 0002
- **Datum**: Jakýkoli budoucí
- **CVC**: Jakékoli 3 číslice

## 5. Jak to funguje

1. Uživatel klikne **"💳 Zaplatit a rezervovat"**
2. Přesměruje se na Stripe Checkout
3. Zadá kartu a zaplatí
4. Vrátí se zpět s potvrzením
5. Místo je automaticky rezervováno

## 6. Produkční režim

Pro ostrý provoz:
1. V Stripe přepni na **Live mode**
2. Získej live klíče (pk_live_... a sk_live_...)
3. Nastav v Railway Variables
4. Aktivuj webhook pro automatické rezervace

## 7. Poplatky

- **Stripe poplatek**: 1.4% + 5 Kč za transakci
- **Příklad**: Jízda za 300 Kč = poplatek ~9 Kč