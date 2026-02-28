#!/usr/bin/env python
# -*- coding: utf-8 -*-

from result import Result, Ok, Err
from typing import Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


def get_llm(
        t: str,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        streaming: bool = False
) -> Result[Union[ChatOpenAI, ChatOllama], Exception]:
    """获取llm"""
    match t:
        case 'openai':
            return Ok(ChatOpenAI(
                model=model,
                base_url=base_url,
                api_key=api_key,
                temperature=temperature,
                streaming=streaming
            ))
        case 'ollama':
            return Ok(ChatOllama(
                model=model,
                base_url=base_url,
                temperature=temperature,
                streaming=streaming
            ))
        case _:
            return Err(ValueError(f'Invalid input: {t}'))
