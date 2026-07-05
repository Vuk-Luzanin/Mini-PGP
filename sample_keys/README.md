# Format fajlova sa ključevima

Ovaj folder sadrži dve vrste fajlova sa ključevima: standardne **PEM**
fajlove sa javnim ključem i prilagođene **MINI-PGP KEY BUNDLE** fajlove
sa čitavim parom ključeva. Iako oba izgledaju slično (tekstualni blok
omeđen sa `-----BEGIN ...-----` / `-----END ...-----`), njihov sadržaj
i namena se razlikuju.

---

## 1. Standardni PEM javni ključ

```
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCy+EDe2rvjktHg3AtfwdzQ5tcS
fp3S9VhjD1ZNYBBeipiKQtIqXz8KV/WP4LXONrEVmMxSPwUVgo7mEFRpD6j1LCEn
DzZ9piZUzVDy5eOpCFVVIXDHRXR4FJ1j5BRkLwUpUOqkZSocr9Gfg3lC1Ye7Rt0A
DHdzW8iQklfWCvDUhwIDAQAB
-----END PUBLIC KEY-----
```

**Šta je ovo:** ovo je pravi, standardan X.509/PEM zapis javnog RSA
ključa (`SubjectPublicKeyInfo`), potpuno kompatibilan sa OpenSSL-om i
svim ostalim alatima koji rade sa PEM formatom.

**Struktura:**
- `-----BEGIN PUBLIC KEY-----` / `-----END PUBLIC KEY-----` — fiksni
  markeri koje prepoznaje svaki PEM parser.
- Tekst između markera je **Base64-enkodiran DER zapis** ASN.1
  strukture koja sadrži RSA algoritam i sam javni ključ (modulus `n` i
  eksponent `e`).

**Kada se koristi:** kada se izvozi *samo javni ključ* nekog para
(funkcija `export_public_key` u aplikaciji), npr. da bi se podelio sa
drugom osobom radi provere potpisa ili enkripcije poruka namenjenih
vama.

**Napomena:** ovaj fajl ne sadrži nikakvu tajnu — javni ključ je po
definiciji javan i bezbedno ga je deliti.

---

## 2. MINI-PGP KEY BUNDLE (ceo par ključeva)

```
-----BEGIN MINI-PGP KEY BUNDLE-----
eyJjcmVhdGVkX2F0IjogIjIwMjYtMDctMDVUMTU6NTc6MzkuNzU3ODI5KzAwOjAwIiwg...
-----END MINI-PGP KEY BUNDLE-----
```

**Šta je ovo:** ovo **nije** standardni PEM format, iako liči na
njega (isti stil markera). Sadržaj između `BEGIN`/`END` linija je
**Base64-enkodiran JSON objekat** koji nosi i javni i (enkriptovani)
privatni ključ zajedno, sa svim metapodacima potrebnim da se par
ponovo učita u drugu instalaciju aplikacije.

**Kada se koristi:** kada se izvozi/uvozi *ceo par ključeva*
(funkcije `export_key_pair` / `import_key_pair`), npr. za backup ili
za prenos identiteta na drugi računar.

### Struktura spoljnog JSON-a

Nakon Base64-dekodiranja sadržaja između markera, dobija se JSON
ovog oblika:

```json
{
  "version": 1,
  "key_id": "909257d60af0d487",
  "user_name": "Sample User",
  "user_email": "sample.user@example.com",
  "key_size": 1024,
  "created_at": "2026-07-05T15:57:39.757829+00:00",
  "public_key_pem": "<Base64 od standardnog PEM javnog ključa, tačka 1>",
  "private_key_blob": "<Base64 od ugnježdenog JSON-a, vidi ispod>"
}
```

| Polje | Značenje |
|---|---|
| `version` | Verzija formata bundle-a (trenutno `1`) |
| `key_id` | 16 heksadecimalnih cifara — donjih 64 bita modulusa `n` javnog ključa, koristi se kao identifikator para |
| `user_name`, `user_email` | Identitet vezan za par ključeva |
| `key_size` | Veličina RSA ključa u bitima (1024 ili 2048) |
| `created_at` | Vreme generisanja para (ISO 8601, UTC) |
| `public_key_pem` | Ceo standardni PEM javni ključ (tačka 1), samo dodatno Base64-upakovan da bi stao u JSON kao string |
| `private_key_blob` | Enkriptovani privatni ključ, upakovan u sopstveni JSON (vidi tačku 3) |

### 3. Struktura `private_key_blob` (enkriptovani privatni ključ)

Nakon Base64-dekodiranja vrednosti polja `private_key_blob`, dobija se
još jedan, ugnježdeni JSON:

```json
{
  "cipher": "CAST5-CBC",
  "iv": "<Base64, 8 bajtova>",
  "ciphertext": "<Base64, šifrovani privatni ključ>"
}
```

| Polje | Značenje |
|---|---|
| `cipher` | Algoritam i mod korišćen za zaštitu privatnog ključa — **CAST5 u CBC modu** |
| `iv` | Inicijalizacioni vektor (8 bajtova, jer CAST5 ima blok veličine 8 bajtova) |
| `ciphertext` | Sam privatni ključ (u PKCS#8/DER formatu, sa PKCS#7 dopunom), enkriptovan CAST5-CBC ključem |

**Ključ za enkripciju** se izvodi iz lozinke koju korisnik unese
prilikom generisanja para:

```
kljuc = SHA1(lozinka)[:16 bajtova]
```

**Bez tačne lozinke privatni ključ se ne može dešifrovati** — lozinka
se nigde ne čuva, samo se koristi trenutno da izvede ključ za
CAST5.

---

## Zašto ovakva struktura (ugnježdeni JSON u JSON-u)?

Postoje dva sloja pakovanja iz praktičnog razloga:

1. **Unutrašnji sloj** (`cipher` / `iv` / `ciphertext`) predstavlja
   samostalnu jedinicu — "enkriptovani privatni ključ" — koja se
   koristi i nezavisno, npr. čuva se u internoj bazi/keyring-u
   aplikacije čak i kad se par ključeva ne izvozi nigde.
2. **Spoljašnji sloj** (`MINI-PGP KEY BUNDLE`) samo pakuje tu istu
   jedinicu zajedno sa javnim ključem i metapodacima, radi lakšeg
   prenosa *celog identiteta* u jednom fajlu.

Markeri `-----BEGIN .../END...-----` su namerno u PEM stilu radi
prepoznatljivosti (fajl liči na kriptografski fajl kad se otvori u
tekst editoru), ali format sadržaja (JSON umesto ASN.1/DER) je
specifičan za ovu aplikaciju — bundle fajlove ne treba pokušavati
učitavati standardnim PEM/X.509 alatima (npr. `openssl`), oni će ih
odbiti kao neispravne.

---

## Pregled formata

| Fajl / marker | Standardan format? | Sadrži privatni ključ? | Namena |
|---|---|---|---|
| `-----BEGIN PUBLIC KEY-----` | Da (X.509/PEM) | Ne | Deljenje samo javnog ključa |
| `-----BEGIN MINI-PGP KEY BUNDLE-----` | Ne (prilagođen, Base64+JSON) | Da (enkriptovan, zaštićen lozinkom) | Backup / prenos celog para ključeva |