#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import importlib
from typing import Dict, Any
from result import Result, Ok, Err

logger = logging.getLogger(__name__)


class Skill:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, dict] = {}  # {skill_name: {description, module}}

    @staticmethod
    def extract_md_header_line_by_line(file_path) -> Result[str, Exception]:
        """
        逐行读取文件，适合大文件
        """
        header_lines = []
        in_header = False
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file):
                    stripped_line = line.strip()
                    # 检测头部开始
                    if not in_header and stripped_line == '---':
                        in_header = True
                        continue
                    # 检测头部结束
                    if in_header and stripped_line == '---':
                        return Ok('\n'.join(header_lines))
                    # 收集头部内容
                    if in_header:
                        header_lines.append(line.rstrip())
            return Err(ValueError('The skill head description is empty.'))
        except Exception as exc:
            return Err(exc)

    @staticmethod
    def _import_skill_module(skill_name: str):
        """动态导入技能模块"""
        module_name = f"skills.{skill_name}"
        return importlib.import_module(module_name)

    def load_skills(self) -> Result[bool, Exception]:
        """Load all skills from skills directory"""
        try:
            for skill_name in os.listdir(self.skills_dir):
                skill_path = os.path.join(self.skills_dir, skill_name)
                if os.path.isdir(skill_path) and "__init__.py" in os.listdir(skill_path) and os.path.exists(
                        os.path.join(skill_path, "SKILL.md")):
                    # 读取SKILL.md描述文件
                    header = self.extract_md_header_line_by_line(os.path.join(skill_path, "SKILL.md"))
                    if not header.is_ok():
                        logger.error(f"Skill {skill_name} failed to load. -> {str(header.err_value)}")
                        continue
                    skill_desc = header.ok_value
                    if skill_desc:
                        self.skills[skill_name] = {
                            "path": skill_path,
                            "description": skill_desc,
                            "module": self._import_skill_module(skill_name)
                        }
            return Ok(True)
        except Exception as exc:
            return Err(exc)

    def read_skills(self, name: str) -> Result[str, Exception]:
        """获取指定的skills"""
        try:
            # 先获取skill所在的位置
            skill = self.skills.get(name, None)
            if not skill or not skill.get("path", None):
                return Err(ValueError(f"Skill {name} not found."))
            # 读取完整的skill
            print(skill.get("path"))
            with open(os.path.join(skill.get("path"), "SKILL.md"), 'r', encoding='utf-8') as file:
                content = file.read()
            return Ok(content)
        except Exception as exc:
            return Err(exc)

    def execute_skill(self, name: str, method_name: str, *args, **kwargs) -> Result[Any, Exception]:
        """
        :param name: skill名称
        :param method_name: 执行的方法
        :param args: 元组参数
        :param kwargs: 字典参数
        :return:
        """
        try:
            skill = self.skills.get(name)
            if not skill:
                return Err(ValueError(f"Skill {name} not found."))

            # 获取skill模块
            module = skill.get("module")
            if not module:
                return Err(ValueError(f"Module for skill {name} not found."))

            # 检查方法是否存在
            if not hasattr(module, method_name):
                return Err(ValueError(f"Method for skill {name} not found."))

            # 获取方法并执行
            method = getattr(module, method_name)
            result = method(*args, **kwargs)
            return Ok(result)
        except Exception as exc:
            return Err(exc)

    def execute_skill_method(self,
                             skill_name: str,
                             class_name: str = None,
                             method_name: str = None,
                             instance_method: bool = False,
                             *args, **kwargs
                             ) -> Result[Any, Exception]:
        """
        :param skill_name: skill 名称
        :param class_name: 类名（如果模块中定义的是类）
        :param method_name: 要执行的方法名
        :param instance_method: 是否为实例方法（需要先创建实例）
        :param args: 传递给方法的参数
        :param kwargs:
        :return:
        """
        try:
            skill = self.skills.get(skill_name)
            if not skill:
                return Err(ValueError(f"Skill {skill_name} not found."))

            module = skill.get("module")
            if not module:
                return Err(ValueError(f"Module for skill {skill_name} not found."))

            # 如果指定了类名
            if class_name:
                if not hasattr(module, class_name):
                    return Err(ValueError(f"Class {class_name} not found in skill {skill_name}."))

                cls = getattr(module, class_name)

                if instance_method:
                    # 实例方法：创建实例然后调用方法
                    instance = cls()
                    if not hasattr(instance, method_name):
                        return Err(ValueError(f"Method {method_name} not found in class {class_name}."))
                    method = getattr(instance, method_name)
                else:
                    # 类方法
                    if not hasattr(cls, method_name):
                        return Err(ValueError(f"Class method {method_name} not found in class {class_name}."))
                    method = getattr(cls, method_name)
            else:
                # 直接调用模块函数
                if not hasattr(module, method_name):
                    return Err(ValueError(f"Function {method_name} not found in skill {skill_name}."))
                method = getattr(module, method_name)

            result = method(*args, **kwargs)
            return Ok(result)
        except Exception as exc:
            return Err(exc)

    def call_skill_function(self, skill_name: str, func_name: str, *args, **kwargs) -> Result[Any, Exception]:
        """快捷调用 skill 中的函数"""
        return self.execute_skill(skill_name, func_name, *args, **kwargs)

    def call_skill_class_method(self, skill_name: str, class_name: str,
                                method_name: str, *args, **kwargs) -> Result[Any, Exception]:
        """调用 skill 中的类方法"""
        return self.execute_skill_method(skill_name, class_name, method_name,
                                         instance_method=False, *args, **kwargs)

    def call_skill_instance_method(self, skill_name: str, class_name: str,
                                   method_name: str, *args, **kwargs) -> Result[Any, Exception]:
        """调用 skill 中的实例方法"""
        return self.execute_skill_method(skill_name, class_name, method_name,
                                         instance_method=True, *args, **kwargs)
