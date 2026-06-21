"""
storage/keyring.py

Definicije struktura podataka za čuvanje PGP ključeva (prsten javnih
i privatnih ključeva).

NAPOMENA: Ovo su samo predložene strukture (skeleton). Studenti treba
da implementiraju stvarno čuvanje (npr. u memoriji za vreme rada
aplikacije, i/ili serijalizaciju na disk) i da popune sva polja
stvarnim vrednostima nakon generisanja/uvoza ključeva.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class PublicKeyEntry:
    """Stavka u prstenu javnih ključeva."""
    key_id: str            # npr. poslednjih 8 hex cifara fingerprinta
    user_name: str
    user_email: str
    key_size: int           # 1024 ili 2048
    created_at: datetime
    public_key_pem: Optional[bytes] = None   # PEM enkodiran javni ključ
    fingerprint: Optional[str] = None
    # TODO: dodati polja po potrebi (npr. algoritam, trust nivo, itd.)


@dataclass
class PrivateKeyEntry:
    """Stavka u prstenu privatnih ključeva.

    Privatni ključ se NE čuva u plain-textu u memoriji van trenutka
    kada je korisnik otključao lozinkom - studenti treba da osmisle
    bezbedan način čuvanja (npr. enkriptovan na disku, ili samo
    referenca + lozinka se traži pri svakom pristupu).
    """
    key_id: str
    user_name: str
    user_email: str
    key_size: int
    created_at: datetime
    encrypted_private_key_pem: Optional[bytes] = None  # PEM, enkriptovan lozinkom
    fingerprint: Optional[str] = None
    # TODO: dodati polja po potrebi


class KeyRing:
    """
    Glavna struktura koja čuva prsten javnih i privatnih ključeva.

    TODO (studenti):
        - Implementirati metode za generisanje novog para ključeva
          (generate_key_pair) - trenutno samo stub.
        - Implementirati uvoz/izvoz u .pem formatu.
        - Implementirati brisanje ključeva.
        - Implementirati persistenciju (čuvanje na disk / učitavanje).
    """

    def __init__(self):
        self.public_keys: List[PublicKeyEntry] = []
        self.private_keys: List[PrivateKeyEntry] = []

    # ---------------- Generisanje / brisanje ----------------

    def add_public_key(self, entry: PublicKeyEntry):
        self.public_keys.append(entry)

    def add_private_key(self, entry: PrivateKeyEntry):
        self.private_keys.append(entry)

    def remove_public_key(self, key_id: str):
        self.public_keys = [k for k in self.public_keys if k.key_id != key_id]

    def remove_private_key(self, key_id: str):
        self.private_keys = [k for k in self.private_keys if k.key_id != key_id]

    def find_public_key(self, key_id: str) -> Optional[PublicKeyEntry]:
        for k in self.public_keys:
            if k.key_id == key_id:
                return k
        return None

    def find_private_key(self, key_id: str) -> Optional[PrivateKeyEntry]:
        for k in self.private_keys:
            if k.key_id == key_id:
                return k
        return None
