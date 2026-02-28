#!/usr/bin/env python
# -*- coding: utf-8 -*-

# SKILL
# from core.ai.skills import Skill
#
# if __name__ == '__main__':
#     skill = Skill('skills')
#     skill.load_skills()
#
#     # 打印所有技能的描述
#     for skill_name, skill_info in skill.skills.items():
#         print(f"Skill: {skill_name}")
#         print(f"Path: {skill_info['path']}")
#         print(f"Description: {skill_info['description']}")
#         print("-" * 50)
#
#     # 获取某个具体的skill
#     info = skill.read_skills("email").unwrap()
#     print(info)
#
#     # 执行skill提供的脚本或者方法
#     res = skill.call_skill_function("email", "hello", "张三").unwrap()
#     print(f"Skill function call: {res}")
