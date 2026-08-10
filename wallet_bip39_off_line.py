#!/usr/bin/env python3
"""
Offline BIP39 Bitcoin Wallet Report
PROGRAMA SOLO CON FINES EDUCATIVOS Y DE PRUEBA

Uso seguro recomendado:
- Ejecutar solo offline.
- Usar un entorno confiable.
- Proporcionar entropía correcta y verificable.
- Preferir una máquina limpia y no comprometida.

Entrada compatible:
- -w / --words
- --entropy-bin
- --entropy-hex
- --mnemonic
- --mnemonic-incomplete

Opciones:
- -p / --passphrase
- -i / --interactive
- --audit-passphrase
- --run-tests
- --vectors-file
- -n / --network
- -f / --format
- -o / --output
- --show-all

Dependencias:
    python3 -m pip install mnemonic bip-utils cryptography
"""

import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import pathlib
import sys
import tempfile
import unicodedata

from mnemonic import Mnemonic
from bip_utils import (
    Bip39SeedGenerator,
    Bip44,
    Bip44Coins,
    Bip44Changes,
    Bip49,
    Bip49Coins,
    Bip84,
    Bip84Coins,
    Bip86,
    Bip86Coins,
)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("⚠️  ADVERTENCIA: La librería 'cryptography' no está instalada.")
    print("    Instala con: pip3 install cryptography")
    print("    El script continuará pero NO podrá encriptar archivos.\n")

VALID_ENTROPY_BITS = {128, 160, 192, 224, 256}
VALID_WORD_COUNTS = {12, 15, 18, 21, 24}
DEFAULT_VECTORS_FILE = "vectors.json"
GAP_LIMIT = 5  # Reducido a 5 direcciones por ruta


def normalize_text(text):
    return unicodedata.normalize("NFKD", text)


def bytes_to_binary(data):
    return "".join(f"{byte:08b}" for byte in data)


def validate_entropy_length(bit_len):
    if bit_len not in VALID_ENTROPY_BITS:
        raise ValueError(
            "La entropía debe ser 128, 160, 192, 224 o 256 bits."
        )


def entropy_checksum_bits(entropy):
    checksum_len = (len(entropy) * 8) // 32
    digest_bits = bytes_to_binary(hashlib.sha256(entropy).digest())
    return digest_bits[:checksum_len]


def binary_to_bytes(binary_str):
    clean = binary_str.strip().replace(" ", "")
    if not clean:
        raise ValueError("La entropía binaria está vacía.")
    if any(ch not in "01" for ch in clean):
        raise ValueError("La entropía binaria solo puede contener 0 y 1.")
    validate_entropy_length(len(clean))
    return int(clean, 2).to_bytes(len(clean) // 8, "big")


def hex_to_bytes(hex_str):
    clean = hex_str.strip().replace(" ", "").lower()
    if not clean:
        raise ValueError("La entropía hexadecimal está vacía.")
    if clean.startswith("0x"):
        clean = clean[2:]
    if len(clean) % 2 != 0:
        raise ValueError("La entropía hexadecimal debe tener longitud par.")
    entropy = bytes.fromhex(clean)
    validate_entropy_length(len(entropy) * 8)
    return entropy


def generate_entropy(words):
    if words not in VALID_WORD_COUNTS:
        raise ValueError(
            "BIP39 solo admite 12, 15, 18, 21 o 24 palabras."
        )
    return os.urandom({12: 16, 15: 20, 18: 24, 21: 28, 24: 32}[words])


def entropy_to_mnemonic(entropy):
    return Mnemonic("english").to_mnemonic(entropy)


def validate_mnemonic_text(mnemonic):
    phrase = normalize_text(mnemonic).strip()
    words = phrase.split()

    if len(words) not in VALID_WORD_COUNTS:
        raise ValueError(
            "La mnemonic debe tener 12, 15, 18, 21 o 24 palabras."
        )

    mnemo = Mnemonic("english")
    if not mnemo.check(phrase):
        raise ValueError(
            "La mnemonic no es válida o su checksum no coincide."
        )

    return phrase


def mnemonic_to_entropy(mnemonic):
    phrase = validate_mnemonic_text(mnemonic)
    mnemo = Mnemonic("english")
    words = phrase.split()

    indexes = [mnemo.wordlist.index(word) for word in words]
    bits = "".join(f"{idx:011b}" for idx in indexes)

    entropy_bits = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}[len(words)]
    checksum_bits = entropy_bits // 32

    entropy_bin = bits[:entropy_bits]
    embedded_checksum = bits[entropy_bits:entropy_bits + checksum_bits]

    entropy = int(entropy_bin, 2).to_bytes(entropy_bits // 8, "big")
    expected_checksum = entropy_checksum_bits(entropy)

    return {
        "entropy": entropy,
        "entropy_bin": entropy_bin,
        "entropy_hex": entropy.hex(),
        "embedded_checksum": embedded_checksum,
        "expected_checksum": expected_checksum,
        "checksum_valid": embedded_checksum == expected_checksum,
    }


def mnemonic_seed(mnemonic, passphrase=""):
    """Genera la seed BIP39 usando PBKDF2-HMAC-SHA512."""
    return Bip39SeedGenerator(normalize_text(mnemonic)).Generate(
        normalize_text(passphrase)
    )


def bip32_master_key(seed):
    """
    Calcula la clave maestra BIP-32 desde la seed BIP39.
    Usa HMAC-SHA512 con Key="Bitcoin seed" y Data=seed.
    Retorna (master_key, chain_code) en formato hex.
    """
    # HMAC-SHA512(Key="Bitcoin seed", Data=seed)
    I = hmac.new(
        key=b"Bitcoin seed",
        msg=seed,
        digestmod=hashlib.sha512
    ).digest()
    
    # I[0:32] = master private key (32 bytes)
    # I[32:64] = master chain code (32 bytes)
    master_key_hex = I[:32].hex()
    chain_code_hex = I[32:].hex()
    
    return master_key_hex, chain_code_hex


def select_network(network):
    if network == "mainnet":
        return {
            "bip44": Bip44Coins.BITCOIN,
            "bip49": Bip49Coins.BITCOIN,
            "bip84": Bip84Coins.BITCOIN,
            "bip86": Bip86Coins.BITCOIN,
            "coin_type": "0'",
        }
    if network == "testnet":
        return {
            "bip44": Bip44Coins.BITCOIN_TESTNET,
            "bip49": Bip49Coins.BITCOIN_TESTNET,
            "bip84": Bip84Coins.BITCOIN_TESTNET,
            "bip86": Bip86Coins.BITCOIN_TESTNET,
            "coin_type": "1'",
        }
    raise ValueError("La red debe ser mainnet o testnet.")


def derive_addresses_bip44(seed, coin, coin_type, gap_limit=GAP_LIMIT):
    root = Bip44.FromSeed(seed, coin)
    account = root.Purpose().Coin().Account(0)
    change = account.Change(Bip44Changes.CHAIN_EXT)

    addresses = []
    for i in range(gap_limit):
        addr = change.AddressIndex(i)
        addresses.append({
            "index": i,
            "path": f"m/44'/{coin_type}/0'/0/{i}",
            "address": addr.PublicKey().ToAddress(),
            "private_key_wif": addr.PrivateKey().ToWif(),
            "public_key_hex": addr.PublicKey().RawCompressed().ToHex(),
        })

    xpub = account.PublicKey().ToExtended()
    return {
        "path_template": f"m/44'/{coin_type}/0'/0/i",
        "xpub": xpub,
        "addresses": addresses,
    }


def derive_addresses_bip49(seed, coin, coin_type, gap_limit=GAP_LIMIT):
    root = Bip49.FromSeed(seed, coin)
    account = root.Purpose().Coin().Account(0)
    change = account.Change(Bip44Changes.CHAIN_EXT)

    addresses = []
    for i in range(gap_limit):
        addr = change.AddressIndex(i)
        addresses.append({
            "index": i,
            "path": f"m/49'/{coin_type}/0'/0/{i}",
            "address": addr.PublicKey().ToAddress(),
            "private_key_wif": addr.PrivateKey().ToWif(),
            "public_key_hex": addr.PublicKey().RawCompressed().ToHex(),
        })

    ypub = account.PublicKey().ToExtended()
    return {
        "path_template": f"m/49'/{coin_type}/0'/0/i",
        "ypub": ypub,
        "addresses": addresses,
    }


def derive_addresses_bip84(seed, coin, coin_type, gap_limit=GAP_LIMIT):
    root = Bip84.FromSeed(seed, coin)
    account = root.Purpose().Coin().Account(0)
    change = account.Change(Bip44Changes.CHAIN_EXT)

    addresses = []
    for i in range(gap_limit):
        addr = change.AddressIndex(i)
        addresses.append({
            "index": i,
            "path": f"m/84'/{coin_type}/0'/0/{i}",
            "address": addr.PublicKey().ToAddress(),
            "private_key_wif": addr.PrivateKey().ToWif(),
            "public_key_hex": addr.PublicKey().RawCompressed().ToHex(),
        })

    zpub = account.PublicKey().ToExtended()
    return {
        "path_template": f"m/84'/{coin_type}/0'/0/i",
        "zpub": zpub,
        "addresses": addresses,
    }


def derive_addresses_bip86(seed, coin, coin_type, gap_limit=GAP_LIMIT):
    root = Bip86.FromSeed(seed, coin)
    account = root.Purpose().Coin().Account(0)
    change = account.Change(Bip44Changes.CHAIN_EXT)

    addresses = []
    for i in range(gap_limit):
        addr = change.AddressIndex(i)
        addresses.append({
            "index": i,
            "path": f"m/86'/{coin_type}/0'/0/{i}",
            "address": addr.PublicKey().ToAddress(),
            "private_key_wif": addr.PrivateKey().ToWif(),
            "public_key_hex": addr.PublicKey().RawCompressed().ToHex(),
        })

    return {
        "path_template": f"m/86'/{coin_type}/0'/0/i",
        "addresses": addresses,
    }


def write_secure_file(path, content, encrypt=True, password=None):
    """Escribe archivo de forma segura, SIEMPRE encriptado con AES-256-GCM."""
    destination = pathlib.Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    # SIEMPRE encriptar (comportamiento por defecto)
    if CRYPTO_AVAILABLE and password:
        # Encriptar con AES-256-GCM
        password_bytes = password.encode('utf-8')
        # Derivar clave de 32 bytes usando SHA-256
        key = hashlib.sha256(password_bytes).digest()
        
        # Generar nonce aleatorio de 12 bytes
        nonce = os.urandom(12)
        
        # Encriptar
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, content.encode('utf-8'), associated_data=None)
        
        # Combinar nonce + ciphertext y codificar en base64
        encrypted_content = base64.b64encode(nonce + ciphertext).decode('utf-8')
        content_to_write = f"ENCRYPTED:{encrypted_content}"
    else:
        # Si no hay crypto o password, escribir sin encriptar (fallback)
        content_to_write = content

    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + ".", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content_to_write)
            f.flush()
            os.fsync(f.fileno())

        try:
            os.chmod(tmp_name, 0o600)
        except OSError:
            pass

        os.replace(tmp_name, destination)

        try:
            os.chmod(destination, 0o600)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def decrypt_file_content(encrypted_content, password):
    """Desencripta contenido encriptado con AES-256-GCM."""
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("La librería 'cryptography' no está instalada.")
    
    if not encrypted_content.startswith("ENCRYPTED:"):
        raise ValueError("El archivo no está encriptado o tiene formato inválido.")
    
    # Decodificar base64
    encrypted_data = base64.b64decode(encrypted_content[10:])
    
    # Extraer nonce (12 bytes) y ciphertext
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    
    # Derivar clave
    password_bytes = password.encode('utf-8')
    key = hashlib.sha256(password_bytes).digest()
    
    # Desencriptar
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    
    return plaintext.decode('utf-8')


def generate_sequential_path(base_path):
    destination = pathlib.Path(base_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent

    counter = 1
    while True:
        new_name = f"{stem}_{counter:03d}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def audit_passphrase(passphrase):
    normalized = normalize_text(passphrase)
    utf8_bytes = normalized.encode("utf-8")

    characters = len(normalized)
    byte_length = len(utf8_bytes)
    unique_characters = len(set(normalized))

    has_lowercase = any(c.islower() for c in normalized)
    has_uppercase = any(c.isupper() for c in normalized)
    has_digits = any(c.isdigit() for c in normalized)
    has_symbols = any(not c.isalnum() and not c.isspace() for c in normalized)
    has_spaces = any(c.isspace() for c in normalized)

    if characters == 0:
        classification = "vacía"
        security_note = "No añade incertidumbre adicional."
    else:
        classification = "proporcionada por el usuario"
        security_note = (
            "No es posible calcular su entropía real sin conocer el proceso aleatorio utilizado para elegirla."
        )

    return {
        "present": characters > 0,
        "characters": characters,
        "utf8_bytes": byte_length,
        "unique_characters": unique_characters,
        "has_lowercase": has_lowercase,
        "has_uppercase": has_uppercase,
        "has_digits": has_digits,
        "has_symbols": has_symbols,
        "has_spaces": has_spaces,
        "classification": classification,
        "security_note": security_note,
    }


def attempt_clear_history():
    try:
        import readline
        readline.clear_history()
    except Exception:
        pass


def get_secure_input(prompt, allow_empty=False):
    """Obtiene input del usuario sin mostrarlo en pantalla (como password)."""
    while True:
        value = getpass.getpass(prompt)
        if value or allow_empty:
            return value
        print("⚠️  Este campo no puede estar vacío. Intenta nuevamente.")


def find_last_word(incomplete_phrase):
    """
    Encuentra TODAS las palabras posibles que completan una mnemonic incompleta.
    Retorna una lista de palabras válidas.
    """
    mnemo = Mnemonic("english")
    wordlist = mnemo.wordlist
    words = incomplete_phrase.strip().split()
    word_count = len(words)
    
    # Determinar longitud objetivo y tamaño de entropía
    if word_count == 11:
        target_count = 12
        entropy_bits = 128
    elif word_count == 23:
        target_count = 24
        entropy_bits = 256
    else:
        raise ValueError("Solo se pueden calcular mnemonics de 11→12 o 23→24 palabras.")
    
    checksum_bits = entropy_bits // 32
    valid_candidates = []
    
    print(f"Buscando palabras para completar mnemonic de {word_count} palabras...")
    print(f"Checksum de {checksum_bits} bits = {2**checksum_bits} posibilidades teóricas")
    
    for candidate_word in wordlist:
        test_phrase = incomplete_phrase + " " + candidate_word
        if mnemo.check(test_phrase):
            valid_candidates.append(candidate_word)
    
    return valid_candidates


def get_secure_mnemonic():
    """Obtiene mnemonic de forma segura (sin mostrar en pantalla)."""
    print("\n📝 Ingresa la mnemonic (las palabras se ocultarán mientras escribes):")
    print("   Escribe todas las palabras separadas por espacios.")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Mnemonic: ").strip()


def get_secure_entropy_hex():
    """Obtiene entropía hexadecimal de forma segura."""
    print("\n🔢 Ingresa la entropía hexadecimal (oculto):")
    print("   Debe ser 32, 40, 48, 56 o 64 caracteres hexadecimales.")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Entropy hex: ").strip()


def get_secure_entropy_bin():
    """Obtiene entropía binaria de forma segura."""
    print("\n🔢 Ingresa la entropía binaria (oculto):")
    print("   Debe ser 128, 160, 192, 224 o 256 bits (solo 0 y 1).")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Entropy bin: ").strip()


def get_secure_passphrase():
    """Obtiene passphrase de forma segura."""
    print("\n🔐 Ingresa la passphrase BIP39 (opcional, oculto):")
    print("   Presiona Enter para dejarla vacía si no quieres usar una.\n")
    return get_secure_input("Passphrase: ", allow_empty=True)


def resolve_input(args, interactive=False):
    """Resuelve la entrada de datos, soportando modo interactivo."""
    
    # Modo interactivo: solicitar datos que faltan
    if interactive:
        # Determinar qué entrada usar
        has_words = args.words is not None
        has_entropy_bin = bool(args.entropy_bin)
        has_entropy_hex = bool(args.entropy_hex)
        has_mnemonic = bool(args.mnemonic)
        has_mnemonic_incomplete = bool(args.mnemonic_incomplete)
        
        input_count = sum([has_words, has_entropy_bin, has_entropy_hex, has_mnemonic, has_mnemonic_incomplete])
        
        if input_count == 0:
            # Preguntar al usuario qué quiere hacer
            print("\nSelecciona el tipo de entrada:")
            print("  [1] Generar nueva mnemonic aleatoria")
            print("  [2] Ingresar entropía hexadecimal")
            print("  [3] Ingresar entropía binaria")
            print("  [4] Ingresar mnemonic existente")
            print("  [5] Calcular última palabra (11 o 23 palabras)")
            print()
            
            while True:
                choice = input("Opción [1-5]: ").strip()
                if choice == '1':
                    # Sub-menú para elegir longitud
                    print("\nSelecciona la longitud de la mnemonic:")
                    print("  [1] 12 palabras (128 bits - estándar, recomendado)")
                    print("  [2] 24 palabras (256 bits - máxima seguridad)")
                    print()
                    
                    while True:
                        length_choice = input("Opción [1-2]: ").strip()
                        if length_choice == '1':
                            args.words = 12
                            break
                        elif length_choice == '2':
                            args.words = 24
                            break
                        else:
                            print("❌ Opción inválida. Ingresa 1 o 2.")
                    break
                elif choice == '2':
                    args.entropy_hex = get_secure_entropy_hex()
                    break
                elif choice == '3':
                    args.entropy_bin = get_secure_entropy_bin()
                    break
                elif choice == '4':
                    args.mnemonic = get_secure_mnemonic()
                    break
                elif choice == '5':
                    args.mnemonic_incomplete = get_secure_mnemonic()
                    break
                else:
                    print("❌ Opción inválida. Ingresa un número entre 1 y 5.")
        
        # Preguntar por la red (mainnet/testnet)
        print("\nSelecciona la red Bitcoin:")
        print("  [1] Mainnet (Bitcoin principal - default)")
        print("  [2] Testnet (Bitcoin de pruebas)")
        print()
        
        while True:
            network_choice = input("Opción [1-2]: ").strip()
            if network_choice == '1':
                args.network = "mainnet"
                break
            elif network_choice == '2':
                args.network = "testnet"
                break
            else:
                print("❌ Opción inválida. Ingresa 1 o 2.")
        
        # Si no hay passphrase, solicitarla
        if not args.passphrase:
            args.passphrase = get_secure_passphrase()
    
    # Validar que haya exactamente una entrada
    if sum(1 for x in [args.words, args.entropy_bin, args.entropy_hex, args.mnemonic, args.mnemonic_incomplete] if x) != 1:
        raise ValueError(
            "Debes proporcionar exactamente una entrada entre -w/--words, --entropy-bin, --entropy-hex, --mnemonic o --mnemonic-incomplete."
        )

    if args.entropy_bin:
        entropy = binary_to_bytes(args.entropy_bin)
        mnemonic = entropy_to_mnemonic(entropy)
        recovered = {
            "entropy": entropy,
            "entropy_bin": bytes_to_binary(entropy),
            "entropy_hex": entropy.hex(),
            "checksum_valid": True,
        }
        return entropy, mnemonic, recovered, "entropy_bin"

    if args.entropy_hex:
        entropy = hex_to_bytes(args.entropy_hex)
        mnemonic = entropy_to_mnemonic(entropy)
        recovered = {
            "entropy": entropy,
            "entropy_bin": bytes_to_binary(entropy),
            "entropy_hex": entropy.hex(),
            "checksum_valid": True,
        }
        return entropy, mnemonic, recovered, "entropy_hex"

    if args.mnemonic:
        mnemonic = validate_mnemonic_text(args.mnemonic)
        recovered = mnemonic_to_entropy(mnemonic)
        return recovered["entropy"], mnemonic, recovered, "mnemonic"

    if args.mnemonic_incomplete:
        # Encontrar TODAS las palabras posibles
        incomplete_phrase = normalize_text(args.mnemonic_incomplete).strip()
        candidates = find_last_word(incomplete_phrase)
        
        if not candidates:
            raise ValueError("No se encontró ninguna palabra válida. Verifica que las palabras sean correctas.")
        
        print(f"\n✅ Se encontraron {len(candidates)} palabra(s) posible(s):\n")
        
        # Mostrar solo la lista numerada de palabras
        for i, word in enumerate(candidates, start=1):
            print(f"  [{i:2d}] {word}")
        
        print()
        
        if len(candidates) == 1:
            # Solo una opción, usarla directamente
            mnemonic = incomplete_phrase + " " + candidates[0]
            print("✅ Única palabra encontrada. Continuando...\n")
        else:
            # Múltiples opciones, solicitar selección al usuario
            print(f"⚠️  Hay {len(candidates)} palabras posibles.\n")
            print("INSTRUCCIONES:")
            print("1. Prueba cada palabra en tu wallet para encontrar la correcta")
            print("2. Ingresa el número de la palabra correcta (1 al {max_idx})".format(max_idx=len(candidates)))
            print("3. O ingresa 'q' para cancelar\n")
            
            while True:
                try:
                    user_input = input("Selecciona una palabra [1-{max_idx}]: ".format(max_idx=len(candidates))).strip()
                    
                    if user_input.lower() == 'q':
                        print("\n❌ Operación cancelada por el usuario.")
                        sys.exit(0)
                    
                    try:
                        selection = int(user_input)
                        if 1 <= selection <= len(candidates):
                            selected_word = candidates[selection - 1]
                            mnemonic = incomplete_phrase + " " + selected_word
                            print(f"\n✅ Palabra seleccionada: {selected_word}")
                            print("⚠️  ADVERTENCIA: Verifica que esta palabra genera las addresses correctas en tu wallet.\n")
                            break
                        else:
                            print(f"❌ Número inválido. Ingresa un número entre 1 y {len(candidates)}.")
                    except ValueError:
                        print("❌ Entrada inválida. Ingresa un número o 'q' para cancelar.")
                
                except EOFError:
                    # Manejar caso de input no interactivo (pipes, redirección)
                    print("\n⚠️  Modo no interactivo detectado. Usando la primera palabra.")
                    print("⚠️  DEBES verificar manualmente cuál es la palabra correcta.\n")
                    mnemonic = incomplete_phrase + " " + candidates[0]
                    break
        
        recovered = mnemonic_to_entropy(mnemonic)
        return recovered["entropy"], mnemonic, recovered, "mnemonic_incomplete"

    entropy = generate_entropy(args.words)
    mnemonic = entropy_to_mnemonic(entropy)
    recovered = {
        "entropy": entropy,
        "entropy_bin": bytes_to_binary(entropy),
        "entropy_hex": entropy.hex(),
        "checksum_valid": True,
    }
    return entropy, mnemonic, recovered, "words"


def build_context(args, interactive=False):
    entropy, mnemonic, recovered, input_mode = resolve_input(args, interactive)
    seed = mnemonic_seed(mnemonic, args.passphrase)
    
    # Calcular clave maestra BIP-32 correctamente con HMAC-SHA512
    bip32_master, bip32_chain_code = bip32_master_key(seed)
    bip32_root_key = bip32_master + bip32_chain_code  # 64 bytes (128 hex chars)
    
    network = select_network(args.network)

    derivations = {
        "BIP44": derive_addresses_bip44(seed, network["bip44"], network["coin_type"], GAP_LIMIT),
        "BIP49": derive_addresses_bip49(seed, network["bip49"], network["coin_type"], GAP_LIMIT),
        "BIP84": derive_addresses_bip84(seed, network["bip84"], network["coin_type"], GAP_LIMIT),
        "BIP86": derive_addresses_bip86(seed, network["bip86"], network["coin_type"], GAP_LIMIT),
    }

    context = {
        "coin_type_label": "Bitcoin",
        "network": args.network,
        "input_mode": input_mode,
        "entropy_bits": len(entropy) * 8,
        "entropy_bin": recovered["entropy_bin"],
        "entropy_hex": recovered["entropy_hex"],
        "entropy_checksum": entropy_checksum_bits(entropy),
        "checksum_valid": recovered["checksum_valid"],
        "mnemonic": mnemonic,
        "mnemonic_valid": True,
        "passphrase_used": bool(args.passphrase),
        "bip39_seed_hex": seed.hex(),
        "bip32_root_key": bip32_root_key,  # Clave maestra BIP-32 correcta (master + chain code)
        "bip32_master_key": bip32_master,  # Solo master key (32 bytes)
        "bip32_chain_code": bip32_chain_code,  # Solo chain code (32 bytes)
        "derivations": derivations,
        "gap_limit": GAP_LIMIT,
    }

    if args.audit_passphrase:
        context["passphrase_audit"] = audit_passphrase(args.passphrase)

    return context


def format_report(data, terminal_mode=True, hide_sensitive=True, show_all=False):
    """
    Genera el reporte.
    Por defecto, SIEMPRE oculta datos sensibles en terminal (hide_sensitive=True).
    Si show_all=True, muestra TODO (modo educativo).
    """
    # Si show_all=True, forzar hide_sensitive=False
    if show_all:
        hide_sensitive = False
    
    lines = [
        "\nOffline BIP39 Bitcoin Wallet Report",
        "PROGRAMA SOLO CON FINES EDUCATIVOS Y DE PRUEBA",
        "========================================",
        f"Coin type       : {data['coin_type_label']}",
        f"Input mode      : {data['input_mode']}",
        f"Network         : {data['network']}",
    ]
    
    if not hide_sensitive or not terminal_mode:
        # Mostrar datos sensibles solo si no se ocultan o es para archivo
        lines.extend([
            f"Entropy bits    : {data['entropy_bits']}",
            f"Entropy binary  : {data['entropy_bin']}",
            f"Entropy hex     : {data['entropy_hex']}",
            f"Checksum BIP39  : {data['entropy_checksum']}",
            f"Checksum valid  : {data['checksum_valid']}",
        ])
    else:
        # Ocultar datos sensibles en terminal (COMPORTAMIENTO POR DEFECTO)
        lines.extend([
            "Entropy bits    : [OCULTO - ver archivo desencriptado]",
            "Entropy binary  : [OCULTO - ver archivo desencriptado]",
            "Entropy hex     : [OCULTO - ver archivo desencriptado]",
            "Checksum BIP39  : [OCULTO - ver archivo desencriptado]",
            "Checksum valid  : [OCULTO - ver archivo desencriptado]",
        ])

    if "passphrase_audit" in data:
        pa = data["passphrase_audit"]
        lines.extend([
            "----------------------------------------",
            "AUDITORÍA DE PASSPHRASE",
            "----------------------------------------",
            f"Estado                 : {'presente' if pa['present'] else 'vacía'}",
            f"Caracteres             : {pa['characters']}",
            f"Bytes UTF-8            : {pa['utf8_bytes']}",
            f"Caracteres distintos   : {pa['unique_characters']}",
            f"Minúsculas             : {pa['has_lowercase']}",
            f"Mayúsculas             : {pa['has_uppercase']}",
            f"Dígitos                : {pa['has_digits']}",
            f"Símbolos               : {pa['has_symbols']}",
            f"Espacios               : {pa['has_spaces']}",
            f"Clasificación          : {pa['classification']}",
            f"Nota                   : {pa['security_note']}",
        ])

    lines.extend([
        "----------------------------------------",
        "Mnemonic",
        "----------------------------------------",
    ])
    
    if not hide_sensitive or not terminal_mode:
        lines.append(data["mnemonic"])
    else:
        word_count = len(data["mnemonic"].split())
        lines.append(f"[{word_count} palabras - OCULTO - ver archivo desencriptado]")
    
    lines.extend([
        f"\nMnemonic valid   : {data['mnemonic_valid']}",
        f"Passphrase used  : {data['passphrase_used']}",
    ])
    
    if not hide_sensitive or not terminal_mode:
        lines.extend([
            f"BIP39 seed hex   : {data['bip39_seed_hex']}",
            f"BIP32 root key   : {data['bip32_root_key']}",
        ])
    else:
        lines.extend([
            "BIP39 seed hex   : [OCULTO - ver archivo desencriptado]",
            "BIP32 root key   : [OCULTO - ver archivo desencriptado]",
        ])
    
    lines.append("----------------------------------------")

    gap = data.get("gap_limit", GAP_LIMIT)

    for name, item in data["derivations"].items():
        lines.extend([
            f"[{name}]",
            f"Path template    : {item['path_template']}",
            f"GAP limit       : {gap}",
        ])

        if "xpub" in item:
            lines.append(f"Extended public key : {item['xpub']}")
        if "ypub" in item:
            lines.append(f"Extended public key : {item['ypub']}")
        if "zpub" in item:
            lines.append(f"Extended public key : {item['zpub']}")

        if terminal_mode:
            first = item["addresses"][0]
            if not hide_sensitive or not terminal_mode:
                lines.extend([
                    f"Address (0)      : {first['address']}",
                    f"Private key WIF   : {first['private_key_wif']}",
                    f"Public key hex    : {first['public_key_hex']}",
                ])
            else:
                lines.append(f"Address (0)      : {first['address']}")
                lines.append("Private key WIF   : [OCULTO - ver archivo desencriptado]")
                lines.append("Public key hex    : [OCULTO - ver archivo desencriptado]")
        else:
            for addr_info in item["addresses"]:
                lines.extend([
                    f"Index            : {addr_info['index']}",
                    f"Path             : {addr_info['path']}",
                    f"Address          : {addr_info['address']}",
                    f"Private key WIF   : {addr_info['private_key_wif']}",
                    f"Public key hex    : {addr_info['public_key_hex']}",
                ])

        lines.append("----------------------------------------")

    lines.extend([
        "ADVERTENCIA, este script:",
        "no puede certificar que una entropía manual ingresada por el usuario sea imprevisible.",
        "no puede certificar que el entorno operativo donde se ejecuta el script no esté comprometido.",
        "no puede certificar que un usuario no haya copiado mal la passphrase o la mnemonic.",
        "\nel script es seguro solo si se ejecuta offline, sobre un entorno confiable, y con entropía correcta.",
        "el script intenta limpiar el historial del proceso Python actual.",
        "\n- Use el script con prudencia.",
    ])

    return "\n".join(lines)


def print_report(data, show_all=False):
    """Imprime reporte. Por defecto oculta datos sensibles, usa show_all=True para mostrar todo."""
    print(format_report(data, terminal_mode=True, hide_sensitive=not show_all, show_all=show_all))


def export_wallet(data, output_path, output_format, password):
    """Exporta wallet SIEMPRE encriptada con AES-256-GCM."""
    if output_format == "json":
        content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    else:
        content = format_report(data, terminal_mode=False, hide_sensitive=False) + "\n"

    final_path = generate_sequential_path(output_path)
    write_secure_file(final_path, content, encrypt=True, password=password)
    return final_path


def load_vectors(vectors_path):
    with open(vectors_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_bip39_test_vectors(vectors_path):
    """
    Ejecuta test vectors BIP39 oficiales.
    Formato: {"english": [[entropy_hex, mnemonic, seed], ...]}
    
    NOTA: Esta función NO usa encriptación para mantener compatibilidad con tests.
    """
    vectors = load_vectors(vectors_path)
    
    # Si es un diccionario con clave "english", extraer la lista
    if isinstance(vectors, dict):
        if "english" in vectors:
            vectors = vectors["english"]
        else:
            first_key = next(iter(vectors.keys()), None)
            if first_key and isinstance(vectors[first_key], list):
                vectors = vectors[first_key]
            else:
                raise ValueError("El archivo vectors.json no tiene el formato esperado.")
    
    for i, vector in enumerate(vectors, start=1):
        if isinstance(vector, list) and len(vector) == 3:
            entropy_hex, expected_mnemonic, expected_seed = vector
            entropy = bytes.fromhex(entropy_hex)
            
            mnemonic = entropy_to_mnemonic(entropy)
            if mnemonic != expected_mnemonic:
                raise AssertionError(f"Vector {i}: mnemonic no coincide.")

            seed = mnemonic_seed(mnemonic, "TREZOR").hex()
            if seed != expected_seed:
                raise AssertionError(f"Vector {i}: seed no coincide.")

            roundtrip = mnemonic_to_entropy(mnemonic)
            if roundtrip["entropy"].hex() != entropy_hex:
                raise AssertionError(f"Vector {i}: entropía no coincide en round-trip.")
        
        elif isinstance(vector, list) and len(vector) == 4:
            entropy_hex, expected_mnemonic, expected_seed, _ = vector
            entropy = bytes.fromhex(entropy_hex)
            
            mnemonic = entropy_to_mnemonic(entropy)
            if mnemonic != expected_mnemonic:
                raise AssertionError(f"Vector {i}: mnemonic no coincide.")

            seed = mnemonic_seed(mnemonic, "TREZOR").hex()
            if seed != expected_seed:
                raise AssertionError(f"Vector {i}: seed no coincide.")

            roundtrip = mnemonic_to_entropy(mnemonic)
            if roundtrip["entropy"].hex() != entropy_hex:
                raise AssertionError(f"Vector {i}: entropía no coincide en round-trip.")
        
        else:
            raise ValueError(f"Vector {i}: formato no soportado. Se espera [entropy_hex, mnemonic, seed].")

    print(f"Test vectors BIP39: OK ({len(vectors)} casos)")


def main():
    parser = argparse.ArgumentParser(description="Offline BIP39 Bitcoin Wallet Report")
    parser.add_argument("-w", "--words", type=int, choices=[12, 15, 18, 21, 24], default=None,
                        help="Genera una mnemonic nueva con el número de palabras indicado.")
    parser.add_argument("--entropy-bin", default="", help="Entropía binaria BIP39")
    parser.add_argument("--entropy-hex", default="", help="Entropía hexadecimal BIP39")
    parser.add_argument("--mnemonic", default="", help="Mnemonic BIP39 existente (completa)")
    parser.add_argument("--mnemonic-incomplete", default="", help="Mnemonic incompleta (11 o 23 palabras)")
    parser.add_argument("-p", "--passphrase", default="", help="Passphrase BIP39 opcional")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Modo interactivo: solicita datos de forma segura (sin historial)")
    parser.add_argument("--audit-passphrase", action="store_true",
                        help="Muestra una auditoría descriptiva de la passphrase.")
    parser.add_argument("--run-tests", action="store_true",
                        help="Ejecuta los test vectors BIP39 oficiales y termina.")
    parser.add_argument("--vectors-file", default=DEFAULT_VECTORS_FILE,
                        help="Archivo JSON de test vectors BIP39.")
    parser.add_argument("-n", "--network", choices=["mainnet", "testnet"], default="mainnet",
                        help="Red Bitcoin: mainnet (default) o testnet")
    parser.add_argument("-f", "--format", choices=["txt", "json"], default="json")
    parser.add_argument("-o", "--output", default="output/bip39_wallet_export.json")
    parser.add_argument("--show-all", action="store_true",
                        help="Muestra TODOS los datos en pantalla (modo educativo)")
    args = parser.parse_args()

    if args.run_tests:
        run_bip39_test_vectors(args.vectors_file)
        return

    # Verificar cryptografía
    if not CRYPTO_AVAILABLE:
        print("\n❌ ERROR: La librería 'cryptography' es requerida pero no está instalada.")
        print("    Instala con: pip3 install cryptography")
        print("    El script NO puede continuar sin encriptación.\n")
        sys.exit(1)

    # Solicitar contraseña SIEMPRE (comportamiento por defecto)
    print("\n🔐 SEGURIDAD ACTIVADA")
    print("   - El archivo de salida será encriptado con AES-256-GCM")
    if not args.show_all:
        print("   - Los datos sensibles se ocultarán en pantalla")
    print("   - Debes recordar esta contraseña para abrir el archivo\n")
    
    encrypt_password = get_secure_input("Contraseña para encriptar: ")
    confirm_password = get_secure_input("Confirmar contraseña: ")
    
    if encrypt_password != confirm_password:
        print("\n❌ Las contraseñas no coinciden. Saliendo.")
        sys.exit(1)
    
    if len(encrypt_password) < 8:
        print("\n⚠️  ADVERTENCIA: La contraseña es muy corta (< 8 caracteres).")
        print("    Se recomienda usar una contraseña más larga y segura.")
        confirm = input("    ¿Continuar de todos modos? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("\n❌ Operación cancelada.")
            sys.exit(1)
    print()

    # Modo interactivo o normal
    if args.interactive:
        print("\n🔒 MODO INTERACTIVO SEGURO")
        print("   Los datos ingresados no se mostrarán en pantalla.")
        print("   No quedarán en el historial del shell.\n")
        data = build_context(args, interactive=True)
    else:
        data = build_context(args, interactive=False)

    # Mostrar reporte (oculto por defecto, show_all para mostrar todo)
    print_report(data, show_all=args.show_all)

    attempt_clear_history()

    # Exportar archivo (SIEMPRE encriptado)
    final_path = export_wallet(data, args.output, args.format, password=encrypt_password)
    
    print()
    print(f"✅ Archivo encriptado guardado: {final_path}")
    print("   ⚠️  Recuerda la contraseña para desencriptar.")
    print("   ⚠️  Si pierdes la contraseña, perderás acceso a los datos.")
    print("\n📋 Para desencriptar el archivo:")
    print("   Usa un script separado con la función decrypt_file_content()")
    print("   O usa: python3 -c \"from wallet_bip39_off_line import decrypt_file_content; print(decrypt_file_content(open('" + str(final_path) + "').read(), 'TU_CONTRASEÑA'))\"")


if __name__ == "__main__":
    main()
