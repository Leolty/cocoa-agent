#!/usr/bin/env python3
"""
Utility functions for in-memory decryption of encrypted task files.

This module provides functions to decrypt task.yaml.enc and test.py.enc
files directly into memory without writing plaintext to disk.
"""

import base64
import hashlib
from pathlib import Path
from typing import Optional


def derive_key(password: str, length: int) -> bytes:
    """Derive a fixed-length key from the password using SHA256."""
    hasher = hashlib.sha256()
    hasher.update(password.encode())
    key = hasher.digest()
    return key * (length // len(key)) + key[: length % len(key)]


def decrypt(ciphertext_b64: str, password: str) -> str:
    """Decrypt base64-encoded ciphertext with XOR.
    
    Args:
        ciphertext_b64: Base64-encoded encrypted content
        password: Password/canary for decryption
        
    Returns:
        Decrypted plaintext string
        
    Raises:
        ValueError: If decryption fails (invalid base64, decode error, etc.)
    """
    try:
        encrypted = base64.b64decode(ciphertext_b64)
    except Exception as e:
        raise ValueError(f"Failed to decode base64: {str(e)}")
    
    key = derive_key(password, len(encrypted))
    decrypted = bytes(a ^ b for a, b in zip(encrypted, key))
    
    try:
        return decrypted.decode('utf-8')
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to decode decrypted content as UTF-8: {str(e)}")


def decrypt_file_to_memory(encrypted_file_path: Path, canary: str) -> str:
    """Decrypt an encrypted file directly to memory without writing to disk.
    
    Args:
        encrypted_file_path: Path to the .enc file
        canary: Decryption key (canary)
        
    Returns:
        Decrypted content as string
        
    Raises:
        FileNotFoundError: If the encrypted file doesn't exist
        ValueError: If decryption fails
    """
    if not encrypted_file_path.exists():
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_file_path}")
    
    try:
        with open(encrypted_file_path, 'r', encoding='utf-8') as f:
            encrypted_content = f.read().strip()
    except IOError as e:
        raise ValueError(f"Failed to read encrypted file {encrypted_file_path}: {str(e)}")
    
    if not encrypted_content:
        raise ValueError(f"Encrypted file {encrypted_file_path} is empty")
    
    try:
        decrypted_content = decrypt(encrypted_content, canary)
        return decrypted_content
    except ValueError as e:
        raise ValueError(f"Failed to decrypt {encrypted_file_path}: {str(e)}")


def read_canary(task_dir: Path) -> Optional[str]:
    """Read canary from canary.txt file.
    
    Args:
        task_dir: Path to task directory
        
    Returns:
        Canary string, or None if file doesn't exist
        
    Raises:
        ValueError: If canary file exists but cannot be read or is empty
    """
    canary_file = task_dir / "canary.txt"
    if not canary_file.exists():
        return None
    
    try:
        with open(canary_file, 'r', encoding='utf-8') as f:
            canary = f.read().strip()
        
        if not canary:
            raise ValueError(f"Canary file {canary_file} is empty")
        
        return canary
    except IOError as e:
        raise ValueError(f"Failed to read canary file {canary_file}: {str(e)}")

