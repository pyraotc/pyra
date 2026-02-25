#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional
from result import Result, Ok, Err
import yaml


class YamlLoader(object):
    _data = None

    @classmethod
    def open(cls, file_path: str) -> Result['YamlLoader', Exception]:
        try:
            with open(file_path, "r", encoding='utf-8') as f:
                cls._data = yaml.safe_load(f) or {}
            return Ok(cls())
        except yaml.YAMLError as exc:
            return Err(exc)
        except Exception as exc:
            return Err(exc)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._data.copy() if self._data else {}

    def get_str(self, key: str, default: Optional[str] = None) -> str:
        value = self.get(key, default)
        return str(value) if value is not None else default

    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """获取整型配置值"""
        value = self.get(key, default)
        return int(value) if value is not None else default

    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """获取浮点型配置值"""
        value = self.get(key, default)
        return float(value) if value is not None else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔型配置值"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1', 'on')
        return bool(value)

    def get_list(self, key: str, default: list = None) -> list:
        """获取列表配置值"""
        if default is None:
            default = []
        value = self.get(key, default)
        return list(value) if value is not None else default

    def get_dict(self, key: str, default: dict = None) -> dict:
        """获取字典配置值"""
        if default is None:
            default = {}
        value = self.get(key, default)
        return dict(value) if value is not None else default

    def has_key(self, key: str) -> bool:
        """检查配置键是否存在"""
        return self.get(key, None) is not None

    def glob(self):
        global settings
        settings = self


settings: Optional[YamlLoader] = None
