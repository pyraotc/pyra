#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tortoise import Tortoise
from tortoise.models import Model
from typing import Type, Dict, Any, List, Optional
from result import Result, Ok, Err


class TortoiseReflect(object):
    _models_cache = None

    @classmethod
    async def models_cache(cls) -> Result[Dict[str, Type[Model]], Exception]:
        """
        获取并缓存模型: {模型名称(表名): 模型对象}
        :return:
        """
        if cls._models_cache is None:
            try:
                cls._models_cache = {}
                apps = Tortoise.apps
                for app_name, models in apps.items():
                    for model_name, model_class in models.items():
                        # 使用 describe_model 方法获取模型元数据
                        table_name = model_class.describe()["table"]
                        cls._models_cache[table_name] = model_class
                        # 同时存储小写版本以便不区分大小写查找
                        cls._models_cache[model_name.lower()] = model_class
            except Exception as exc:
                return Err(exc)
        return Ok(cls._models_cache)

    @classmethod
    async def get_model(cls, identifier: str) -> Result[Type[Model], Exception]:
        """根据表名或模型名获取模型类型"""
        model_cache_result = await cls.models_cache()
        if not model_cache_result.is_ok():
            return Err(model_cache_result.err_value)
        try:
            model_cache = model_cache_result.ok_value
            # 直接匹配
            if identifier in model_cache:
                return Ok(model_cache[identifier])
            # 小写匹配
            if identifier.lower() in model_cache:
                return Ok(model_cache[identifier.lower()])
            return Err(ValueError(f"Model '{identifier}' not found. Available"))
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def create(cls, table_name: str, data: Dict[str, Any]) -> Result[Model, Exception]:
        """创建记录"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                val = await model_cls.create(**data)
                return Ok(val)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def update(cls, table_name: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Result[int, Exception]:
        """更新记录"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                n = await model_cls.filter(**filters).update(**data)
                return Ok(n)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def delete(cls, table_name: str, filters: Dict[str, Any]) -> Result[int, Exception]:
        """删除记录"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                val = await model_cls.filter(**filters).delete()
                return Ok(val)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def get(cls, table_name: str, filters: Dict[str, Any] = None) -> Result[List[Model], Exception]:
        """查询记录"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                query = model_cls.all()
                if filters:
                    query = query.filter(**filters)
                return Ok(await query)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def get_first(cls, table_name: str, filters: Dict[str, Any] = None) -> Result[Optional[Model], Exception]:
        """获取第一条记录"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                # 构建查询
                if filters is not None:
                    record = await model_cls.filter(**filters).first()
                else:
                    record = await model_cls.all().first()
                return Ok(record)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    @classmethod
    async def count(cls, table_name: str, filters: Dict[str, Any] = None) -> Result[int, Exception]:
        """获取count"""
        try:
            model_cls_result = await cls.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                query = model_cls.all()
                if filters:
                    query = query.filter(**filters)
                count = await query.count()
                return Ok(count)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)


class TortoiseIrModelDataReflect(TortoiseReflect):

    @classmethod
    async def ref_id(cls, xml_id) -> Result[Optional[int], Exception]:
        """根据xml_id获取记录的id"""
        try:
            record_result = await cls.get_first("ir_model_data", {"complete_name": xml_id})
            if record_result.is_ok():
                record = record_result.ok_value
                if record is not None:
                    ref_id = record.ref_id
                    return Ok(ref_id)
                return Ok(None)
            return Err(record_result.err_value)
        except Exception as exc:
            return Err(exc)

    @staticmethod
    async def many2many(instance, data: Dict[str, List[int]]) -> Result[bool, Exception]:
        """添加多对多关联关系"""
        for field_name, related_ids in data.items():
            try:
                # 检查记录实例是否有这个多对多字段
                if hasattr(instance, field_name):
                    # 获取多对多 管理器
                    many2many_manager = getattr(instance, field_name)
                    # 获取对应的模型类
                    related_model = many2many_manager.remote_model
                    # 查询相关的记录
                    related_objects = []
                    for rel_id in related_ids:
                        related_obj = await related_model.filter(id=rel_id).first()
                        if related_obj:
                            related_objects.append(related_obj)
                    if related_objects:
                        # 添加多对多关系
                        await many2many_manager.add(*related_objects)
                return Ok(True)
            except Exception as exc:
                return Err(exc)
