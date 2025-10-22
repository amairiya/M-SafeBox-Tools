# M-SafeBox

**M-SafeBox** is a lightweight CLI tool for encrypting and decrypting folders on Windows (and compatible with Linux/macOS with Python). It provides interactive folder selection, password-based encryption, optional compression, and color-coded terminal messages.

---

## Demo

[![Démo M-SafeBox](https://youtu.be/o5Bz-F_aDnA/0.jpg)](https://youtu.be/o5Bz-F_aDnA)

---


## Features

- Encrypt entire folders into a single secure file.
- Decrypt encrypted files back to their original folder structure.
- Optional compression using ZIP before encryption.
- Interactive CLI with validation of source and destination paths.
- Colorful terminal output for better readability.
- Confirmation prompts before overwriting files.
- Password-based key derivation using PBKDF2-HMAC-SHA256.
- AES encryption via Fernet (symmetric encryption).

---



## Installation

1. **Clone the repository:**

```bash
git clone https://github.com/amairiya/M-SafeBox-Tools.git
cd M-SafeBox-Tools
```


