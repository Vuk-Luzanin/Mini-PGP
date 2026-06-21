"""
core/pgp_engine.py

Logika za slanje i prijem PGP poruka: potpisivanje (autentičnost),
enkripcija (tajnost), kompresija i radix-64 konverzija, kao i
odgovarajuće inverzne operacije pri prijemu.

Ovo su SAMO potpisi metoda sa TODO komentarima - implementaciju
kriptografskih operacija treba dodati.

Podržani simetrični algoritmi (potrebno je implementirati BAREM 2 od
4): TripleDES, AES128, Cast5, IDEA.
Hash funkcija za potpisivanje: SHA-1.
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class SymmetricAlgorithm(Enum):
    TRIPLE_DES = "TripleDES"
    AES128 = "AES128"
    CAST5 = "Cast5"
    IDEA = "IDEA"


@dataclass
class SendOptions:
    """Opcije koje korisnik bira prilikom slanja poruke."""
    sign: bool = False
    sign_private_key_id: Optional[str] = None      # koji privatni ključ se koristi za potpis
    encrypt: bool = False
    encrypt_public_key_id: Optional[str] = None    # koji javni ključ se koristi za enkripciju
    symmetric_algorithm: Optional[SymmetricAlgorithm] = None
    compress: bool = False
    radix64: bool = False


@dataclass
class ReceiveResult:
    """Rezultat obrade primljene poruke."""
    success: bool
    error_message: Optional[str] = None
    was_signed: bool = False
    signature_valid: Optional[bool] = None
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None
    was_encrypted: bool = False
    was_compressed: bool = False
    was_radix64: bool = False
    plaintext: Optional[bytes] = None


class PGPEngine:
    """
    Glavna klasa koja implementira PGP operacije.

    Struktura izlazne datoteke (pri slanju) treba da odgovara strukturi
    obrađenoj na vežbama (RFC 4880 kao referenca za inspiraciju, ali ne
    obavezno identično). Studenti treba da definišu i implementiraju
    format zaglavlja/paketa same datoteke.
    """

    def __init__(self, key_manager):
        self.key_manager = key_manager

    # ------------------------------------------------------------------
    # SLANJE PORUKE
    # ------------------------------------------------------------------

    def send_message(self, message_text: str, options: SendOptions,
                      sign_password: Optional[str], destination_path: str) -> None:
        """
        Glavna funkcija za slanje poruke. Na osnovu zadatih opcija
        (`options`) treba da:

          1. (opciono) potpiše poruku:
             - izračuna SHA-1 hash poruke
             - potpiše hash privatnim ključem (uz proveru lozinke
               preko self.key_manager.verify_password)
          2. (opciono) komprimuje poruku (npr. zlib)
          3. (opciono) enkriptuje poruku:
             - generiše sesijski (simetrični) ključ
             - enkriptuje poruku izabranim simetričnim algoritmom
             - enkriptuje sesijski ključ javnim RSA ključem primaoca
          4. (opciono) konvertuje rezultat u radix-64 (Base64) format
          5. Upiše sve potrebne podatke (paket potpisa, paket sesijskog
             ključa, enkriptovani/plain sadržaj, indikatori koje opcije
             su korišćene, itd.) u izlaznu datoteku na `destination_path`.

        TODO (studenti): implementirati kompletnu logiku iznad.
        """
        raise NotImplementedError("TODO: implementirati slanje poruke")

    # ------------------------------------------------------------------
    # PRIJEM PORUKE
    # ------------------------------------------------------------------

    def receive_message(self, source_path: str,
                         decrypt_password: Optional[str]) -> ReceiveResult:
        """
        Glavna funkcija za prijem/obradu poruke. Treba da:

          1. Pročita datoteku sa `source_path` i prepozna koji paketi
             postoje (potpis, sesijski ključ, enkriptovani sadržaj,
             radix-64, kompresija, itd.)
          2. (ako je radix-64 korišćen) dekodira iz Base64
          3. (ako je enkriptovano) dekriptuje sesijski ključ privatnim
             RSA ključem (uz proveru lozinke), zatim dekriptuje sadržaj
             simetričnim algoritmom
          4. (ako je komprimovano) dekomprimuje sadržaj
          5. (ako je potpisano) izračuna SHA-1 hash dobijenog sadržaja i
             verifikuje potpis javnim ključem potpisnika; popuni
             informacije o autoru potpisa
          6. Vrati ReceiveResult sa svim relevantnim informacijama
             (uspeh/neuspeh, da li je potpis valjan, ko je potpisnik,
             dekriptovani tekst poruke, itd.)

        TODO (studenti): implementirati kompletnu logiku iznad. U
        slučaju neuspešne dekripcije ili verifikacije, vratiti
        ReceiveResult(success=False, error_message=<opis greške>, ...).
        """
        raise NotImplementedError("TODO: implementirati prijem poruke")
