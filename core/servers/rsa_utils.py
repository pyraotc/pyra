#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os.path

from result import Result, Err, Ok

logger = logging.getLogger(__name__)


def generate_rsa_key(path: str) -> Result[bool, Exception]:
    try:
        from core.crypto.rsa import DEFAULT_EXPONENT, DEFAULT_SIZE, generate_keys, save_private_key, save_public_key
        keys_result = generate_keys(DEFAULT_SIZE, DEFAULT_EXPONENT)
        if not keys_result.is_ok():
            return Err(keys_result.err_value)
        keys = keys_result.ok_value
        save_private_key(os.path.join(path, 'private.pem'), keys[0]).unwrap()
        save_public_key(os.path.join(path, 'public.pem'), keys[1]).unwrap()
        logger.info(f"Generated RSA keys successfully -> {path}")
        return Ok(True)
    except Exception as exc:
        logger.error(exc)
        return Err(exc)
