#!/usr/bin/env python
# -*- coding: utf-8 -*-

from core.reflect.db import TortoiseIrModelDataReflect
import logging
import json
import os
import bcrypt
import hashlib
import base64
import random
import string
import xml.etree.ElementTree as ET

from result import Result, Ok, Err
from typing import Any, Optional, Dict, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Record(BaseModel):
    id: Optional[str] = None
    model: Optional[str] = None
    noupdate: bool = False
    fields: Optional[Dict] = None
    many2many: Optional[Dict[str, List[str]]] = None

    class Config:
        extra = 'allow'


def recover2img(path: str) -> str | None:
    """将图片转换为base64编码"""
    try:
        with open(path, "rb") as image_file:
            # 读取图片二进制数据
            image_data = image_file.read()
            # 转换为base64编码
            base64_str = base64.b64encode(image_data).decode('utf-8')
            return base64_str
    except Exception as exc:
        logger.error(exc)
        return None


def safe_eval(code_string, context=None):
    """安全地执行代码字符串"""
    """安全地执行代码字符串"""
    if context is None:
        context = {}

    # 添加一些常用的模块到上下文
    safe_context = {
        'bcrypt': bcrypt,
        'hashlib': hashlib,
        'base64': base64,
        'random': random,
        'string': string,
        'recover2img': recover2img,
        '__builtins__': {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'len': len,
            'range': range,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            '__import__': __import__,
        }
    }
    safe_context.update(context)

    try:
        # 对于多行代码，使用exec并在最后设置result
        if '\n' in code_string or code_string.strip().startswith(
                ('import ', 'def ', 'class ', 'for ', 'while ', 'if ')):
            # 创建完整的可执行代码
            lines = code_string.strip().split('\n')
            last_line = lines[-1].strip()

            # 检查最后一行是否是表达式（不是语句）
            if not last_line.startswith((' ', '\t', 'def ', 'class ', 'for ', 'while ', 'if ', 'import ', 'from ')):
                # 最后一行是表达式，将其结果赋给result
                exec_code = '\n'.join(lines[:-1]) + f'\nresult = {last_line}'
            else:
                # 最后一行是语句，直接执行并设置result为None
                exec_code = code_string + '\nresult = None'
            exec(exec_code, safe_context)
            return safe_context.get('result')
        else:
            # 单行表达式，使用eval
            return eval(code_string, safe_context)
    except Exception as exc:
        logger.error(f"Error in safe_eval: {exc}")
        return None


class Parse2XML(TortoiseIrModelDataReflect):
    def __init__(self):
        super(Parse2XML, self).__init__()

    @staticmethod
    async def parse_element_tag2record(element: Any) -> Result[Record, Exception]:
        """解析record元素"""
        try:
            r = Record(
                id=element.get('id'),
                model=element.get("model"),
                noupdate=False if element.get("noupdate") is None else True if element.get(
                    "noupdate") == '1' else False,
                fields={},
                many2many={}
            )

            for field in element:
                field_name = field.get('name')
                if not field_name:
                    continue
                field_value = field.text.strip() if field.text else ""
                # 处理eval表达式（多对多关系）- 第一阶段只解析，不解析引用
                if field.get("eval"):
                    try:
                        eval_str = field.get("eval")
                        evals = eval(eval_str) if eval_str else []
                        refs = []
                        for val in evals:
                            if val[0] == 4:  # 4表示添加关联
                                # 第一阶段只存储xml_id，不解析引用
                                refs.append(val[1])
                        if refs:
                            r.many2many[field_name] = refs
                    except Exception as exc:
                        logger.error(f"Error parsing eval for field {field_name}: {exc}")
                        return Err(exc)
                # 处理外键引用 - 第一阶段只存储引用ID，不解析
                elif field.get('ref'):
                    ref_id = field.get('ref')
                    r.fields[f"{field_name}_xml_ref"] = ref_id
                elif field_value.startswith('eval("""') and field_value.endswith('""")'):
                    # 提取eval内部的代码
                    eval_code = field_value[8:-4]  # 移除 eval(""" 和 """)
                    # 清理代码：移除多余的空格和换行
                    eval_code = eval_code.strip()
                    try:
                        # 使用安全的eval函数
                        result = safe_eval(eval_code)
                        if result is not None:
                            r.fields[field_name] = result
                        else:
                            return Err(ValueError(f"Eval execution returned None for field {field_name}"))
                    except Exception as exc:
                        logger.error(f"Error in eval for field {field_name}: {exc}")
                        return Err(exc)
                # 处理普通值
                else:
                    try:
                        if field_value.lower() in ('true', 'false'):
                            r.fields[field_name] = field_value.lower() == 'true'
                        elif field_value.isdigit():
                            r.fields[field_name] = int(field_value)
                        else:
                            r.fields[field_name] = field_value
                    except Exception as exc:
                        logger.error(f"Error parsing field {field_name}: {exc}")
                        r.fields[field_name] = field_value  # 保持原始值
            return Ok(r)
        except Exception as exc:
            logger.error(f"Error parsing record element: {exc}")
            return Err(exc)

    async def get_xml_with_record(self, xml_content: str) -> Result[List[Record], Exception]:
        """解析xml生成记录集，按照顺序放入列表"""
        try:
            root = ET.fromstring(xml_content)
            records = []
            for element in root:
                if element.tag == "record":
                    res = await self.parse_element_tag2record(element)
                    if res.is_ok():
                        records.append(res.unwrap())
                    else:
                        logger.error(f"Failed to parse record: {res.unwrap_err()}")
                        return Err(res.unwrap_err())
                else:
                    logger.warning(f"Unknown element tag: {element.tag}")
                    continue
            return Ok(records)
        except ET.ParseError as exc:
            logger.error(f"XML parsing error: {exc}")
            return Err(exc)
        except Exception as exc:
            logger.error(f"Unexpected error in get_xml_with_record: {exc}")
            return Err(exc)

    async def resolve_references(self, record: Record) -> Result[Record, Exception]:
        """解析记录中的引用关系"""
        try:
            resolved_record = Record(
                id=record.id,
                model=record.model,
                noupdate=False,
                fields=record.fields.copy() if record.fields else {},
                many2many={}
            )
            # 解析字段中的引用 - 使用列表收集要处理的引用字段
            ref_fields_to_process = []
            for field_name, field_value in resolved_record.fields.items():
                if field_name.endswith('_xml_ref'):
                    base_field_name = field_name.replace('_xml_ref', '')
                    ref_fields_to_process.append((field_name, base_field_name, field_value))

            # 处理引用字段
            for field_name, base_field_name, ref_id in ref_fields_to_process:
                # 查找引用的数据库ID
                referenced_id = await self.ref_id(ref_id)
                if referenced_id.is_ok():
                    if referenced_id.ok_value is not None:
                        resolved_record.fields[f"{base_field_name}_id"] = referenced_id.ok_value
                        # 从字段中移除临时的引用字段
                        del resolved_record.fields[field_name]
                    else:
                        return Err(ValueError(f"Referenced record {ref_id} not found"))
                else:
                    return Err(referenced_id.err_value)

            # 解析多对多关系中的引用
            if record.many2many:
                for field_name, xml_ids in record.many2many.items():
                    db_ids = []
                    for xml_id in xml_ids:
                        referenced_id = await self.ref_id(xml_id)
                        if referenced_id.is_ok():
                            if referenced_id.unwrap() is not None:
                                db_ids.append(referenced_id.unwrap())
                            else:
                                return Err(ValueError(f"Referenced record {xml_id} not found"))
                        else:
                            return Err(referenced_id.unwrap_err())
                    resolved_record.many2many[field_name] = db_ids
            return Ok(resolved_record)
        except Exception as exc:
            return Err(exc)

    async def create_record(self, module: str, record: Record) -> Result[bool, Exception]:
        """创建单个记录"""
        try:
            tmp_result = await self.get_first("ir_model_data", {"complete_name": f"{module}.{record.id}"})
            if tmp_result.is_ok():
                tmp = tmp_result.ok_value
                # 解析引用关系
                resolved_record = await self.resolve_references(record)
                if not resolved_record.is_ok():
                    return Err(resolved_record.err_value)

                if tmp is None:
                    # 创建记录
                    rd_result = await self.create(resolved_record.unwrap().model, resolved_record.unwrap().fields)
                    if not rd_result.is_ok():
                        return Err(rd_result.err_value)
                    created_record = rd_result.ok_value
                    # 处理多对多关系
                    if resolved_record.unwrap().many2many:
                        for field_name, db_ids in resolved_record.unwrap().many2many.items():
                            many2many_manager = getattr(created_record, field_name)
                            # 建立新关系
                            related_objects = []
                            for rel_id in db_ids:
                                related_model = many2many_manager.remote_model
                                related_obj = await related_model.filter(id=rel_id).first()
                                if related_obj:
                                    related_objects.append(related_obj)

                            if related_objects:
                                await many2many_manager.add(*related_objects)
                    # 写入模板记录
                    template_result = await self.create("ir_model_data", {
                        "module": module,
                        "name": record.id,
                        "complete_name": f"{module}.{record.id}",
                        "model": record.model,
                        "ref_id": created_record.id,
                        "noupdate": record.noupdate
                    })
                    if not template_result.is_ok():
                        return Err(template_result.unwrap_err())
                    logger.info(f"Successfully created record {record.id} with ID {created_record.id}")
                    return Ok(True)
                else:
                    if record.noupdate:
                        # 更新记录
                        resolved_record = await self.resolve_references(record)  # 解析引用关系
                        if not resolved_record.is_ok():
                            return Err(resolved_record.err_value)
                        # 更新主记录
                        update_result = await self.update(
                            resolved_record.unwrap().model,
                            {"id": tmp.ref_id},
                            resolved_record.unwrap().fields
                        )
                        if not update_result.is_ok():
                            return Err(update_result.err_value)
                        updated_record_id = tmp.ref_id
                        # 处理多对多关系更新
                        if resolved_record.unwrap().many2many:
                            # 获取目标记录实例
                            model_result = await self.get_model(record.model)
                            if model_result.is_ok():
                                target_record = await model_result.ok_value.filter(id=updated_record_id).first()
                                if target_record:
                                    for field_name, db_ids in resolved_record.unwrap().many2many.items():
                                        if hasattr(target_record, field_name):
                                            many2many_manager = getattr(target_record, field_name)
                                            # 清除现有关系
                                            await many2many_manager.clear()
                                            # 建立新关系
                                            related_objects = []
                                            for rel_id in db_ids:
                                                related_model = many2many_manager.remote_model
                                                related_obj = await related_model.filter(id=rel_id).first()
                                                if related_obj:
                                                    related_objects.append(related_obj)

                                            if related_objects:
                                                await many2many_manager.add(*related_objects)
                        # 更新记录时间戳
                        await self.update(
                            "ir_model_data",
                            {"id": tmp.id},
                            {"write_date": "now()"}
                        )
                        logger.info(f"Updated record {record.id} (ID: {updated_record_id})")
                return Ok(True)
            return Err(tmp_result.err_value)
        except Exception as exc:
            return Err(exc)

    async def parse(self, module: str, path: str) -> Result[bool, Exception]:
        """"""
        from rcc.config import BASE_DIR
        try:
            with open(path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            data_files = manifest_data.get('data', [])
            for data_file in data_files:
                normalized_data_path = os.path.normpath(data_file.replace('/', os.sep))
                full_data_path = os.path.join(BASE_DIR, 'apps', module, normalized_data_path)
                try:
                    with open(full_data_path, 'r', encoding="utf-8") as file:
                        # 第一阶段：解析所有记录到内存
                        records_result = await self.get_xml_with_record(file.read())
                        if not records_result.is_ok():
                            logger.error(records_result.err_value)
                            continue
                        records = records_result.ok_value
                        # 第二阶段：按顺序创建记录
                        for record in records:
                            try:
                                res = await self.create_record(module, record)
                                if res.is_ok():
                                    logger.info(f"Successfully load record {module}.{record.id}")
                                else:
                                    logger.error(f"Failed to load record {module}.{record.id}: {res.err_value}")
                                    continue
                            except Exception as exc:
                                logger.error(f"Error processing record {record.id}: {exc}")
                                continue
                    logger.info(f"Successfully processed {len(records)} records")
                except Exception as exc:
                    logger.error(f"Failed to parse record: {exc}")
                    continue
            return Ok(True)
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in manifest for app {module}: {str(exc)}")
            return Err(exc)
        except Exception as exc:
            logger.error(exc)
            return Err(exc)
