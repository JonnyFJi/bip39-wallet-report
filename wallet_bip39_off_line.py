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
from collections import Counter
import math

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

# ============================================================================
# WORDLIST BIP39 OFICIAL EMBEBIDA
# Fuente: https://github.com/bitcoin/bips/blob/master/bip-0039/english.txt
# Hash SHA256: 187db04a869dd9bc7be80d21a86497d692c0db6abd3aa8cb6be5d618ff757fae
# ============================================================================

BIP39_OFFICIAL_WORDLIST = [
    "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
    "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert",
    "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter",
    "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
    "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic",
    "area", "arena", "argue", "arm", "armed", "armor", "army", "around", "arrange", "arrest",
    "arrive", "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset",
    "assist", "assume", "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract", "auction",
    "audit", "august", "aunt", "author", "auto", "autumn", "average", "avocado", "avoid", "awake",
    "aware", "away", "awesome", "awful", "awkward", "axis", "baby", "bachelor", "bacon", "badge",
    "bag", "balance", "balcony", "ball", "bamboo", "banana", "banner", "bar", "barely", "bargain",
    "barrel", "base", "basic", "basket", "battle", "beach", "bean", "beauty", "because", "become",
    "beef", "before", "begin", "behave", "behind", "believe", "below", "belt", "bench", "benefit",
    "best", "betray", "better", "between", "beyond", "bicycle", "bid", "bike", "bind", "biology",
    "bird", "birth", "bitter", "black", "blade", "blame", "blanket", "blast", "bleak", "bless",
    "blind", "blood", "blossom", "blouse", "blue", "blur", "blush", "board", "boat", "body",
    "boil", "bomb", "bone", "bonus", "book", "boost", "border", "boring", "borrow", "boss",
    "bottom", "bounce", "box", "boy", "bracket", "brain", "brand", "brass", "brave", "bread",
    "breeze", "brick", "bridge", "brief", "bright", "bring", "brisk", "broccoli", "broken", "bronze",
    "broom", "brother", "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb",
    "bulk", "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus", "business", "busy",
    "butter", "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake", "call",
    "calm", "camera", "camp", "can", "canal", "cancel", "candy", "cannon", "canoe", "canvas",
    "canyon", "capable", "capital", "captain", "car", "carbon", "card", "cargo", "carpet", "carry",
    "cart", "case", "cash", "casino", "castle", "casual", "cat", "catalog", "catch", "category",
    "cattle", "caught", "cause", "caution", "cave", "ceiling", "celery", "cement", "census", "century",
    "cereal", "certain", "chair", "chalk", "champion", "change", "chaos", "chapter", "charge", "chase",
    "chat", "cheap", "check", "cheese", "chef", "cherry", "chest", "chicken", "chief", "child",
    "chimney", "choice", "choose", "chronic", "chuckle", "chunk", "churn", "cigar", "cinnamon", "circle",
    "citizen", "city", "civil", "claim", "clap", "clarify", "claw", "clay", "clean", "clerk",
    "clever", "click", "client", "cliff", "climb", "clinic", "clip", "clock", "clog", "close",
    "cloth", "cloud", "clown", "club", "clump", "cluster", "clutch", "coach", "coast", "coconut",
    "code", "coffee", "coil", "coin", "collect", "color", "column", "combine", "come", "comfort",
    "comic", "common", "company", "concert", "conduct", "confirm", "congress", "connect", "consider", "control",
    "convince", "cook", "cool", "copper", "copy", "coral", "core", "corn", "correct", "cost",
    "cotton", "couch", "country", "couple", "course", "cousin", "cover", "coyote", "crack", "cradle",
    "craft", "cram", "crane", "crash", "crater", "crawl", "crazy", "cream", "credit", "creek",
    "crew", "cricket", "crime", "crisp", "critic", "crop", "cross", "crouch", "crowd", "crucial",
    "cruel", "cruise", "crumble", "crunch", "crush", "cry", "crystal", "cube", "culture", "cup",
    "cupboard", "curious", "current", "curtain", "curve", "cushion", "custom", "cute", "cycle", "dad",
    "damage", "damp", "dance", "danger", "daring", "dash", "daughter", "dawn", "day", "deal",
    "debate", "debris", "decade", "december", "decide", "decline", "decorate", "decrease", "deer", "defense",
    "define", "defy", "degree", "delay", "deliver", "demand", "demise", "denial", "dentist", "deny",
    "depart", "depend", "deposit", "depth", "deputy", "derive", "describe", "desert", "design", "desk",
    "despair", "destroy", "detail", "detect", "develop", "device", "devote", "diagram", "dial", "diamond",
    "diary", "dice", "diesel", "diet", "differ", "digital", "dignity", "dilemma", "dinner", "dinosaur",
    "direct", "dirt", "disagree", "discover", "disease", "dish", "dismiss", "disorder", "display", "distance",
    "divert", "divide", "divorce", "dizzy", "doctor", "document", "dog", "doll", "dolphin", "domain",
    "donate", "donkey", "donor", "door", "dose", "double", "dove", "draft", "dragon", "drama",
    "drastic", "draw", "dream", "dress", "drift", "drill", "drink", "drip", "drive", "drop",
    "drum", "dry", "duck", "dumb", "dune", "during", "dust", "dutch", "duty", "dwarf",
    "dynamic", "eager", "eagle", "early", "earn", "earth", "easily", "east", "easy", "echo",
    "ecology", "economy", "edge", "edit", "educate", "effort", "egg", "eight", "either", "elbow",
    "elder", "electric", "elegant", "element", "elephant", "elevator", "elite", "else", "embark", "embody",
    "embrace", "emerge", "emotion", "employ", "empower", "empty", "enable", "enact", "end", "endless",
    "endorse", "enemy", "energy", "enforce", "engage", "engine", "enhance", "enjoy", "enlist", "enough",
    "enrich", "enroll", "ensure", "enter", "entire", "entry", "envelope", "episode", "equal", "equip",
    "era", "erase", "erode", "erosion", "error", "erupt", "escape", "essay", "essence", "estate",
    "eternal", "ethics", "evidence", "evil", "evoke", "evolve", "exact", "example", "excess", "exchange",
    "excite", "exclude", "excuse", "execute", "exercise", "exhaust", "exhibit", "exile", "exist", "exit",
    "exotic", "expand", "expect", "expire", "explain", "expose", "express", "extend", "extra", "eye",
    "eyebrow", "fabric", "face", "faculty", "fade", "faint", "faith", "fall", "false", "fame",
    "family", "famous", "fan", "fancy", "fantasy", "farm", "fashion", "fat", "fatal", "father",
    "fatigue", "fault", "favorite", "feature", "february", "federal", "fee", "feed", "feel", "female",
    "fence", "festival", "fetch", "fever", "few", "fiber", "fiction", "field", "figure", "file",
    "film", "filter", "final", "find", "fine", "finger", "finish", "fire", "firm", "first",
    "fiscal", "fish", "fit", "fitness", "fix", "flag", "flame", "flash", "flat", "flavor",
    "flee", "flight", "flip", "float", "flock", "floor", "flower", "fluid", "flush", "fly",
    "foam", "focus", "fog", "foil", "fold", "follow", "food", "foot", "force", "forest",
    "forget", "fork", "fortune", "forum", "forward", "fossil", "foster", "found", "fox", "fragile",
    "frame", "frequent", "fresh", "friend", "fringe", "frog", "front", "frost", "frown", "frozen",
    "fruit", "fuel", "fun", "funny", "furnace", "fury", "future", "gadget", "gain", "galaxy",
    "gallery", "game", "gap", "garage", "garbage", "garden", "garlic", "garment", "gas", "gasp",
    "gate", "gather", "gauge", "gaze", "general", "genius", "genre", "gentle", "genuine", "gesture",
    "ghost", "giant", "gift", "giggle", "ginger", "giraffe", "girl", "give", "glad", "glance",
    "glare", "glass", "glide", "glimpse", "globe", "gloom", "glory", "glove", "glow", "glue",
    "goat", "goddess", "gold", "good", "goose", "gorilla", "gospel", "gossip", "govern", "gown",
    "grab", "grace", "grain", "grant", "grape", "grass", "gravity", "great", "green", "grid",
    "grief", "grit", "grocery", "group", "grow", "grunt", "guard", "guess", "guide", "guilt",
    "guitar", "gun", "gym", "habit", "hair", "half", "hammer", "hamster", "hand", "happy",
    "harbor", "hard", "harsh", "harvest", "hat", "have", "hawk", "hazard", "head", "health",
    "heart", "heavy", "hedgehog", "height", "hello", "helmet", "help", "hen", "hero", "hidden",
    "high", "hill", "hint", "hip", "hire", "history", "hobby", "hockey", "hold", "hole",
    "holiday", "hollow", "home", "honey", "hood", "hope", "horn", "horror", "horse", "hospital",
    "host", "hotel", "hour", "hover", "hub", "huge", "human", "humble", "humor", "hundred",
    "hungry", "hunt", "hurdle", "hurry", "hurt", "husband", "hybrid", "ice", "icon", "idea",
    "identify", "idle", "ignore", "ill", "illegal", "illness", "image", "imitate", "immense", "immune",
    "impact", "impose", "improve", "impulse", "inch", "include", "income", "increase", "index", "indicate",
    "indoor", "industry", "infant", "inflict", "inform", "inhale", "inherit", "initial", "inject", "injury",
    "inmate", "inner", "innocent", "input", "inquiry", "insane", "insect", "inside", "inspire", "install",
    "intact", "interest", "into", "invest", "invite", "involve", "iron", "island", "isolate", "issue",
    "item", "ivory", "jacket", "jaguar", "jar", "jazz", "jealous", "jeans", "jelly", "jewel",
    "job", "join", "joke", "journey", "joy", "judge", "juice", "jump", "jungle", "junior",
    "junk", "just", "kangaroo", "keen", "keep", "ketchup", "key", "kick", "kid", "kidney",
    "kind", "kingdom", "kiss", "kit", "kitchen", "kite", "kitten", "kiwi", "knee", "knife",
    "knock", "know", "lab", "label", "labor", "ladder", "lady", "lake", "lamp", "language",
    "laptop", "large", "later", "latin", "laugh", "laundry", "lava", "law", "lawn", "lawsuit",
    "layer", "lazy", "leader", "leaf", "learn", "leave", "lecture", "left", "leg", "legal",
    "legend", "leisure", "lemon", "lend", "length", "lens", "leopard", "lesson", "letter", "level",
    "liar", "liberty", "library", "license", "life", "lift", "light", "like", "limb", "limit",
    "link", "lion", "liquid", "list", "little", "live", "lizard", "load", "loan", "lobster",
    "local", "lock", "logic", "lonely", "long", "loop", "lottery", "loud", "lounge", "love",
    "loyal", "lucky", "luggage", "lumber", "lunar", "lunch", "luxury", "lyrics", "machine", "mad",
    "magic", "magnet", "maid", "mail", "main", "major", "make", "mammal", "man", "manage",
    "mandate", "mango", "mansion", "manual", "maple", "marble", "march", "margin", "marine", "market",
    "marriage", "mask", "mass", "master", "match", "material", "math", "matrix", "matter", "maximum",
    "maze", "meadow", "mean", "measure", "meat", "mechanic", "medal", "media", "melody", "melt",
    "member", "memory", "mention", "menu", "mercy", "merge", "merit", "merry", "mesh", "message",
    "metal", "method", "middle", "midnight", "milk", "million", "mimic", "mind", "minimum", "minor",
    "minute", "miracle", "mirror", "misery", "miss", "mistake", "mix", "mixed", "mixture", "mobile",
    "model", "modify", "mom", "moment", "monitor", "monkey", "monster", "month", "moon", "moral",
    "more", "morning", "mosquito", "mother", "motion", "motor", "mountain", "mouse", "move", "movie",
    "much", "muffin", "mule", "multiply", "muscle", "museum", "mushroom", "music", "must", "mutual",
    "myself", "mystery", "myth", "naive", "name", "napkin", "narrow", "nasty", "nation", "nature",
    "near", "neck", "need", "negative", "neglect", "neither", "nephew", "nerve", "nest", "net",
    "network", "neutral", "never", "news", "next", "nice", "night", "noble", "noise", "nominee",
    "noodle", "normal", "north", "nose", "notable", "note", "nothing", "notice", "novel", "now",
    "nuclear", "number", "nurse", "nut", "oak", "obey", "object", "oblige", "obscure", "observe",
    "obtain", "obvious", "occur", "ocean", "october", "odor", "off", "offer", "office", "often",
    "oil", "okay", "old", "olive", "olympic", "omit", "once", "one", "onion", "online",
    "only", "open", "opera", "opinion", "oppose", "option", "orange", "orbit", "orchard", "order",
    "ordinary", "organ", "orient", "original", "orphan", "ostrich", "other", "outdoor", "outer", "output",
    "outside", "oval", "oven", "over", "own", "owner", "oxygen", "oyster", "ozone", "pact",
    "paddle", "page", "pair", "palace", "palm", "panda", "panel", "panic", "panther", "paper",
    "parade", "parent", "park", "parrot", "party", "pass", "patch", "path", "patient", "patrol",
    "pattern", "pause", "pave", "payment", "peace", "peanut", "pear", "peasant", "pelican", "pen",
    "penalty", "pencil", "people", "pepper", "perfect", "permit", "person", "pet", "phone", "photo",
    "phrase", "physical", "piano", "picnic", "picture", "piece", "pig", "pigeon", "pill", "pilot",
    "pink", "pioneer", "pipe", "pistol", "pitch", "pizza", "place", "planet", "plastic", "plate",
    "play", "please", "pledge", "pluck", "plug", "plunge", "poem", "poet", "point", "polar",
    "pole", "police", "pond", "pony", "pool", "popular", "portion", "position", "possible", "post",
    "potato", "pottery", "poverty", "powder", "power", "practice", "praise", "predict", "prefer", "prepare",
    "present", "pretty", "prevent", "price", "pride", "primary", "print", "priority", "prison", "private",
    "prize", "problem", "process", "produce", "profit", "program", "project", "promote", "proof", "property",
    "prosper", "protect", "proud", "provide", "public", "pudding", "pull", "pulp", "pulse", "pumpkin",
    "punch", "pupil", "puppy", "purchase", "purity", "purpose", "purse", "push", "put", "puzzle",
    "pyramid", "quality", "quantum", "quarter", "question", "quick", "quit", "quiz", "quote", "rabbit",
    "raccoon", "race", "rack", "radar", "radio", "rail", "rain", "raise", "rally", "ramp",
    "ranch", "random", "range", "rapid", "rare", "rate", "rather", "raven", "raw", "razor",
    "ready", "real", "reason", "rebel", "rebuild", "recall", "receive", "recipe", "record", "recycle",
    "reduce", "reflect", "reform", "refuse", "region", "regret", "regular", "reject", "relax", "release",
    "relief", "rely", "remain", "remember", "remind", "remove", "render", "renew", "rent", "reopen",
    "repair", "repeat", "replace", "report", "require", "rescue", "resemble", "resist", "resource", "response",
    "result", "retire", "retreat", "return", "reunion", "reveal", "review", "reward", "rhythm", "rib",
    "ribbon", "rice", "rich", "ride", "ridge", "rifle", "right", "rigid", "ring", "riot",
    "ripple", "risk", "ritual", "rival", "river", "road", "roast", "robot", "robust", "rocket",
    "romance", "roof", "rookie", "room", "rose", "rotate", "rough", "round", "route", "royal",
    "rubber", "rude", "rug", "rule", "run", "runway", "rural", "sad", "saddle", "sadness",
    "safe", "sail", "salad", "salmon", "salon", "salt", "salute", "same", "sample", "sand",
    "satisfy", "satoshi", "sauce", "sausage", "save", "say", "scale", "scan", "scare", "scatter",
    "scene", "scheme", "school", "science", "scissors", "scorpion", "scout", "scrap", "screen", "script",
    "scrub", "sea", "search", "season", "seat", "second", "secret", "section", "security", "seed",
    "seek", "segment", "select", "sell", "seminar", "senior", "sense", "sentence", "series", "service",
    "session", "settle", "setup", "seven", "shadow", "shaft", "shallow", "share", "shed", "shell",
    "sheriff", "shield", "shift", "shine", "ship", "shiver", "shock", "shoe", "shoot", "shop",
    "short", "shoulder", "shove", "shrimp", "shrug", "shuffle", "shy", "sibling", "sick", "side",
    "siege", "sight", "sign", "silent", "silk", "silly", "silver", "similar", "simple", "since",
    "sing", "siren", "sister", "situate", "six", "size", "skate", "sketch", "ski", "skill",
    "skin", "skirt", "skull", "slab", "slam", "sleep", "slender", "slice", "slide", "slight",
    "slim", "slogan", "slot", "slow", "slush", "small", "smart", "smile", "smoke", "smooth",
    "snack", "snake", "snap", "sniff", "snow", "soap", "soccer", "social", "sock", "soda",
    "soft", "solar", "soldier", "solid", "solution", "solve", "someone", "song", "soon", "sorry",
    "sort", "soul", "sound", "soup", "source", "south", "space", "spare", "spatial", "spawn",
    "speak", "special", "speed", "spell", "spend", "sphere", "spice", "spider", "spike", "spin",
    "spirit", "split", "spoil", "sponsor", "spoon", "sport", "spot", "spray", "spread", "spring",
    "spy", "square", "squeeze", "squirrel", "stable", "stadium", "staff", "stage", "stairs", "stamp",
    "stand", "start", "state", "stay", "steak", "steel", "stem", "step", "stereo", "stick",
    "still", "sting", "stock", "stomach", "stone", "stool", "story", "stove", "strategy", "street",
    "strike", "strong", "struggle", "student", "stuff", "stumble", "style", "subject", "submit", "subway",
    "success", "such", "sudden", "suffer", "sugar", "suggest", "suit", "summer", "sun", "sunny",
    "sunset", "super", "supply", "supreme", "sure", "surface", "surge", "surprise", "surround", "survey",
    "suspect", "sustain", "swallow", "swamp", "swap", "swarm", "swear", "sweet", "swift", "swim",
    "swing", "switch", "sword", "symbol", "symptom", "syrup", "system", "table", "tackle", "tag",
    "tail", "talent", "talk", "tank", "tape", "target", "task", "taste", "tattoo", "taxi",
    "teach", "team", "tell", "ten", "tenant", "tennis", "tent", "term", "test", "text",
    "thank", "that", "theme", "then", "theory", "there", "they", "thing", "this", "thought",
    "three", "thrive", "throw", "thumb", "thunder", "ticket", "tide", "tiger", "tilt", "timber",
    "time", "tiny", "tip", "tired", "tissue", "title", "toast", "tobacco", "today", "toddler",
    "toe", "together", "toilet", "token", "tomato", "tomorrow", "tone", "tongue", "tonight", "tool",
    "tooth", "top", "topic", "topple", "torch", "tornado", "tortoise", "toss", "total", "tourist",
    "toward", "tower", "town", "toy", "track", "trade", "traffic", "tragic", "train", "transfer",
    "trap", "trash", "travel", "tray", "treat", "tree", "trend", "trial", "tribe", "trick",
    "trigger", "trim", "trip", "trophy", "trouble", "truck", "true", "truly", "trumpet", "trust",
    "truth", "try", "tube", "tuition", "tumble", "tuna", "tunnel", "turkey", "turn", "turtle",
    "twelve", "twenty", "twice", "twin", "twist", "two", "type", "typical", "ugly", "umbrella",
    "unable", "unaware", "uncle", "uncover", "under", "undo", "unfair", "unfold", "unhappy", "uniform",
    "unique", "unit", "universe", "unknown", "unlock", "until", "unusual", "unveil", "update", "upgrade",
    "uphold", "upon", "upper", "upset", "urban", "urge", "usage", "use", "used", "useful",
    "useless", "usual", "utility", "vacant", "vacuum", "vague", "valid", "valley", "valve", "van",
    "vanish", "vapor", "various", "vast", "vault", "vehicle", "velvet", "vendor", "venture", "venue",
    "verb", "verify", "version", "very", "vessel", "veteran", "viable", "vibrant", "vicious", "victory",
    "video", "view", "village", "vintage", "violin", "virtual", "virus", "visa", "visit", "visual",
    "vital", "vivid", "vocal", "voice", "void", "volcano", "volume", "vote", "voyage", "wage",
    "wagon", "wait", "walk", "wall", "walnut", "want", "warfare", "warm", "warrior", "wash",
    "wasp", "waste", "water", "wave", "way", "wealth", "weapon", "wear", "weasel", "weather",
    "web", "wedding", "weekend", "weird", "welcome", "west", "wet", "whale", "what", "wheat",
    "wheel", "when", "where", "whip", "whisper", "wide", "width", "wife", "wild", "will",
    "win", "window", "wine", "wing", "wink", "winner", "winter", "wire", "wisdom", "wise",
    "wish", "witness", "wolf", "woman", "wonder", "wood", "wool", "word", "work", "world",
    "worry", "worth", "wrap", "wreck", "wrestle", "wrist", "write", "wrong", "yard", "year",
    "yellow", "you", "young", "youth", "zebra", "zero", "zone", "zoo"
]

BIP39_OFFICIAL_SHA256 = "187db04a869dd9bc7be80d21a86497d692c0db6abd3aa8cb6be5d618ff757fae"


def verify_against_bip39_official():
    """Verifica que la wordlist embebida coincida con BIP39 oficial (offline)"""
    if len(BIP39_OFFICIAL_WORDLIST) != 2048:
        print(f"\n❌ ERROR: BIP39 oficial embebida tiene {len(BIP39_OFFICIAL_WORDLIST)} palabras")
        return False

    official_hash = hashlib.sha256("\n".join(BIP39_OFFICIAL_WORDLIST).encode("utf-8")).hexdigest()
    if official_hash != BIP39_OFFICIAL_SHA256:
        print(f"\n❌ ERROR: Hash BIP39 oficial incorrecto")
        print(f"   Esperado: {BIP39_OFFICIAL_SHA256}")
        print(f"   Obtenido: {official_hash}")
        return False

    print("✅ BIP39 Oficial (GitHub): VERIFICADA (2048 palabras)")
    return True


VALID_ENTROPY_BITS = {128, 160, 192, 224, 256}
VALID_WORD_COUNTS = {12, 15, 18, 21, 24}
DEFAULT_VECTORS_FILE = "vectors.json"
GAP_LIMIT = 5


def normalize_text(text):
    return unicodedata.normalize("NFKD", text)


def bytes_to_binary(data):
    return "".join(f"{byte:08b}" for byte in data)


def validate_entropy_length(bit_len):
    if bit_len not in VALID_ENTROPY_BITS:
        raise ValueError("La entropía debe ser 128, 160, 192, 224 o 256 bits.")


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
        raise ValueError("BIP39 solo admite 12, 15, 18, 21 o 24 palabras.")
    return os.urandom({12: 16, 15: 20, 18: 24, 21: 28, 24: 32}[words])


def entropy_to_mnemonic(entropy):
    return Mnemonic("english").to_mnemonic(entropy)


def validate_mnemonic_text(mnemonic):
    phrase = normalize_text(mnemonic).strip()
    words = phrase.split()
    if len(words) not in VALID_WORD_COUNTS:
        raise ValueError("La mnemonic debe tener 12, 15, 18, 21 o 24 palabras.")
    mnemo = Mnemonic("english")
    if not mnemo.check(phrase):
        raise ValueError("La mnemonic no es válida o su checksum no coincide.")
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
    return Bip39SeedGenerator(normalize_text(mnemonic)).Generate(normalize_text(passphrase))


def bip32_master_key(seed):
    I = hmac.new(key=b"Bitcoin seed", msg=seed, digestmod=hashlib.sha512).digest()
    return I[:32].hex(), I[32:].hex()


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
    return {
        "path_template": f"m/44'/{coin_type}/0'/0/i",
        "xpub": account.PublicKey().ToExtended(),
        "addresses": addresses,
        "address_type": "P2PKH",
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
    return {
        "path_template": f"m/49'/{coin_type}/0'/0/i",
        "ypub": account.PublicKey().ToExtended(),
        "addresses": addresses,
        "address_type": "P2WPKH-P2SH",
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
    return {
        "path_template": f"m/84'/{coin_type}/0'/0/i",
        "zpub": account.PublicKey().ToExtended(),
        "addresses": addresses,
        "address_type": "P2WPKH",
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
        "address_type": "P2TR",
    }


def write_secure_file(path, content, encrypt=True, password=None):
    destination = pathlib.Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    if CRYPTO_AVAILABLE and password:
        key = hashlib.sha256(password.encode("utf-8")).digest()
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, content.encode("utf-8"), associated_data=None)
        content_to_write = "ENCRYPTED:" + base64.b64encode(nonce + ciphertext).decode("utf-8")
    else:
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
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("La librería 'cryptography' no está instalada.")
    if not encrypted_content.startswith("ENCRYPTED:"):
        raise ValueError("El archivo no está encriptado o tiene formato inválido.")
    encrypted_data = base64.b64decode(encrypted_content[10:])
    nonce, ciphertext = encrypted_data[:12], encrypted_data[12:]
    key = hashlib.sha256(password.encode("utf-8")).digest()
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    return plaintext.decode("utf-8")


def generate_sequential_path(base_path):
    destination = pathlib.Path(base_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        return destination
    stem, suffix, parent = destination.stem, destination.suffix, destination.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter:03d}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def audit_passphrase(passphrase):
    normalized = normalize_text(passphrase)
    utf8_bytes = normalized.encode("utf-8")
    return {
        "present": len(normalized) > 0,
        "characters": len(normalized),
        "utf8_bytes": len(utf8_bytes),
        "unique_characters": len(set(normalized)),
        "has_lowercase": any(c.islower() for c in normalized),
        "has_uppercase": any(c.isupper() for c in normalized),
        "has_digits": any(c.isdigit() for c in normalized),
        "has_symbols": any(not c.isalnum() and not c.isspace() for c in normalized),
        "has_spaces": any(c.isspace() for c in normalized),
        "classification": "vacía" if len(normalized) == 0 else "proporcionada por el usuario",
        "security_note": "No añade incertidumbre adicional." if len(normalized) == 0 else "No es posible calcular su entropía real sin conocer el proceso aleatorio utilizado para elegirla.",
    }


def attempt_clear_history():
    try:
        import readline
        readline.clear_history()
    except Exception:
        pass


def get_secure_input(prompt, allow_empty=False):
    while True:
        value = getpass.getpass(prompt)
        if value or allow_empty:
            return value
        print("⚠️  Este campo no puede estar vacío. Intenta nuevamente.")


def find_last_word(incomplete_phrase):
    mnemo = Mnemonic("english")
    wordlist = mnemo.wordlist
    words = incomplete_phrase.strip().split()
    if len(words) == 11:
        entropy_bits = 128
    elif len(words) == 23:
        entropy_bits = 256
    else:
        raise ValueError("Solo se pueden calcular mnemonics de 11→12 o 23→24 palabras.")
    checksum_bits = entropy_bits // 32
    valid_candidates = []
    print(f"Buscando palabras para completar mnemonic de {len(words)} palabras...")
    print(f"Checksum de {checksum_bits} bits = {2**checksum_bits} posibilidades teóricas")
    for candidate_word in wordlist:
        if mnemo.check(incomplete_phrase + " " + candidate_word):
            valid_candidates.append(candidate_word)
    return valid_candidates


def get_secure_mnemonic():
    print("\n📝 Ingresa la mnemonic (las palabras se ocultarán mientras escribes):")
    print("   Escribe todas las palabras separadas por espacios.")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Mnemonic: ").strip()


def get_secure_entropy_hex():
    print("\n🔢 Ingresa la entropía hexadecimal (oculto):")
    print("   Debe ser 32, 40, 48, 56 o 64 caracteres hexadecimales.")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Entropy hex: ").strip()


def get_secure_entropy_bin():
    print("\n🔢 Ingresa la entropía binaria (oculto):")
    print("   Debe ser 128, 160, 192, 224 o 256 bits (solo 0 y 1).")
    print("   Presiona Enter cuando termines.\n")
    return get_secure_input("Entropy bin: ").strip()


def get_secure_passphrase():
    print("\n🔐 Ingresa la passphrase BIP39 (opcional, oculto):")
    print("   Presiona Enter para dejarla vacía si no quieres usar una.\n")
    return get_secure_input("Passphrase: ", allow_empty=True)


def analizar_seguridad_mnemonic(mnemonic):
    mnemo = Mnemonic("english")
    words = mnemonic.strip().split()
    word_count = len(words)
    if word_count not in [12, 15, 18, 21, 24]:
        return {"valido": False, "error": "Número de palabras inválido", "score": 0}
    if not mnemo.check(mnemonic):
        return {"valido": False, "error": "Checksum BIP39 inválido", "score": 0}

    indices = [mnemo.wordlist.index(w) for w in words]
    unique_words = len(set(words))
    freq = Counter(words)

    ratio_unicidad = unique_words / word_count
    score_unicidad = 100 if ratio_unicidad >= 0.9 else (ratio_unicidad * 100)

    entropia_shannon = -sum((c/word_count) * math.log2(c/word_count) for c in freq.values())
    max_entropia = math.log2(word_count)
    ratio_entropia = entropia_shannon / max_entropia
    score_entropia = ratio_entropia * 100

    secuencias = sum(1 for i in range(1, len(indices)) if indices[i] == indices[i-1] + 1)
    score_secuencias = 100 if secuencias == 0 else max(0, 100 - (secuencias * 20))

    media = sum(indices) / len(indices)
    varianza = sum((i - media) ** 2 for i in indices) / len(indices)
    varianza_esperada = (2048 ** 2) / 12
    score_distribucion = min(varianza / varianza_esperada, 1.0) * 100

    repetidas_consecutivas = sum(1 for i in range(1, len(words)) if words[i] == words[i-1])
    palabras_repetidas_total = word_count - unique_words
    palabras_con_repetidos = sum(1 for _, count in freq.items() if count > 1)
    score_repetidas = 100 if palabras_repetidas_total == 0 else max(0, 100 - (palabras_repetidas_total * 25))

    porcentaje_repeticion = (palabras_repetidas_total / word_count) * 100

    if porcentaje_repeticion > 5:
        alerta_manipulacion = "ALTA"
        mensaje_manipulacion = "Posible manipulación manual detectada (repetición inusual)"
        score_manipulacion = 40
    elif porcentaje_repeticion > 2:
        alerta_manipulacion = "MODERADA"
        mensaje_manipulacion = "Verifica origen de las palabras (repetición moderada)"
        score_manipulacion = 70
    else:
        alerta_manipulacion = "BAJA"
        mensaje_manipulacion = "Distribución normal esperada"
        score_manipulacion = 100

    score_final = (
        score_unicidad * 0.20 +
        score_entropia * 0.20 +
        score_secuencias * 0.20 +
        score_distribucion * 0.15 +
        score_repetidas * 0.15 +
        score_manipulacion * 0.10
    )

    if score_final >= 80 and alerta_manipulacion == "BAJA":
        clasificacion = "✅ FUERTE - Entropía adecuada"
        recomendacion = "Esta mnemonic parece tener buena aleatoriedad."
    elif score_final >= 60 and alerta_manipulacion in ["BAJA", "MODERADA"]:
        clasificacion = "⚠️  MODERADA - Posibles patrones menores"
        recomendacion = "Verifica que fue generada con RNG criptográfico."
    elif score_final >= 40 or alerta_manipulacion == "MODERADA":
        clasificacion = "⚠️  DÉBIL - Patrones detectados"
        recomendacion = "Considera generar una nueva mnemonic con mejor entropía."
    else:
        clasificacion = "❌ MUY DÉBIL - Alta probabilidad de baja entropía"
        recomendacion = "NO uses esta mnemonic. Genera una nueva con RNG criptográfico."

    if alerta_manipulacion == "ALTA":
        clasificacion = "⚠️  DÉBIL - Posible manipulación manual"
        recomendacion = "Verifica origen de las palabras. Considera generar una nueva mnemonic."

    return {
        "valido": True,
        "palabras": word_count,
        "entropia_bits": {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}[word_count],
        "palabras_unicas": unique_words,
        "ratio_unicidad": f"{ratio_unicidad:.2%}",
        "entropia_shannon": f"{entropia_shannon:.2f} bits",
        "ratio_entropia": f"{ratio_entropia:.2%}",
        "secuencias_detectadas": secuencias,
        "repetidas_consecutivas": repetidas_consecutivas,
        "palabras_repetidas_total": palabras_repetidas_total,
        "palabras_con_repetidos": palabras_con_repetidos,
        "porcentaje_repeticion": f"{porcentaje_repeticion:.2%}",
        "alerta_manipulacion": alerta_manipulacion,
        "mensaje_manipulacion": mensaje_manipulacion,
        "score": round(score_final, 1),
        "clasificacion": clasificacion,
        "recomendacion": recomendacion,
        "detalles": {
            "score_unicidad": round(score_unicidad, 1),
            "score_entropia": round(score_entropia, 1),
            "score_secuencias": round(score_secuencias, 1),
            "score_distribucion": round(score_distribucion, 1),
            "score_repetidas": round(score_repetidas, 1),
            "score_manipulacion": round(score_manipulacion, 1),
        }
    }


def resolve_input(args, interactive=False):
    if interactive:
        has_words = args.words is not None
        has_entropy_bin = bool(args.entropy_bin)
        has_entropy_hex = bool(args.entropy_hex)
        has_mnemonic = bool(args.mnemonic)
        has_mnemonic_incomplete = bool(args.mnemonic_incomplete)

        input_count = sum([has_words, has_entropy_bin, has_entropy_hex, has_mnemonic, has_mnemonic_incomplete])

        if input_count == 0:
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

        if not args.passphrase:
            args.passphrase = get_secure_passphrase()

    if sum(1 for x in [args.words, args.entropy_bin, args.entropy_hex, args.mnemonic, args.mnemonic_incomplete] if x) != 1:
        raise ValueError("Debes proporcionar exactamente una entrada entre -w/--words, --entropy-bin, --entropy-hex, --mnemonic o --mnemonic-incomplete.")

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
        incomplete_phrase = normalize_text(args.mnemonic_incomplete).strip()
        candidates = find_last_word(incomplete_phrase)

        if not candidates:
            raise ValueError("No se encontró ninguna palabra válida. Verifica que las palabras sean correctas.")

        print(f"\n✅ Se encontraron {len(candidates)} palabra(s) posible(s):\n")
        for i, word in enumerate(candidates, start=1):
            print(f"  [{i:2d}] {word}")
        print()

        if len(candidates) == 1:
            mnemonic = incomplete_phrase + " " + candidates[0]
            print("✅ Única palabra encontrada. Continuando...\n")
        else:
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
                    print("\n⚠️  Modo no interactivo detectado. Usando la primera palabra.")
                    print("⚠️  DEBES verificar manualmente cuál es la palabra correcta.\n")
                    mnemonic = incomplete_phrase + " " + candidates[0]
                    break

        recovered = mnemonic_to_entropy(mnemonic)
        return recovered["entropy"], mnemonic, recovered, "mnemonic_incomplete"

    entropy = generate_entropy(args.words)
    mnemonic = entropy_to_mnemonic(entropy)

    # Reintentar si salen palabras repetidas en la generación
    max_attempts = 1000
    if len(set(mnemonic.split())) != len(mnemonic.split()):
        mnemo = Mnemonic("english")
        for attempt in range(max_attempts):
            entropy = generate_entropy(args.words)
            mnemonic = entropy_to_mnemonic(entropy)
            if len(set(mnemonic.split())) == len(mnemonic.split()):
                if attempt > 0:
                    print(f"✅ Mnemonic sin repeticiones generada en {attempt + 1} intento(s)")
                break
        else:
            print(f"⚠️  ADVERTENCIA: No se pudo generar mnemonic sin repeticiones en {max_attempts} intentos.")
            print("   Usando la última generación (puede tener repeticiones).")

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

    bip32_master, bip32_chain_code = bip32_master_key(seed)
    bip32_root_key = bip32_master + bip32_chain_code

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
        "bip32_root_key": bip32_root_key,
        "bip32_master_key": bip32_master,
        "bip32_chain_code": bip32_chain_code,
        "derivations": derivations,
        "gap_limit": GAP_LIMIT,
    }

    seguridad = analizar_seguridad_mnemonic(mnemonic)
    context["seguridad_mnemonic"] = seguridad

    if args.audit_passphrase:
        context["passphrase_audit"] = audit_passphrase(args.passphrase)

    return context


def format_report(data, terminal_mode=True, hide_sensitive=True, show_all=False):
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
        lines.extend([
            f"Entropy bits    : {data['entropy_bits']}",
            f"Entropy binary  : {data['entropy_bin']}",
            f"Entropy hex     : {data['entropy_hex']}",
            f"Checksum BIP39  : {data['entropy_checksum']}",
            f"Checksum valid  : {data['checksum_valid']}",
        ])
    else:
        lines.extend([
            "Entropy bits    : [OCULTO - ver archivo desencriptado]",
            "Entropy binary  : [OCULTO - ver archivo desencriptado]",
            "Entropy hex     : [OCULTO - ver archivo desencriptado]",
            "Checksum BIP39  : [OCULTO - ver archivo desencriptado]",
            "Checksum valid  : [OCULTO - ver archivo desencriptado]",
        ])

    if "seguridad_mnemonic" in data:
        seg = data["seguridad_mnemonic"]
        lines.extend([
            "----------------------------------------",
            "ANÁLISIS DE SEGURIDAD MNEMONIC",
            "----------------------------------------",
            f"Score             : {seg['score']}/100",
            f"Clasificación     : {seg['clasificacion']}",
            f"Palabras únicas   : {seg['palabras_unicas']}/{seg['palabras']}",
            f"Ratio unicidad    : {seg['ratio_unicidad']}",
            f"Entropía Shannon : {seg['entropia_shannon']}",
            f"Ratio entropía    : {seg['ratio_entropia']}",
            f"Secuencias        : {seg['secuencias_detectadas']}",
            f"Palabras repetidas  : {seg['palabras_repetidas_total']} ({seg['palabras_con_repetidos']} palabras con repeticiones)",
            f"Porcentaje repet. : {seg['porcentaje_repeticion']}",
            f"Alerta manipulación: {seg['alerta_manipulacion']}",
            f"  → {seg['mensaje_manipulacion']}",
            f"Recomendación     : {seg['recomendacion']}",
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
        address_type = item.get("address_type", "")
        display_name = f"[{name}] ({address_type})" if address_type else f"[{name}]"
        
        lines.extend([
            display_name,
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
    print(format_report(data, terminal_mode=True, hide_sensitive=not show_all, show_all=show_all))


def export_wallet(data, output_path, output_format, password):
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
    vectors = load_vectors(vectors_path)
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
            raise ValueError(f"Vector {i}: formato no soportado.")

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

    if not CRYPTO_AVAILABLE:
        print("\n❌ ERROR: La librería 'cryptography' es requerida pero no está instalada.")
        print("    Instala con: pip3 install cryptography")
        print("    El script NO puede continuar sin encriptación.\n")
        sys.exit(1)

    print("\n" + "="*60)
    print("VERIFICACIÓN DE INTEGRIDAD BIP39")
    print("="*60)
    ok_official = verify_against_bip39_official()
    if not ok_official:
        print("\n⚠️  ADVERTENCIA: Wordlist BIP39 oficial INCORRECTA")
        print("   ¡NO uses este script para generar wallets reales!\n")
        if input("¿Continuar de todos modos? (s/N): ").strip().lower() != 's':
            sys.exit(0)

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

    if args.interactive:
        print("\n🔒 MODO INTERACTIVO SEGURO")
        print("   Los datos ingresados no se mostrarán en pantalla.")
        print("   No quedarán en el historial del shell.\n")
        data = build_context(args, interactive=True)
    else:
        data = build_context(args, interactive=False)

    print_report(data, show_all=args.show_all)

    attempt_clear_history()

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
