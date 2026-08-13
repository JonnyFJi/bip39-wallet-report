# Offline BIP39 Bitcoin Wallet Report

**PROGRAMA SOLO CON FINES EDUCATIVOS Y DE PRUEBA.**
**NO SE RECOMIENDA USAR CON FONDOS REALES.**
**No es sustituto para una Hot Wallet o una Hardware wallet.**

## Descripción del script

Este script es una herramienta offline para generar y verificar wallets de Bitcoin usando el estándar BIP39. Permite crear mnemonics seguras, calcular la clave maestra BIP-32 correcta, derivar addresses en múltiples rutas de derivación (BIP44, BIP49, BIP84, BIP86), y realizar análisis de seguridad de mnemonics.

## Función del script

El script realiza las siguientes funciones principales:

1. **Generación de entropía**: Usa `os.urandom()` para generar entropía criptográficamente segura
2. **Generación sin repeticiones**: Reintenta automáticamente hasta obtener mnemonics con todas las palabras únicas
3. **Conversión a mnemonic**: Transforma la entropía en frases mnemotécnicas de 12, 15, 18, 21 o 24 palabras
4. **Cálculo de clave maestra BIP-32**: Usa HMAC-SHA512 con Key="Bitcoin seed" para derivar la clave maestra correctamente
5. **Derivación de seed**: Genera la seed BIP39 usando PBKDF2 con HMAC-SHA512
6. **Derivación de addresses**: Genera 5 addresses por cada ruta de derivación (GAP limit)
7. **Análisis de seguridad**: Realiza 6 tests para detectar patrones de baja entropía y posible manipulación manual
8. **Verificación**: Valida checksums, mnemonics y round-trips
9. **Exportación segura**: Escribe archivos encriptados con AES-256-GCM y permisos restringidos (0o600)
10. **Verificación de wordlist**: Valida la wordlist embebida contra la lista oficial BIP39 de GitHub

## Características de seguridad

- ✅ **Encriptación AES-256-GCM**: Todos los archivos de salida están encriptados
- ✅ **Ocultamiento de datos**: Los datos sensibles se ocultan en terminal por defecto
- ✅ **Input seguro**: Usa `getpass` para evitar que las contraseñas queden en el historial
- ✅ **Permisos restringidos**: Archivos con permisos 0o600 (solo propietario)
- ✅ **Escritura atómica**: Usa `tempfile` + `os.replace()` para evitar corrupción
- ✅ **Limpieza de historial**: Intenta limpiar `readline.clear_history()`
- ✅ **Bitcoin-only**: Reduce superficie de ataque
- ✅ **Análisis de seguridad**: 6 tests para detectar mnemonics débiles o manipuladas
- ✅ **Verificación BIP39**: Wordlist validada contra lista oficial de GitHub

## Test vectors

✅ **Pasaron los 24 casos oficiales de Trezor**  
✅ **Compatible con BIP39 estándar**  
✅ **Clave maestra BIP-32 calculada correctamente con HMAC-SHA512**  
✅ **Wordlist oficial verificada (2048 palabras)**

El script ha sido verificado con los test vectors oficiales de Trezor, lo que confirma que la implementación es correcta y compatible con el estándar BIP39.

## Análisis de seguridad de mnemonics

El script incluye un sistema de análisis de seguridad con 6 tests:

1. **Test de unicidad**: Verifica que todas las palabras sean únicas
2. **Test de entropía de Shannon**: Mide la distribución de frecuencias de palabras
3. **Test de patrones secuenciales**: Detecta palabras consecutivas en la wordlist
4. **Test de distribución de índices**: Verifica distribución uniforme en la wordlist
5. **Test de palabras repetidas**: Detecta repeticiones consecutivas y no consecutivas
6. **Test de manipulación manual**: Identifica patrones sospechosos de intervención humana

### Score y clasificación

- **100-80**: ✅ FUERTE - Entropía adecuada
- **79-60**: ⚠️ MODERADA - Posibles patrones menores
- **59-40**: ⚠️ DÉBIL - Patrones detectados
- **<40**: ❌ MUY DÉBIL - Alta probabilidad de baja entropía

## Tipos de dirección soportados

| Estándar | Ruta de derivación | Tipo de address | Descripción |
|----------|-------------------|-----------------|-------------|
| **BIP44** | m/44'/0'/0'/0/i | P2PKH | Legacy (direcciones que empiezan con 1) |
| **BIP49** | m/49'/0'/0'/0/i | P2WPKH-P2SH | Nested SegWit (direcciones que empiezan con 3) |
| **BIP84** | m/84'/0'/0'/0/i | P2WPKH | Native SegWit (direcciones que empiezan con bc1q) |
| **BIP86** | m/86'/0'/0'/0/i | P2TR | Taproot (direcciones que empiezan con bc1p) |

## Dependencias

```bash
python3 -m pip install mnemonic bip-utils cryptography
```

## Instalación

### 1. Verificar Python 3

```bash
python3 --version
```

Deberías tener Python 3.8 o superior.

### 2. Instalar librerías requeridas

```bash
python3 -m pip install mnemonic bip-utils cryptography
```

### 3. Verificar instalación

```bash
python3 -c "from mnemonic import Mnemonic; from bip_utils import Bip44; from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print('✅ Todas las dependencias instaladas')"
```

### 4. Descargar test vectors oficiales (opcional)

```bash
curl -o vectors.json https://raw.githubusercontent.com/trezor/python-mnemonic/refs/heads/master/vectors.json
```

O usa wget:

```bash
wget -O vectors.json https://raw.githubusercontent.com/trezor/python-mnemonic/refs/heads/master/vectors.json
```

## Uso del script

### Comandos y banderas

```bash
python3 wallet_bip39_off_line.py [OPCIONES]
```

#### Opciones de entrada (usar exactamente una):

- `-w, --words {12,15,18,21,24}`: Genera una mnemonic nueva con el número de palabras indicado
- `--entropy-bin`: Entropía binaria BIP39 (128, 160, 192, 224 o 256 bits)
- `--entropy-hex`: Entropía hexadecimal BIP39 (32, 40, 48, 56 o 64 caracteres hex)
- `--mnemonic`: Mnemonic BIP39 existente (completa, 12-24 palabras)
- `--mnemonic-incomplete`: Mnemonic incompleta (11 o 23 palabras) para calcular la última

#### Opciones generales:

- `-p, --passphrase`: Passphrase BIP39 opcional
- `-i, --interactive`: Modo interactivo (solicita datos de forma segura, sin historial)
- `-n, --network {mainnet,testnet}`: Red Bitcoin (default: mainnet)
- `-f, --format {txt,json}`: Formato de salida (default: json)
- `-o, --output`: Ruta del archivo de salida (default: output/bip39_wallet_export.json)
- `--show-all`: Muestra TODOS los datos en pantalla (modo educativo)
- `--audit-passphrase`: Muestra auditoría descriptiva de la passphrase
- `--run-tests`: Ejecuta los test vectors BIP39 oficiales
- `--vectors-file`: Archivo JSON de test vectors BIP39 (default: vectors.json)

### Ejemplos de uso

#### 1. Generar wallet nueva (12 palabras, mainnet)

```bash
python3 wallet_bip39_off_line.py -w 12
```

**Flujo:**
1. Pide contraseña para encriptar
2. Genera 12 palabras aleatorias (reintenta si hay repeticiones)
3. Realiza análisis de seguridad de la mnemonic
4. Usa red mainnet (default)
5. Oculta datos sensibles en terminal
6. Guarda archivo encriptado en `output/bip39_wallet_export.json`

#### 2. Generar wallet nueva (24 palabras, testnet)

```bash
python3 wallet_bip39_off_line.py -w 24 -n testnet
```

**Flujo:**
1. Pide contraseña para encriptar
2. Genera 24 palabras aleatorias (reintenta si hay repeticiones)
3. Realiza análisis de seguridad
4. Usa red testnet
5. Oculta datos sensibles en terminal
6. Guarda archivo encriptado

#### 3. Modo interactivo (menú guiado)

```bash
python3 wallet_bip39_off_line.py -i
```

**Flujo:**
1. Pide contraseña
2. Muestra menú interactivo:
   - Seleccionar tipo de entrada (1-5)
   - Seleccionar longitud (12 o 24 palabras)
   - Seleccionar red (mainnet o testnet)
   - Ingresar passphrase (opcional)
3. Genera wallet
4. Realiza análisis de seguridad
5. Guarda archivo encriptado

#### 4. Modo educativo (muestra todo en pantalla)

```bash
python3 wallet_bip39_off_line.py -w 12 --show-all
```

**Flujo:**
1. Pide contraseña
2. Genera 12 palabras
3. **Muestra TODOS los datos en pantalla** (entropy, mnemonic, seed, keys, addresses)
4. Muestra análisis de seguridad completo con score y clasificación
5. Guarda archivo encriptado

⚠️ **ADVERTENCIA**: No usar `--show-all` en producción. Solo para fines educativos.

#### 5. Verificar mnemonic existente

```bash
python3 wallet_bip39_off_line.py --mnemonic "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about" -p "TREZOR"
```

**Flujo:**
1. Pide contraseña
2. Verifica checksum BIP39
3. Realiza análisis de seguridad (6 tests)
4. Calcula seed y derivaciones
5. Guarda archivo encriptado

#### 6. Calcular última palabra (recuperación)

```bash
python3 wallet_bip39_off_line.py --mnemonic-incomplete "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon"
```

**Flujo:**
1. Busca todas las palabras posibles (16 opciones para 11 palabras)
2. Muestra lista numerada
3. Pide al usuario seleccionar la correcta
4. Verifica que la palabra genera addresses correctas
5. Genera wallet completa
6. Realiza análisis de seguridad

#### 7. Usar entropía hexadecimal

```bash
python3 wallet_bip39_off_line.py --entropy-hex 00000000000000000000000000000000
```

**Requisitos:**
- 32, 40, 48, 56 o 64 caracteres hexadecimales
- Formato: solo 0-9, a-f (sin espacios)

#### 8. Usar entropía binaria

```bash
python3 wallet_bip39_off_line.py --entropy-bin 00000000000000000000000000000000
```

**Requisitos:**
- 128, 160, 192, 224 o 256 bits
- Formato: solo 0 y 1 (sin espacios)

#### 9. Ejecutar test vectors oficiales

```bash
python3 wallet_bip39_off_line.py --run-tests --vectors-file vectors.json
```

**Resultado esperado:**
Test vectors BIP39: OK (24 casos)


#### 10. Auditoría de passphrase

```bash
python3 wallet_bip39_off_line.py -w 12 -p "mi_passphrase" --audit-passphrase
```

**Muestra:**
- Número de caracteres
- Bytes UTF-8
- Caracteres distintos
- Presencia de mayúsculas, minúsculas, dígitos, símbolos, espacios
- Clasificación de seguridad

## Flujo de trabajo recomendado

### Para generación de wallet nueva:

```bash
# 1. Generar wallet (modo seguro)
python3 wallet_bip39_off_line.py -w 12 -i

# 2. Verificar análisis de seguridad (score > 80 recomendado)

# 3. Verificar mnemonic en wallet (Electrum, BlueWallet, etc.)

# 4. Guardar mnemonic en papel o metal (NUNCA en digital)

# 5. Borrar archivo encriptado si no es necesario
rm output/bip39_wallet_export.json
```

### Para recuperación de wallet:

```bash
# 1. Calcular última palabra (si falta)
python3 wallet_bip39_off_line.py --mnemonic-incomplete "word1 word2 ... word23" -i

# 2. Verificar mnemonic completa
python3 wallet_bip39_off_line.py --mnemonic "word1 word2 ... word24" -i

# 3. Verificar análisis de seguridad

# 4. Comparar addresses generadas con las de tu wallet
```

### Para verificación educativa:

```bash
# 1. Generar wallet mostrando todo (SOLO en entorno seguro)
python3 wallet_bip39_off_line.py -w 12 --show-all

# 2. Estudiar análisis de seguridad y derivaciones

# 3. Estudiar estructura BIP32/BIP39

# 4. Borrar archivo después de estudiar
rm output/bip39_wallet_export.json
```

## Salida del script

### En terminal (por defecto):

- Coin type: Bitcoin
- Input mode: (words, entropy-bin, entropy-hex, mnemonic, mnemonic-incomplete)
- Network: mainnet/testnet
- Entropy: [OCULTO]
- Checksum: [OCULTO]
- **Análisis de seguridad**: Score, clasificación, tests
- Mnemonic: [OCULTO]
- BIP39 seed: [OCULTO]
- BIP32 root key: [OCULTO]
- Addresses (0): Solo primera address por ruta
- **Tipos de address**: P2PKH, P2WPKH-P2SH, P2WPKH, P2TR
- Extended public keys: xpub, ypub, zpub

### En archivo (desencriptado):

- TODOS los datos sensibles visibles
- 5 addresses por ruta (índices 0-4)
- Claves privadas en formato WIF
- Claves públicas en formato hex
- Extended public keys completas
- Análisis de seguridad completo con detalles de cada test

## Seguridad operacional

### Ejecución OFF-LINE (Recomendado)

**Ventajas:**
- ✅ Sin riesgo de exposición por red
- ✅ Sin riesgo de MITM (Man-in-the-Middle)
- ✅ Sin riesgo de DNS spoofing
- ✅ Control total del entorno

**Recomendaciones:**
- Usar máquina air-gapped (nunca conectada a internet)
- Usar sistema Live USB (Tails, Ubuntu Live)
- Verificar hashes de descargas antes de transferir
- Usar hardware wallet para almacenar las keys generadas
- Imprimir o escribir en papel la mnemonic generada
- Borrar todos los archivos después de usar

### Ejecución ON-LINE (No recomendado para producción)

**Riesgos:**
- ⚠️ Posible exposición de datos por red
- ⚠️ Riesgo de malware remoto
- ⚠️ Posible keylogger
- ⚠️ Riesgo de DNS spoofing
- ⚠️ Riesgo de MITM

**Si debes ejecutar on-line:**
- Usa una máquina virtual desechable
- No uses mnemonics reales (solo pruebas)
- Usa redes seguras (evita WiFi público)
- Verifica que el firewall esté activo
- No guardes archivos sensibles permanentemente
- Borra todo después de usar

## Desencriptar archivo

Para desencriptar el archivo de salida:

```python
from wallet_bip39_off_line import decrypt_file_content

# Leer archivo encriptado
encrypted_content = open('output/bip39_wallet_export.json').read()

# Desencriptar con contraseña
decrypted = decrypt_file_content(encrypted_content, 'TU_CONTRASEÑA')

# Mostrar contenido
print(decrypted)
```

O desde la terminal:

```bash
python3 -c "from wallet_bip39_off_line import decrypt_file_content; print(decrypt_file_content(open('output/bip39_wallet_export.json').read(), 'TU_CONTRASEÑA'))"
```

## Análisis Final del Script

### ✅ Seguridad

#### Criptografía
- ✅ **BIP39**: Implementación correcta con `mnemonic` library (Trezor)
- ✅ **BIP32**: Clave maestra calculada con HMAC-SHA512(Key="Bitcoin seed", Data=seed)
- ✅ **BIP44/49/84/86**: Derivación correcta con `bip-utils`
- ✅ **AES-256-GCM**: Encriptación de archivos con nonce aleatorio
- ✅ **SHA-256**: Derivación de clave desde contraseña

#### Generación de entropía
- ✅ `os.urandom()`: Entropía criptográficamente segura del sistema
- ✅ **Reintento automático**: Hasta obtener mnemonics sin repeticiones
- ✅ Longitudes válidas: 128, 160, 192, 224, 256 bits
- ✅ Checksum BIP39: Verificado correctamente

#### Análisis de seguridad
- ✅ **6 tests implementados**: Unicidad, entropía, secuencias, distribución, repetidas, manipulación
- ✅ **Score 0-100**: Clasificación automática
- ✅ **Detección de patrones**: Identifica mnemonics débiles o manipuladas
- ✅ **Umbrales ajustados**: Considera longitud de mnemonic

#### Protección de datos
- ✅ **Encriptación**: Siempre activa (AES-256-GCM)
- ✅ **Ocultamiento**: Datos sensibles ocultos en terminal por defecto
- ✅ **Input seguro**: `getpass.getpass()` sin eco ni historial
- ✅ **Permisos**: Archivos con 0o600 (solo propietario)
- ✅ **Escritura atómica**: `tempfile.mkstemp()` + `os.replace()`
- ✅ **Limpieza**: `readline.clear_history()` al finalizar

#### Validaciones
- ✅ Checksum BIP39 en mnemonics
- ✅ Longitud de palabras (12, 15, 18, 21, 24)
- ✅ Palabras del diccionario inglés
- ✅ **Verificación de wordlist**: Hash SHA256 contra lista oficial
- ✅ Round-trip: entropy ↔ mnemonic ↔ entropy
- ✅ Test vectors oficiales: 24 casos pasan

### ✅ Flujo de programación

#### Estructura del código
- ✅ **Separación de responsabilidades**: Cada función hace una cosa
- ✅ **Manejo de errores**: Mensajes claros y descriptivos
- ✅ **Validación de entrada**: Exclusión mutua entre métodos
- ✅ **Código limpio**: Sin duplicación, fácil de mantener

#### Funciones principales
1. `normalize_text()`: Normalización Unicode NFKD
2. `bytes_to_binary()`: Conversión a binario
3. `validate_entropy_length()`: Validación de longitud
4. `entropy_checksum_bits()`: Cálculo de checksum
5. `binary_to_bytes()`: Conversión de binario
6. `hex_to_bytes()`: Conversión de hexadecimal
7. `generate_entropy()`: Generación aleatoria con reintentos
8. `entropy_to_mnemonic()`: Conversión a mnemonic
9. `validate_mnemonic_text()`: Validación de mnemonic
10. `mnemonic_to_entropy()`: Conversión inversa
11. `mnemonic_seed()`: Seed BIP39 (PBKDF2)
12. `bip32_master_key()`: Clave maestra B-32 (HMAC-SHA512)
13. `select_network()`: Selección de red
14. `derive_addresses_*()`: Derivación BIP44/49/84/86 con tipos de address
15. `write_secure_file()`: Escritura segura encriptada
16. `generate_sequential_path()`: Nombres secuenciales
17. `audit_passphrase()`: Auditoría de passphrase
18. `get_secure_input()`: Input seguro
19. `find_last_word()`: Búsqueda de palabra faltante
20. `analizar_seguridad_mnemonic()`: **NUEVO** - Análisis de 6 tests
21. `resolve_input()`: Resolución de entrada
22. `build_context()`: Construcción de contexto
23. `format_report()`: Formateo de reporte con tipos de address
24. `export_wallet()`: Exportación de wallet
25. `run_bip39_test_vectors()`: Test vectors oficiales
26. `verify_against_bip39_official()`: **NUEVO** - Verificación de wordlist

#### Manejo de errores
- ✅ Validación de longitud de entropía
- ✅ Validación de checksum BIP39
- ✅ Validación de formato de archivo
- ✅ Manejo de EOF para input no interactivo
- ✅ Manejo de contraseñas no coincidentes
- ✅ **Reintento por repeticiones**: Máximo 1000 intentos

### ✅ Compatibilidad con estándares

#### BIP39
- ✅ Wordlist inglés (2048 palabras)
- ✅ Entropy: 128-256 bits
- ✅ Checksum: entropy_bits // 32
- ✅ Passphrase: Unicode NFKD, máximo 256 bytes
- ✅ Seed: PBKDF2-HMAC-SHA512, 2048 iteraciones

#### BIP32
- ✅ Clave maestra: HMAC-SHA512("Bitcoin seed", seed)
- ✅ Master key: 32 bytes
- ✅ Chain code: 32 bytes
- ✅ Derivación hardendada y normal

#### BIP44/49/84/86
- ✅ BIP44: m/44'/0'/0'/0/i (Legacy P2PKH)
- ✅ BIP49: m/49'/0'/0'/0/i (Nested SegWit P2SH-P2WPKH)
- ✅ BIP84: m/84'/0'/0'/0/i (Native SegWit P2WPKH)
- ✅ BIP86: m/86'/0'/0'/0/i (Taproot P2TR)
- ✅ Coin type: 0' (mainnet), 1' (testnet)

### ✅ Test vectors

#### Resultados
- ✅ **24 casos oficiales de Trezor**: PASAN
- ✅ **Mnemonic generation**: Correcta
- ✅ **Seed derivation**: Correcta (passphrase "TREZOR")
- ✅ **Round-trip**: entropy → mnemonic → entropy
- ✅ **Wordlist verification**: Hash SHA256 verificado

### ⚠️ Consideraciones

#### Dependencias
- ⚠️ `cryptography`: Requerida para encriptación
- ⚠️ `mnemonic`: Requerida para BIP39
- ⚠️ `bip-utils`: Requerida para derivación

#### Limitaciones documentadas
- ⚠️ No certifica entropía manual imprevisible
- ⚠️ No certifica entorno no comprometido
- ⚠️ No certifica errores de usuario
- ⚠️ GAP limit: 5 addresses (suficiente para prueba)
- ⚠️ **Análisis de seguridad es estadístico**: No garantiza seguridad absoluta

#### Mejores prácticas
- ✅ Solo offline en entorno confiable
- ✅ Verificar en hardware wallet antes de usar
- ✅ Guardar mnemonic en papel/metal (nunca digital)
- ✅ Usar passphrase única y segura
- ✅ Borrar archivos después de usar
- ✅ **Verificar score de seguridad > 80**

### ✅ Resumen final

El script está **completo, seguro y listo para uso educativo**. Cumple con:

- ✅ Estándares BIP39, BIP32, BIP44, BIP49, BIP84, BIP86
- ✅ Seguridad criptográfica adecuada
- ✅ Protección de datos sensibles
- ✅ Test vectors oficiales aprobados
- ✅ **Análisis de seguridad con 6 tests**
- ✅ **Generación sin repeticiones**
- ✅ **Verificación de wordlist oficial**
- ✅ **Tipos de address documentados**
- ✅ Código limpio y mantenible
- ✅ Documentación completa (README)

**Recomendación**: El script puede usarse para generación y verificación de wallets Bitcoin en entornos offline seguros, siempre siguiendo las mejores prácticas de seguridad operacional.

## Advertencias finales

**IMPORTANTE:**
- Este script es solo para fines educativos y de prueba
- No certifica que el sistema tiene suficiente entropía acumulada
- No certifica que una entropía manual sea imprevisible
- No certifica que el entorno no esté comprometido
- No certifica que no haya errores de usuario
- El script es seguro solo si se ejecuta offline, en entorno confiable, con entropía correcta
- **Use el script con prudencia**
- **NUNCA uses mnemonics reales en máquinas conectadas a internet**
- **SIEMPRE verifica las addresses generadas en una wallet hardware antes de usar**
- **No auditado para producción**: Este es un proyecto educativo. No ha sido auditado por firmas de seguridad independientes. Si consideras usarlo con fondos reales (*no recomendado*), entiende los riesgos documentados y se repite la **advertencia**, verifica siempre las addresses en una hardware wallet antes de depositar.
- **El análisis de seguridad es una guía estadística**: Un score alto no garantiza seguridad absoluta, pero un score bajo indica problemas potenciales.

## Licencia

PROGRAMA SOLO CON FINES EDUCATIVOS Y DE PRUEBA

## Contacto

**Para reportar errores o sugerencias, usa issues en el repositorio.**
