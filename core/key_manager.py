"""
core/key_manager.py

Logika za upravljanje RSA parovima ključeva: generisanje, uvoz, izvoz,
brisanje. Ovde su definisani SAMO potpisi metoda i TODO komentari -
implementaciju treba dodati (npr. korišćenjem `cryptography` ili `rsa`
Python modula, što je dozvoljeno prema zadatku).

Zabranjeno je koristiti modul koji već implementira čitavu PGP šemu
(npr. py-pgp) - dozvoljeni su samo moduli za osnovne kriptografske
primitive (RSA, AES, SHA-1, itd.).
"""

from typing import Optional, Tuple
from storage.keyring import KeyRing, PublicKeyEntry, PrivateKeyEntry


class KeyManager:
    def __init__(self, keyring: KeyRing):
        self.keyring = keyring

    def generate_key_pair(self, name: str, email: str, key_size: int,
                           password: str) -> Tuple[PublicKeyEntry, PrivateKeyEntry]:
        """
        Generiše novi RSA par ključeva (key_size: 1024 ili 2048 bita),
        čuva privatni ključ enkriptovan zadatom lozinkom, i dodaje
        odgovarajuće zapise u keyring.

        TODO (studenti):
            1. Generisati RSA par ključeva (npr. cryptography.hazmat...).
            2. Izračunati fingerprint / key_id.
            3. Serijalizovati javni ključ u PEM format.
            4. Serijalizovati privatni ključ u PEM format, enkriptovan
               lozinkom (npr. BestAvailableEncryption(password)).
            5. Kreirati PublicKeyEntry i PrivateKeyEntry i ubaciti ih
               u self.keyring.
        """
        raise NotImplementedError("TODO: implementirati generisanje RSA ključeva")

    def delete_key_pair(self, key_id: str) -> None:
        """
        Briše par ključeva (javni i privatni) iz prstena ključeva.

        TODO (studenti): obrisati odgovarajuće zapise iz keyring-a.
        """
        raise NotImplementedError("TODO: implementirati brisanje ključeva")

    def import_public_key(self, pem_path: str) -> PublicKeyEntry:
        """
        Uvozi javni ključ iz .pem fajla i dodaje ga u prsten javnih
        ključeva.

        TODO (studenti):
            1. Pročitati .pem fajl sa diska.
            2. Parsirati javni ključ.
            3. Izvući/izračunati potrebne metapodatke (ime, mejl, key_id...).
            4. Dodati u keyring.
        """
        raise NotImplementedError("TODO: implementirati uvoz javnog ključa")

    def import_key_pair(self, pem_path: str, password: str) -> Tuple[PublicKeyEntry, PrivateKeyEntry]:
        """
        Uvozi ceo par ključeva (javni + privatni) iz .pem fajla.

        TODO (studenti): implementirati učitavanje i parsiranje para
        ključeva, uz proveru lozinke za privatni ključ.
        """
        raise NotImplementedError("TODO: implementirati uvoz para ključeva")

    def export_public_key(self, key_id: str, destination_path: str) -> None:
        """
        Izvozi javni dio ključa u .pem format na zadatu destinaciju.

        TODO (studenti): implementirati serijalizaciju i upis u fajl.
        """
        raise NotImplementedError("TODO: implementirati izvoz javnog ključa")

    def export_key_pair(self, key_id: str, password: str, destination_path: str) -> None:
        """
        Izvozi ceo par ključeva (javni + privatni) u .pem format.

        TODO (studenti): implementirati serijalizaciju (uz proveru
        lozinke za pristup privatnom ključu) i upis u fajl.
        """
        raise NotImplementedError("TODO: implementirati izvoz para ključeva")

    def verify_password(self, key_id: str, password: str) -> bool:
        """
        Provera da li je uneta lozinka ispravna za dati privatni ključ.
        Koristi se svaki put kada je potreban pristup privatnom ključu
        (potpisivanje, dekripcija, izvoz privatnog ključa...).

        TODO (studenti): implementirati stvarnu proveru (npr. pokušaj
        dekripcije privatnog ključa sa datom lozinkom).
        """
        raise NotImplementedError("TODO: implementirati proveru lozinke")
