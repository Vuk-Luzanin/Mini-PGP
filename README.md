# PGP Aplikacija — Skeleton projekta (Kivy GUI)

Ovo je **skeleton** (GUI bez implementirane PGP logike) za projektni zadatak
iz predmeta *Zaštita podataka*. GUI je urađen u **Kivy** biblioteci (instalira
se isključivo preko `pip`, bez potrebe za `sudo`/sistemskim paketima) i
povezan je sa "praznim" (stub) funkcijama u `core/` modulima — te funkcije
trenutno bacaju `NotImplementedError` i to je potrebno implementirati.

## Pokretanje

```bash
pip install -r requirements.txt
python main.py
```

Nije potreban `sudo` — `kivy` i `cryptography` su čisti Python paketi koji
se instaliraju u korisničkom prostoru (ili virtualnom environment-u).

> Napomena: pri prvom pokretanju Kivy može ispisati dosta log linija u
> konzoli (inicijalizacija grafičkog konteksta) — to je normalno.

## Struktura projekta

```
pgp_project/
├── main.py                            # Ulazna tačka aplikacije
├── requirements.txt
├── core/
│   ├── key_manager.py                  # TODO: generisanje/uvoz/izvoz/brisanje RSA ključeva
│   └── pgp_engine.py                   # TODO: slanje/prijem poruke (enkripcija, potpis, kompresija, radix-64)
├── storage/
│   └── keyring.py                      # Strukture za čuvanje prstena javnih/privatnih ključeva
└── gui/
    ├── main_app.py                      # Glavna Kivy App klasa, TabbedPanel navigacija
    ├── key_management_screen.py         # Prikaz prstena ključeva + akcije
    ├── key_generation_popup.py          # Popup za generisanje novog para ključeva
    ├── key_import_export_popup.py       # Popup-ovi za uvoz/izvoz ključeva
    ├── send_message_screen.py           # Ekran za slanje poruke
    ├── receive_message_screen.py        # Ekran za prijem poruke
    ├── file_chooser_popup.py            # Pomoćni file-chooser popup (otvori/sačuvaj)
    └── message_popup.py                 # Pomoćni info/confirm/password popup
```

## Šta je već urađeno (GUI)

- **Upravljanje ključevima** (tab "Ključevi"): liste javnih i privatnih
  ključeva (ID, ime, mejl, veličina, datum kreiranja), dugmići za
  generisanje, uvoz, izvoz i brisanje. Popup za generisanje traži ime,
  mejl, veličinu ključa (1024/2048) i lozinku (sa potvrdom). Popup-ovi za
  uvoz/izvoz razlikuju "samo javni ključ" i "ceo par ključeva" (sa
  lozinkom za privatni deo).
- **Slanje poruke** (tab "Slanje poruke"): polje za unos teksta poruke,
  checkbox-ovi za potpisivanje (uz izbor privatnog ključa iz spinner-a),
  enkripciju (uz izbor javnog ključa primaoca i simetričnog algoritma),
  kompresiju i radix-64 konverziju. Čuvanje rezultata na izabranu
  lokaciju preko ugrađenog file-chooser popup-a.
- **Prijem poruke** (tab "Prijem poruke"): izbor datoteke, dugme za
  obradu, prikaz statusa (uspeh/greška), informacija o validnosti
  potpisa i autoru, kao i da li je poruka bila
  enkriptovana/komprimovana/radix-64 kodirana. Prikaz dekriptovane
  poruke i mogućnost čuvanja na disk.

Sve greške/izuzeci iz `core/` modula (`NotImplementedError` i ostali) se
hvataju i prikazuju korisniku kroz popup poruku, tako da se GUI ne
"ruši" dok logika nije implementirana — videćete poruku
"Nije implementirano" kada testirate dugmiće.

## Šta TREBA implementirati (core logika)

Ovaj deo je **identičan** bez obzira na GUI biblioteku — `core/` i
`storage/` moduli ne zavise od Kivy-ja.

### `core/key_manager.py`
- `generate_key_pair(name, email, key_size, password)` — generisanje RSA
  para, čuvanje privatnog ključa enkriptovanog lozinkom, dodavanje u
  `KeyRing`.
- `delete_key_pair(key_id)`
- `import_public_key(pem_path)` / `import_key_pair(pem_path, password)`
- `export_public_key(key_id, destination_path)` /
  `export_key_pair(key_id, password, destination_path)`
- `verify_password(key_id, password)`

### `core/pgp_engine.py`
- `send_message(message_text, options, sign_password, destination_path)`
  — potpisivanje (SHA-1 + RSA), enkripcija (RSA + simetrični alg. po
  izboru: TripleDES/AES128/Cast5/IDEA — minimum 2 od 4), kompresija,
  radix-64, i upis u fajl po formatu koji sami definišete (inspirisano
  RFC 4880 / vežbama).
- `receive_message(source_path, decrypt_password)` — parsiranje fajla,
  dekripcija, dekompresija, radix-64 dekodiranje, verifikacija potpisa,
  vraćanje `ReceiveResult`.

### `storage/keyring.py`
Strukture (`PublicKeyEntry`, `PrivateKeyEntry`, `KeyRing`) su predložene
— možete ih proširiti po potrebi (npr. dodati polje za algoritam,
trust nivo, persistenciju na disk, itd.).

## Napomena o podeli posla (tim od 2 studenta)

Zadatak **eksplicitno zabranjuje** podelu na "jedan radi logiku, drugi
GUI". Predlog podele po funkcionalnostima (svaki student radi GUI + logiku
za svoj deo):

- **Student A**: upravljanje ključevima (generisanje, uvoz/izvoz,
  brisanje) — `key_manager.py` + `key_management_screen.py` +
  `key_generation_popup.py` + `key_import_export_popup.py`.
- **Student B**: slanje i prijem poruka (enkripcija, potpis, kompresija,
  radix-64) — `pgp_engine.py` + `send_message_screen.py` +
  `receive_message_screen.py`.

Obavezno pažljivo pročitajte kompletan tekst zadatka pre početka
implementacije i uvedite razumne pretpostavke gde nešto nije precizno
definisano.
