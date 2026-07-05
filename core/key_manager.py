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

import base64
import json
import os
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Optional, Tuple

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives import padding, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from storage.keyring import KeyRing, PublicKeyEntry, PrivateKeyEntry


class KeyManager:
    _PAIR_BUNDLE_BEGIN = "-----BEGIN MINI-PGP KEY BUNDLE-----"
    _PAIR_BUNDLE_END = "-----END MINI-PGP KEY BUNDLE-----"

    def __init__(self, keyring: KeyRing):
        self.keyring = keyring

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    # key_id je string od 16 heksadecimalnih cifara (najniži 64 bita javnog ključa - n)
    # create key_id from public key object
    @staticmethod
    def _public_key_key_id(public_key) -> str:
        public_numbers = public_key.public_numbers()
        key_id_int = public_numbers.n & ((1 << 64) - 1)
        return f"{key_id_int:016x}"

    # CAST-128 (CAST5) ocekuje kljuc duzine 16 bajtova (128 bita)
    # hash od lozinke se skrati na 16 bajtova i koristi kao kljuc za CAST5
    @staticmethod
    def _password_key(password: str) -> bytes:
        return sha1(password.encode("utf-8")).digest()[:16]

    @staticmethod
    def _encrypt_private_key(private_key, password: str) -> bytes:
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,                # binary DER format
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # hash od password-a - key
        key = KeyManager._password_key(password)
        iv = os.urandom(8)
        encryptor = Cipher(algorithms.CAST5(key), modes.CBC(iv)).encryptor()

        # add padding
        padder = padding.PKCS7(algorithms.CAST5.block_size).padder()
        padded = padder.update(private_bytes) + padder.finalize()       # + for bytes is concatenation
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        # save all info
        payload = {
            "cipher": "CAST5-CBC",
            "iv": base64.b64encode(iv).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }
    
        # dumps - from python object to json string, sort_keys=True for deterministic output
        return json.dumps(payload, sort_keys=True).encode("utf-8")      # bytes for writing to file

    @staticmethod
    def _decrypt_private_key_blob(encrypted_blob: bytes, password: str):
        try:
            payload = json.loads(encrypted_blob.decode("utf-8"))

            if payload.get("cipher") != "CAST5-CBC":
                raise ValueError("Nepodržan algoritam za zaštitu privatnog ključa.")

            iv = base64.b64decode(payload["iv"])
            ciphertext = base64.b64decode(payload["ciphertext"])

            key = KeyManager._password_key(password)
            decryptor = Cipher(algorithms.CAST5(key), modes.CBC(iv)).decryptor()

            padded = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(algorithms.CAST5.block_size).unpadder()
            private_bytes = unpadder.update(padded) + unpadder.finalize()

            return serialization.load_der_private_key(private_bytes, password=None)
        except ValueError:
            raise
        except Exception:
            return None

    # spakuj kljuceve u fajl format
    @staticmethod
    def _serialize_pair_bundle(public_entry: PublicKeyEntry, private_entry: PrivateKeyEntry) -> bytes:
        payload = {
            "version": 1,
            "key_id": public_entry.key_id,
            "user_name": public_entry.user_name,
            "user_email": public_entry.user_email,
            "key_size": public_entry.key_size,
            "created_at": public_entry.created_at.isoformat(),
            "public_key_pem": base64.b64encode(public_entry.public_key_pem or b"").decode("ascii"),
            "private_key_blob": base64.b64encode(private_entry.encrypted_private_key_pem or b"").decode("ascii"),
        }
        body = base64.b64encode(json.dumps(payload, sort_keys=True).encode("utf-8")).decode("ascii")
        return (
            f"{KeyManager._PAIR_BUNDLE_BEGIN}\n"
            f"{body}\n"
            f"{KeyManager._PAIR_BUNDLE_END}\n"
        ).encode("utf-8")

    @staticmethod
    def _deserialize_pair_bundle(bundle_bytes: bytes):
        text = bundle_bytes.decode("utf-8")
        start = text.find(KeyManager._PAIR_BUNDLE_BEGIN)
        end = text.find(KeyManager._PAIR_BUNDLE_END)
        if start == -1 or end == -1:
            raise ValueError("Neispravan format paketa ključeva.")
        body = text[start + len(KeyManager._PAIR_BUNDLE_BEGIN):end].strip()
        return json.loads(base64.b64decode(body).decode("utf-8"))

    def generate_key_pair(self, name: str, email: str, key_size: int,
                           password: str) -> Tuple[PublicKeyEntry, PrivateKeyEntry]:
        """
        Generiše novi RSA par ključeva (key_size: 1024 ili 2048 bita),
        čuva privatni ključ enkriptovan zadatom lozinkom, i dodaje
        odgovarajuće zapise u keyring.
        
        """
        if key_size not in (1024, 2048):
            raise ValueError("Veličina ključa mora biti 1024 ili 2048 bita.")

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        public_key = private_key.public_key()
        key_id = self._public_key_key_id(public_key)
        created_at = self._now()

        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        encrypted_private_key_pem = self._encrypt_private_key(private_key, password)

        public_entry = PublicKeyEntry(
            key_id=key_id,
            user_name=name,
            user_email=email,
            key_size=key_size,
            created_at=created_at,
            public_key_pem=public_key_pem,
        )
        private_entry = PrivateKeyEntry(
            key_id=key_id,
            user_name=name,
            user_email=email,
            key_size=key_size,
            created_at=created_at,
            public_key_pem=public_key_pem,
            encrypted_private_key_pem=encrypted_private_key_pem,
        )

        existing_public = self.keyring.find_public_key(key_id)
        existing_private = self.keyring.find_private_key(key_id)

        if existing_public is None:
            self.keyring.add_public_key(public_entry)
        else:
            public_entry = existing_public

        if existing_private is None:
            self.keyring.add_private_key(private_entry)
        else:
            private_entry = existing_private

        return public_entry, private_entry

    def delete_key_pair(self, key_id: str) -> None:
        """
        Briše par ključeva (javni i privatni) iz prstena ključeva.
        """
        self.keyring.remove_public_key(key_id)
        self.keyring.remove_private_key(key_id)

    def import_public_key(
        self,
        pem_path: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> PublicKeyEntry:
        """
        Uvozi javni ključ iz .pem fajla i dodaje ga u prsten javnih
        ključeva.

        """
        pem_bytes = Path(pem_path).read_bytes()
        public_key = serialization.load_pem_public_key(pem_bytes)
        key_id = self._public_key_key_id(public_key)
        created_at = self._now()
        key_size = getattr(public_key, "key_size", 0)

        entry = PublicKeyEntry(
            key_id=key_id,
            user_name=user_name or "Imported public key",
            user_email=user_email or "unknown",
            key_size=key_size,
            created_at=created_at,
            public_key_pem=pem_bytes,
        )
        self.keyring.add_public_key(entry)
        return entry

    def import_key_pair(
        self,
        pem_path: str,
        password: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> Tuple[PublicKeyEntry, PrivateKeyEntry]:
        """
        Uvozi ceo par ključeva (javni + privatni) iz .pem fajla.

        """
        bundle_bytes = Path(pem_path).read_bytes()
        payload = self._deserialize_pair_bundle(bundle_bytes)

        public_key_pem = base64.b64decode(payload["public_key_pem"])
        public_key = serialization.load_pem_public_key(public_key_pem)
        key_id = payload.get("key_id") or self._public_key_key_id(public_key)
        created_at = datetime.fromisoformat(payload["created_at"])
        key_size = int(payload["key_size"])
        bundle_user_name = payload.get("user_name", "")
        bundle_user_email = payload.get("user_email", "")
        final_user_name = user_name or bundle_user_name
        final_user_email = user_email or bundle_user_email

        private_blob = base64.b64decode(payload["private_key_blob"])
        decrypted_private_key = self._decrypt_private_key_blob(private_blob, password)
        if decrypted_private_key is None:
            raise ValueError("Lozinka nije ispravna ili privatni ključ nije moguće dešifrovati.")

        public_entry = PublicKeyEntry(
            key_id=key_id,
            user_name=final_user_name,
            user_email=final_user_email,
            key_size=key_size,
            created_at=created_at,
            public_key_pem=public_key_pem,
        )
        private_entry = PrivateKeyEntry(
            key_id=key_id,
            user_name=final_user_name,
            user_email=final_user_email,
            key_size=key_size,
            created_at=created_at,
            public_key_pem=public_key_pem,
            encrypted_private_key_pem=private_blob,
        )

        existing_public = self.keyring.find_public_key(key_id)
        existing_private = self.keyring.find_private_key(key_id)

        if existing_public is None:
            self.keyring.add_public_key(public_entry)
        else:
            public_entry = existing_public

        if existing_private is None:
            self.keyring.add_private_key(private_entry)
        else:
            private_entry = existing_private

        return public_entry, private_entry

    def export_public_key(self, key_id: str, destination_path: str) -> None:
        """
        Izvozi javni dio ključa u .pem format na zadatu destinaciju.

        """
        entry = self.keyring.find_public_key(key_id)
        if entry is None:
            raise KeyError(f"Javni ključ '{key_id}' nije pronađen.")
        if entry.public_key_pem is None:
            raise ValueError("Javni ključ nema serijalizovan PEM sadržaj.")
        Path(destination_path).write_bytes(entry.public_key_pem)

    def export_key_pair(self, key_id: str, password: str, destination_path: str) -> None:
        """
        Izvozi ceo par ključeva (javni + privatni) u .pem format.

        """
        public_entry = self.keyring.find_public_key(key_id)
        private_entry = self.keyring.find_private_key(key_id)
        if public_entry is None or private_entry is None:
            raise KeyError(f"Par ključeva '{key_id}' nije pronađen.")
        if not self.verify_password(key_id, password):
            raise ValueError("Lozinka za privatni ključ nije ispravna.")
        if public_entry.public_key_pem is None or private_entry.encrypted_private_key_pem is None:
            raise ValueError("Nedostaju podaci za izvoz para ključeva.")
        bundle = self._serialize_pair_bundle(public_entry, private_entry)
        Path(destination_path).write_bytes(bundle)

    def verify_password(self, key_id: str, password: str) -> bool:
        """
        Provera da li je uneta lozinka ispravna za dati privatni ključ.
        Koristi se svaki put kada je potreban pristup privatnom ključu
        (potpisivanje, dekripcija, izvoz privatnog ključa...).

        """
        entry = self.keyring.find_private_key(key_id)
        if entry is None or entry.encrypted_private_key_pem is None:
            return False
        try:
            return self._decrypt_private_key_blob(entry.encrypted_private_key_pem, password) is not None
        except ValueError:
            return False
