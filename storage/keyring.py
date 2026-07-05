"""
storage/keyring.py

Backend strukture za javni i privatni prsten ključeva.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class PublicKeyEntry:
    key_id: str
    user_name: str
    user_email: str
    key_size: int
    created_at: datetime
    public_key_pem: bytes

    # Izračunato svojstvo za PGP-style korisnički identifikator.
    @property
    def user_id(self) -> str:
        if self.user_name:
            return f"{self.user_name} <{self.user_email}>"
        return self.user_email

@dataclass
class PrivateKeyEntry:
    key_id: str                     # najnižih 64 bita javnog ključa
    user_name: str
    user_email: str
    key_size: int
    created_at: datetime
    public_key_pem: bytes
    encrypted_private_key_pem: bytes
    encryption_algorithm: str = "CAST-128"

    @property
    def user_id(self) -> str:
        if self.user_name:
            return f"{self.user_name} <{self.user_email}>"
        return self.user_email


class KeyRing:
    def __init__(self):
        self.public_keys: List[PublicKeyEntry] = []
        self.private_keys: List[PrivateKeyEntry] = []
        self._public_by_key_id: Dict[str, PublicKeyEntry] = {}
        self._private_by_key_id: Dict[str, PrivateKeyEntry] = {}
        self._private_by_email: Dict[str, List[PrivateKeyEntry]] = {}

    def _rebuild_public_index(self) -> None:
        self._public_by_key_id = {entry.key_id: entry for entry in self.public_keys}

    def _rebuild_private_indexes(self) -> None:
        self._private_by_key_id = {}
        self._private_by_email = {}
        for entry in self.private_keys:
            self._private_by_key_id[entry.key_id] = entry
            self._private_by_email.setdefault(entry.user_email.lower(), []).append(entry)

    def add_public_key(self, entry: PublicKeyEntry) -> None:
        if entry.key_id in self._public_by_key_id:
            raise ValueError(f"Javni ključ sa key_id='{entry.key_id}' već postoji.")
        self.public_keys.append(entry)
        self._public_by_key_id[entry.key_id] = entry

    def add_private_key(self, entry: PrivateKeyEntry) -> None:
        if entry.key_id in self._private_by_key_id:
            raise ValueError(f"Privatni ključ sa key_id='{entry.key_id}' već postoji.")
        self.private_keys.append(entry)
        self._private_by_key_id[entry.key_id] = entry
        self._private_by_email.setdefault(entry.user_email.lower(), []).append(entry)

    def add_key_pair(self, public_entry: PublicKeyEntry, private_entry: PrivateKeyEntry) -> None:
        if public_entry.key_id != private_entry.key_id:
            raise ValueError("Public i private entry moraju imati isti key_id.")
        self.add_public_key(public_entry)
        self.add_private_key(private_entry)

    def remove_public_key(self, key_id: str) -> bool:
        if key_id not in self._public_by_key_id:
            return False
        self.public_keys = [k for k in self.public_keys if k.key_id != key_id]
        self._rebuild_public_index()
        return True

    def remove_private_key(self, key_id: str) -> bool:
        if key_id not in self._private_by_key_id:
            return False
        self.private_keys = [k for k in self.private_keys if k.key_id != key_id]
        self._rebuild_private_indexes()
        return True

    def remove_key_pair(self, key_id: str) -> bool:
        removed_public = self.remove_public_key(key_id)
        removed_private = self.remove_private_key(key_id)
        return removed_public or removed_private

    def find_public_key(self, key_id: str) -> Optional[PublicKeyEntry]:
        return self._public_by_key_id.get(key_id)

    def find_private_key(self, key_id: str) -> Optional[PrivateKeyEntry]:
        return self._private_by_key_id.get(key_id)

    def find_private_keys_by_email(self, user_email: str) -> List[PrivateKeyEntry]:
        return list(self._private_by_email.get(user_email.lower(), []))

    def find_public_keys_by_email(self, user_email: str) -> List[PublicKeyEntry]:
        email = user_email.lower()
        return [entry for entry in self.public_keys if entry.user_email.lower() == email]

    def has_public_key(self, key_id: str) -> bool:
        return key_id in self._public_by_key_id

    def has_private_key(self, key_id: str) -> bool:
        return key_id in self._private_by_key_id

    def list_public_keys(self) -> List[PublicKeyEntry]:
        return list(self.public_keys)

    def list_private_keys(self) -> List[PrivateKeyEntry]:
        return list(self.private_keys)

    def clear(self) -> None:
        self.public_keys.clear()
        self.private_keys.clear()
        self._public_by_key_id.clear()
        self._private_by_key_id.clear()
        self._private_by_email.clear()

    def __len__(self) -> int:
        return len(self.private_keys)

    def __repr__(self) -> str:
        return f"KeyRing(public_keys={len(self.public_keys)}, private_keys={len(self.private_keys)})"
