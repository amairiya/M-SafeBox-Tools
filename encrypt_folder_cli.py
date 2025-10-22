#!/usr/bin/env python3
"""
encrypt_folder_cli.py

Outil CLI Windows/Linux pour chiffrer/déchiffrer un dossier.
Version corrigée : saisie interactive, validation des chemins,
confirmation avant écrasement, compression optionnelle et messages colorés.
"""

import os
import sys
import tempfile
import zipfile
from getpass import getpass
import time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64
from colorama import init, Fore, Style

init(autoreset=True)

SALT_SIZE = 16
KDF_ITERATIONS = 390000

# -------------------- Fonctions principales --------------------

def derive_key(password: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    key = kdf.derive(password)
    return base64.urlsafe_b64encode(key)

def make_zip_of_folder(folder_path: str, out_zip_path: str) -> None:
    with zipfile.ZipFile(out_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, start=folder_path)
                zf.write(abs_path, arcname=rel_path)

def encrypt_folder(folder: str, out_file: str, password: str, compress: bool = True) -> None:
    if not os.path.isdir(folder):
        print(Fore.RED + f"❌ Erreur : dossier source introuvable : {folder}")
        sys.exit(1)

    password_bytes = password.encode("utf-8")

    # Toujours utiliser un fichier temporaire
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_zip = tmp.name

    try:
        if compress:
            print("📦 Archiving folder...")
            make_zip_of_folder(folder, tmp_zip)
        else:
            print("📦 Lecture du contenu des fichiers sans compression...")
            with open(tmp_zip, "wb") as f_out:
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        file_path = os.path.join(root, f)
                        with open(file_path, "rb") as f_in:
                            f_out.write(f_in.read())

        salt = os.urandom(SALT_SIZE)
        key = derive_key(password_bytes, salt)
        fernet = Fernet(key)

        with open(tmp_zip, "rb") as f_in:
            plaintext = f_in.read()

        print("🔒 Encrypting...")
        ciphertext = fernet.encrypt(plaintext)

        if os.path.exists(out_file):
            confirm = input(Fore.YELLOW + f"⚠ Le fichier {out_file} existe déjà. Écraser ? (y/n) : ").strip().lower()
            if confirm != 'y':
                print("❌ Abandon du chiffrement.")
                sys.exit(0)

        with open(out_file, "wb") as f_out:
            f_out.write(salt + ciphertext)

        print(Fore.GREEN + f"✅ Chiffrement terminé : {out_file}")

    finally:
        try:
            os.remove(tmp_zip)
        except Exception:
            pass

def decrypt_file(in_file: str, out_folder: str, password: str) -> None:
    if not os.path.isfile(in_file):
        print(Fore.RED + f"❌ Erreur : fichier introuvable : {in_file}")
        sys.exit(1)

    password_bytes = password.encode("utf-8")

    with open(in_file, "rb") as f_in:
        data = f_in.read()

    if len(data) < SALT_SIZE:
        print(Fore.RED + "❌ Erreur : fichier trop court ou invalide")
        sys.exit(1)

    salt = data[:SALT_SIZE]
    ciphertext = data[SALT_SIZE:]

    key = derive_key(password_bytes, salt)
    fernet = Fernet(key)

    try:
        print("🔓 Decrypting...")
        plaintext = fernet.decrypt(ciphertext)
    except Exception as e:
        print(Fore.RED + f"❌ Erreur de déchiffrement : {e}")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_zip = tmp.name
    try:
        with open(tmp_zip, "wb") as zf:
            zf.write(plaintext)

        os.makedirs(out_folder, exist_ok=True)
        print("📂 Extracting archive...")
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(out_folder)

        print(Fore.GREEN + f"✅ Déchiffrement terminé dans : {out_folder}")
    finally:
        try:
            os.remove(tmp_zip)
        except Exception:
            pass

# -------------------- Affichage bannière --------------------

def show_banner():
    RED = Fore.RED
    CYAN = Fore.CYAN
    END = Style.RESET_ALL

    banner = f"""{RED}
    __  __        _____        __     ____            
    |  \/  |      / ____|      / _|   |  _ \           
    | \  / |_____| (___   __ _| |_ ___| |_) | _____  __
    | |\/| |______\___ \ / _` |  _/ _ \  _ < / _ \ \/ / 
    | |  | |      ____) | (_| | ||  __/ |_) | (_) >  <  
    |_|  |_|     |_____/ \__,_|_| \___|____/ \___/_/\_\ 
    {END}
    ─────────────────────────────────────────────
    Email   : contact.mamairi@gmail.com
    GitHub  : github.com/amairiya
    ─────────────────────────────────────────────
    """
    print(banner)

# -------------------- Fonction principale --------------------

def main():
    show_banner()

    action = input("Tapez 'encrypt (e)' ou 'decrypt (d)' : ").strip().lower()
    if action == 'e':
        action = 'encrypt'
    elif action == 'd':
        action = 'decrypt'
    elif action not in ['encrypt', 'decrypt']:
        print(Fore.RED + "❌ Action invalide. Fin du programme.")
        sys.exit(1)

    source_folder = input("Entrez le chemin du dossier source (ou fichier pour déchiffrement) : ").strip()
    destination = input("Entrez le chemin du dossier de destination (ou fichier pour chiffrement) : ").strip()
    password = getpass("Entrez la phrase de passe : ")

    if action == 'encrypt' and not destination.endswith('.bin'):
        destination += '.bin'

    compress = True
    if action == 'encrypt':
        compress = input("Voulez-vous compresser le dossier avant chiffrement ? (y/n) : ").strip().lower() == 'y'

    if action == 'encrypt':
        encrypt_folder(source_folder, destination, password, compress)
    else:
        decrypt_file(source_folder, destination, password)

# -------------------- Lancement --------------------
if __name__ == "__main__":
    main()
