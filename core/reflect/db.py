#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tortoise import Tortoise
from tortoise.models import Model
from typing import Type, Dict, Any, List, Optional
from sanic.request import Request
from result import Result, Ok, Err


def client_info(request: Request) -> tuple:
    """获取客户端信息"""
    # 获取IP地址（考虑代理情况）
    ip_address = request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.ip))
    if isinstance(ip_address, str) and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()

    # 获取User-Agent
    user_agent = request.headers.get('User-Agent', 'Unknown')

    return ip_address, user_agent


class TortoiseReflect(object):
    def __init__(self):
        """初始化实例，每个实例有自己的缓存"""
        self._models_cache = None

    async def models_cache(self) -> Result[Dict[str, Type[Model]], Exception]:
        """
        获取并缓存模型: {模型名称(表名): 模型对象}
        :return:
        """
        if self._models_cache is None:
            try:
                self._models_cache = {}
                apps = Tortoise.apps
                for app_name, models in apps.items():
                    for model_name, model_class in models.items():
                        # 使用 describe_model 方法获取模型元数据
                        table_name = model_class.describe()["table"]
                        self._models_cache[table_name] = model_class
                        # 同时存储小写版本以便不区分大小写查找
                        self._models_cache[model_name.lower()] = model_class
            except Exception as exc:
                return Err(exc)
        return Ok(self._models_cache)

    async def get_model(self, identifier: str) -> Result[Type[Model], Exception]:
        """根据表名或模型名获取模型类型"""
        model_cache_result = await self.models_cache()
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
            return Err(ValueError(f"Model '{identifier}' not found. Available models: {list(model_cache.keys())}"))
        except Exception as exc:
            return Err(exc)

    async def create(self, table_name: str, data: Dict[str, Any]) -> Result[Model, Exception]:
        """创建记录"""
        try:
            model_cls_result = await self.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                val = await model_cls.create(**data)
                return Ok(val)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    async def update(self, table_name: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Result[int, Exception]:
        """更新记录"""
        try:
            model_cls_result = await self.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                n = await model_cls.filter(**filters).update(**data)
                return Ok(n)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    async def delete(self, table_name: str, filters: Dict[str, Any]) -> Result[int, Exception]:
        """删除记录"""
        try:
            model_cls_result = await self.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                val = await model_cls.filter(**filters).delete()
                return Ok(val)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    async def get(self, table_name: str, filters: Dict[str, Any] = None) -> Result[List[Model], Exception]:
        """查询记录"""
        try:
            model_cls_result = await self.get_model(table_name)
            if model_cls_result.is_ok():
                model_cls = model_cls_result.ok_value
                query = model_cls.all()
                if filters:
                    query = query.filter(**filters)
                return Ok(await query)
            return Err(model_cls_result.err_value)
        except Exception as exc:
            return Err(exc)

    async def get_first(self, table_name: str, filters: Dict[str, Any] = None) -> Result[Optional[Model], Exception]:
        """获取第一条记录"""
        try:
            model_cls_result = await self.get_model(table_name)
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

    async def count(self, table_name: str, filters: Dict[str, Any] = None) -> Result[int, Exception]:
        """获取count"""
        try:
            model_cls_result = await self.get_model(table_name)
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

    async def clear_cache(self):
        """清除缓存，如果需要重新加载模型时可以调用"""
        self._models_cache = None
        return Ok(None)


class TortoiseIrModelDataReflect(TortoiseReflect):

    async def ref_id(self, xml_id) -> Result[Optional[int], Exception]:
        """根据xml_id获取记录的id"""
        try:
            record_result = await self.get_first("ir_model_data", {"complete_name": xml_id})
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

    async def batch_ref_id(self, xml_ids: List[str]) -> Result[Dict[str, Optional[int]], Exception]:
        """批量获取多个xml_id对应的记录id"""
        try:
            result = {}
            for xml_id in xml_ids:
                ref_id_result = await self.ref_id(xml_id)
                if ref_id_result.is_ok():
                    result[xml_id] = ref_id_result.ok_value
                else:
                    return Err(ref_id_result.err_value)
            return Ok(result)
        except Exception as exc:
            return Err(exc)

    async def get_record_by_xml_id(self, xml_id: str) -> Result[Optional[Model], Exception]:
        """通过xml_id获取完整的ir_model_data记录"""
        try:
            record_result = await self.get_first("ir_model_data", {"complete_name": xml_id})
            if record_result.is_ok():
                return Ok(record_result.ok_value)
            return Err(record_result.err_value)
        except Exception as exc:
            return Err(exc)


class TortoiseLoggerReflect(TortoiseReflect):
    async def write(self,
                    request: Request,
                    mode: str,
                    title: str,
                    content: str,
                    is_success: bool = True,
                    error_message: Optional[str] = None,
                    metadata: Optional[Any] = None
                    ) -> Result[bool, Exception]:
        """
        :param request: sanic request
        :param mode: 日志类型
        :param title:
        :param content:
        :param is_success:
        :param error_message:
        :param metadata:
        :return:
        """
        try:
            ip_address, user_agent = client_info(request)
            user_log_result = await self.create("ir_logger", **{
                'log_type': mode,
                'title': title,
                'content': content,
                'metadata': metadata,
                'is_success': is_success,
                'error_message': error_message,
                'ip_address': ip_address,
                'user_agent': user_agent,
            })
            if not user_log_result.is_ok():
                return Err(user_log_result.err_value)
            return Ok(True)
        except Exception as exc:
            return Err(exc)
