#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from typing import Union, Tuple
from result import Result, Ok, Err

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey

DEFAULT_SIZE = 2048
DEFAULT_EXPONENT = 65537


def generate_keys(size: int, exponent: int) -> Result[Tuple[RSAPrivateKey, RSAPublicKey], Exception]:
    """生成RSA秘钥"""
    try:
        private_key = rsa.generate_private_key(
            public_exponent=exponent,
            key_size=size,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return Ok((private_key, public_key))
    except Exception as exc:
        return Err(exc)


def save_private_key(
        file_path: str,
        private_key: RSAPrivateKey = None,
        password: str = None) -> Result[bool, Exception]:
    """保存私钥到文件"""
    try:
        if private_key is None:
            return Err(ValueError('private_key is required'))
        encryption_algorithm = serialization.NoEncryption()
        if password:
            serialization.BestAvailableEncryption(password.encode())
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        with open(file_path, 'wb') as f:
            f.write(pem)

        return Ok(True)
    except Exception as exc:
        return Err(exc)


def save_public_key(
        file_path: str,
        public_key: RSAPublicKey = None
) -> Result[bool, Exception]:
    """保存公钥到文件"""
    try:
        if public_key is None:
            return Err(ValueError('public_key is required'))

        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        with open(file_path, 'wb') as f:
            f.write(pem)
        return Ok(True)
    except Exception as exc:
        return Err(exc)


def load_private_key(file_path: str, password: str = None) -> Result[rsa.RSAPrivateKey, Exception]:
    """从文件加载私钥"""
    try:
        with open(file_path, 'rb') as key_file:
            if password:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=password.encode(),
                    backend=default_backend()
                )
                return Ok(private_key)
            else:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
                return Ok(private_key)
    except Exception as exc:
        return Err(exc)


def load_public_key(file_path: str) -> Result[rsa.RSAPublicKey, Exception]:
    """从文件加载公钥"""
    try:
        with open(file_path, 'rb') as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
            return Ok(public_key)
    except Exception as exc:
        return Err(exc)


def encrypt(data: Union[str, bytes], public_key: rsa.RSAPublicKey = None) -> Result[bytes, Exception]:
    """
    RSA 加密
        data: 要加密的数据
        public_key: 公钥
    """
    try:
        if public_key is None:
            return Err(ValueError('public_key is required'))

        if isinstance(data, str):
            data = data.encode('utf-8')

        # RSA 加密有长度限制，需要分段加密
        max_length = (public_key.key_size // 8) - 11  # PKCS#1 v1.5 padding
        encrypted_chunks = []

        for i in range(0, len(data), max_length):
            chunk = data[i:i + max_length]
            encrypted_chunk = public_key.encrypt(
                chunk,
                padding.PKCS1v15()
            )
            encrypted_chunks.append(encrypted_chunk)

        # 将所有加密块连接起来
        return Ok(b''.join(encrypted_chunks))
    except Exception as exc:
        return Err(exc)


def decrypt(encrypted_data: bytes, private_key: rsa.RSAPrivateKey = None) -> Result[bytes, Exception]:
    """
    RSA 解密
        encrypted_data: 加密的数据
        private_key: 私钥
    """
    try:
        if private_key is None:
            return Err(ValueError('private_key is required'))

        chunk_size = private_key.key_size // 8
        decrypted_chunks = []

        for i in range(0, len(encrypted_data), chunk_size):
            chunk = encrypted_data[i:i + chunk_size]
            decrypted_chunk = private_key.decrypt(
                chunk,
                padding.PKCS1v15()
            )
            decrypted_chunks.append(decrypted_chunk)

        return Ok(b''.join(decrypted_chunks))
    except Exception as exc:
        return Err(exc)


def sign(
        data: Union[str, bytes],
        private_key: rsa.RSAPrivateKey = None,
        hash_algorithm: hashes.HashAlgorithm = hashes.SHA256()
) -> Result[bytes, Exception]:
    """
    RSA 签名
        data: 要签名的数据
        private_key: 私钥
        hash_algorithm: 哈希算法，默认 SHA256
    """
    try:
        if private_key is None:
            return Err(ValueError('private_key is required'))

        if isinstance(data, str):
            data = data.encode('utf-8')

        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hash_algorithm
        )
        return Ok(signature)
    except Exception as exc:
        return Err(exc)


def verify(
        data: Union[str, bytes],
        signature: bytes,
        public_key: rsa.RSAPublicKey = None,
        hash_algorithm: hashes.HashAlgorithm = hashes.SHA256()) -> Result[bool, Exception]:
    """
    RSA 验证签名
        data: 原始数据
        signature: 签名数据
        public_key: 公钥
        hash_algorithm: 哈希算法，默认 SHA256
    """
    if public_key is None:
        return Err(ValueError('public_key is required'))

    if isinstance(data, str):
        data = data.encode('utf-8')

    try:
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hash_algorithm),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hash_algorithm
        )
        return Ok(True)
    except Exception as exc:
        return Err(exc)


def encrypt_base64(data: Union[str, bytes], public_key: rsa.RSAPublicKey = None) -> Result[str, Exception]:
    """
    RSA 加密并返回 Base64 编码字符
        data: 要加密的数据
        public_key: 公钥
    """
    encrypted = encrypt(data, public_key)
    if encrypted.is_ok():
        return Ok(base64.b64encode(encrypted.ok_value).decode('utf-8'))
    else:
        return Err(encrypted.err_value)


def decrypt_base64(base64_data: str, private_key: rsa.RSAPrivateKey = None) -> Result[str, Exception]:
    """
    解密 Base64 编码的 RSA 加密数据
        base64_data: Base64 编码的加密数据
        private_key: 私钥
    """
    encrypted_data = base64.b64decode(base64_data)
    result = decrypt(encrypted_data, private_key)
    if result.is_ok():
        return Ok(result.ok_value.decode('utf-8'))
    else:
        return Err(result.err_value)


def sign_base64(data: Union[str, bytes], private_key: rsa.RSAPrivateKey = None,
                hash_algorithm: hashes.HashAlgorithm = hashes.SHA256()) -> Result[str, Exception]:
    """
    RSA 签名并返回 Base64 编码字符串
        data: 要签名的数据
        private_key: 私钥
        hash_algorithm: 哈希算法
    """
    signature = sign(data, private_key, hash_algorithm)
    if signature.is_ok():
        return Ok(base64.b64encode(signature.ok_value).decode('utf-8'))
    else:
        return Err(signature.err_value)


def get_public_key_pem(public_key: rsa.RSAPublicKey = None) -> Result[str, Exception]:
    """
    获取公钥 PEM 格式字符串
    """
    try:
        if public_key is None:
            return Err(ValueError('public_key is required'))

        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return Ok(pem.decode('utf-8'))
    except Exception as exc:
        return Err(exc)


def get_private_key_pem(private_key: rsa.RSAPrivateKey = None, password: str = None) -> Result[str, Exception]:
    """
    获取私钥 PEM 格式字符串

        password: 密码，可选
    """
    try:
        if private_key is None:
            return Err(ValueError('private_key is required'))

        encryption_algorithm = serialization.NoEncryption()
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())

        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )
        return Ok(pem.decode('utf-8'))
    except Exception as exc:
        return Err(exc)
