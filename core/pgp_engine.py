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
import time
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from Crypto.Cipher import AES
from Crypto.Cipher import DES3
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
import os
import zlib
import base64
from Crypto.Random import get_random_bytes
from hashlib import sha1
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

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
        #OSNOVNI IZGLED PORUKE
        timestamp=int(time.time())
        filename="test.txt" #PROMENI OVO
        data=message_text
        timestampBytes=timestamp.to_bytes(4, "big")
        filenameBytes=filename.encode("utf-8")
        filenameLenByte = len(filenameBytes).to_bytes(1, "big")
        dataBytes=data.encode("utf-8")
        message=filenameLenByte+filenameBytes+timestampBytes+dataBytes
        print(message)

        #AUTENTIKACIJA
        if options.sign==True:
          if not self.key_manager.verify_password(options.sign_private_key_id, sign_password):
            raise ValueError("Pogrešna lozinka za privatni ključ.")
          timestamp = int(time.time())
          signatureTimestampBytes=timestamp.to_bytes(4, "big")

          publicKeyID = bytes.fromhex(options.sign_private_key_id)
          print(publicKeyID)
          signedData=signatureTimestampBytes + message
          digest=sha1(signedData).digest()

          privateKey = self.key_manager.get_private_key(options.sign_private_key_id, sign_password)
          messageDigest=privateKey.sign(
            signedData,
            asym_padding.PKCS1v15(),
            hashes.SHA1(),
          )
          messageDigestLen = len(messageDigest).to_bytes(2, "big")
          twoOctets = digest[:2]
          signature=signatureTimestampBytes+publicKeyID+twoOctets+messageDigestLen+messageDigest
          message=signature+message
          print(message)

        #Kompresija
        if options.compress==True:
          compressedMessage=zlib.compress(message)
          print(compressedMessage)
          print("original:", len(message))
          print("compressed:", len(compressedMessage))
          message=compressedMessage
        #ovde dodaj opciju za dva simetricna algoritma i dodaj u poruku keyid i KS
        #Enkripcija
        if options.encrypt==True:#options.encrypt
          if options.symmetric_algorithm==SymmetricAlgorithm.AES128:
            kljucSesije = get_random_bytes(16)
            iv = get_random_bytes(AES.block_size)
            cipher = AES.new(kljucSesije, AES.MODE_CFB, iv=iv)
            message=iv+cipher.encrypt(message)

          if options.symmetric_algorithm==SymmetricAlgorithm.TRIPLE_DES:
            while True:
              try:
                kljucSesije = DES3.adjust_key_parity(get_random_bytes(24))
                break
              except ValueError:
                pass
            iv = get_random_bytes(DES3.block_size)
            cipher = DES3.new(kljucSesije, DES3.MODE_CFB, iv=iv)
            message=iv+cipher.encrypt(message)
            #Sifrovanje kljuca sesije
          publicKey = self.key_manager.keyring.find_public_key(options.encrypt_public_key_id)
          if publicKey is None:
            raise KeyError(f"Javni ključ primaoca '{options.encrypt_public_key_id}' nije pronađen.")

          javniKljucPrimaoca = RSA.import_key(publicKey.public_key_pem)
          rsa = PKCS1_OAEP.new(javniKljucPrimaoca)
          sifrovanKljucSesije = rsa.encrypt(kljucSesije)

          kljucPrimaocaID = bytes.fromhex(options.encrypt_public_key_id)
          duzinaKljuca=len(sifrovanKljucSesije).to_bytes(2, "big")
          message=kljucPrimaocaID+duzinaKljuca+sifrovanKljucSesije+message
          print(message)

        #Radix64 Konverzija
        algorithmdIDs = {
          SymmetricAlgorithm.AES128: 0,
          SymmetricAlgorithm.TRIPLE_DES: 1,
        }
        flags = 0
        if options.sign:     flags |= 0b00000001
        if options.compress: flags |= 0b00000010
        if options.encrypt:  flags |= 0b00000100
        if options.radix64:  flags |= 0b00001000
        if options.encrypt:
          flags |= (algorithmdIDs[options.symmetric_algorithm] << 4)
        flagsByte = flags.to_bytes(1, "big")
        # RADIX64 KONVERZIJA — na kraju, obuhvata CEO paket (flags + message)
        if options.radix64 == True:
          message = base64.b64encode(message)
        output = flagsByte+message



        with open(destination_path, "wb") as f:
          f.write(output)


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
        try:
          with open(source_path, "rb") as f:
            raw = f.read()
        except OSError as e:
          return ReceiveResult(success=False, error_message=f"Ne mogu da pročitam fajl: {e}")

        flags = raw[0]
        message = raw[1:]
        wasSigned = bool(flags & 0b00000001)
        wasCompressed = bool(flags & 0b00000010)
        wasEncrypted = bool(flags & 0b00000100)
        wasRadix = bool(flags & 0b00001000)
        alg_id = (flags >> 4) & 0b11
        algorithmIDs = {
          0: SymmetricAlgorithm.AES128,
          1: SymmetricAlgorithm.TRIPLE_DES
        }
        # RADIX64 DEKODIRANJE
        if wasRadix:
          try:
            message = base64.b64decode(message)
          except Exception:
            return ReceiveResult(success=False, error_message="Neispravan radix-64 sadržaj.")
            # DEKRIPCIJA
        if wasEncrypted:
            if len(message) < 10:
              return ReceiveResult(success=False, error_message="Fajl je oštećen (paket sesijskog ključa).")

            javniKljucID = message[:8]
            duzina = int.from_bytes(message[8:10], "big")
            sifrovanKljucSesije = message[10:10 + duzina]
            rest = message[10 + duzina:]

            if decrypt_password is None:
              return ReceiveResult(success=False, error_message="Potrebna je lozinka za dekripciju.")

            recipientKeyIDHex = javniKljucID.hex()
            if not self.key_manager.verify_password(recipientKeyIDHex, decrypt_password):
                return ReceiveResult(success=False, error_message="Pogrešna lozinka ili ključ nije pronađen.")

            try:
              privatanKljuc = self.key_manager.get_private_key(recipientKeyIDHex, decrypt_password)
              kljucSesije = privatanKljuc.decrypt(
                sifrovanKljucSesije,
                asym_padding.OAEP(
                  mgf=asym_padding.MGF1(algorithm=hashes.SHA1()),
                  algorithm=hashes.SHA1(),
                  label=None,
                ),
              )
            except Exception:
              return ReceiveResult(success=False, error_message="Dekripcija sesijskog ključa nije uspela.")

            symmetric_algorithm = algorithmIDs.get(alg_id)
            try:
              if symmetric_algorithm == SymmetricAlgorithm.AES128:
                iv, ciphertext = rest[:AES.block_size], rest[AES.block_size:]
                cipher = AES.new(kljucSesije, AES.MODE_CFB, iv=iv)
                message = cipher.decrypt(ciphertext)
              elif symmetric_algorithm == SymmetricAlgorithm.TRIPLE_DES:
                iv, ciphertext = rest[:DES3.block_size], rest[DES3.block_size:]
                cipher = DES3.new(kljucSesije, DES3.MODE_CFB, iv=iv)
                message = cipher.decrypt(ciphertext)
              else:
                return ReceiveResult(success=False, error_message=f"Algoritam nije implementiran (id={alg_id}).")
            except Exception:
              return ReceiveResult(success=False, error_message="Dekripcija sadržaja nije uspela.")

        # DEKOMPRESIJA
        if wasCompressed:
          try:
              message = zlib.decompress(message)
          except zlib.error:
              return ReceiveResult(success=False, error_message="Greška pri dekompresiji, podaci su oštećeni.")

        #VERIFIKACIJA POTPISA
        signature_valid = None
        signer_name = None
        signer_email = None

        if wasSigned:
            if len(message) < 4 + 8 + 2 + 2:
                return ReceiveResult(success=False, error_message="Fajl je oštećen (paket potpisa).")

            signatureTimestampBytes = message[0:4]
            publicKeyID = message[4:12]
            twoOctets = message[12:14]
            messageDigestLen = int.from_bytes(message[14:16], "big")
            messageDigest = message[16:16 + messageDigestLen]
            message = message[16 + messageDigestLen:]

            signedData = signatureTimestampBytes + message
            digest = sha1(signedData).digest()

            if digest[:2] != twoOctets:
                  # brzi test nije prošao - poruka je oštećena ili neko drugi je "potpisao"
                  signature_valid = False
            else:
                signerKeyIDHex = publicKeyID.hex()

                public_entry = self.key_manager.keyring.find_public_key(signerKeyIDHex)

                if public_entry is None:
                    signature_valid = False
                else:
                    signerPublicKey = serialization.load_pem_public_key(public_entry.public_key_pem)
                    try:
                      signerPublicKey.verify(
                        messageDigest, signedData,
                        asym_padding.PKCS1v15(), hashes.SHA1(),
                      )
                      signature_valid = True
                      signer_name = public_entry.user_name
                      signer_email = public_entry.user_email
                    except InvalidSignature:
                      signature_valid = False



     # LITERAL PACKET (ime fajla, timestamp, sadržaj)
        if len(message) < 1:
            return ReceiveResult(success=False, error_message="Fajl je oštećen (nedostaje sadržaj poruke).")

        filenameLen = message[0]
        if len(message) < 1 + filenameLen + 4:
            return ReceiveResult(success=False, error_message="Fajl je oštećen (nedostaje sadržaj poruke).")

        dataBytes = message[1 + filenameLen + 4:]

        return ReceiveResult(
            success=True,
            was_signed=wasSigned,
            signature_valid=signature_valid,
            signer_name=signer_name,
            signer_email=signer_email,
            was_encrypted=wasEncrypted,
            was_compressed=wasCompressed,
            was_radix64=wasRadix,
            plaintext=dataBytes,
        )
