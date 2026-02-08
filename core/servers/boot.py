#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from result import Result, Ok, Err
from typing import Dict, Any
from core.reflect.model import TortoiseIrModelDataReflect

logger = logging.getLogger(__name__)


async def assign_default_groups_to_users() -> Result[Dict[str, Any], Exception]:
    """
    检查所有用户是否拥有默认用户组，没有则添加
    :return: 成功处理的统计信息
    """
    try:
        # 1. 获取默认用户组
        default_groups_res = await TortoiseIrModelDataReflect.get(
            "groups",
            {"default": True}
        )
        if not default_groups_res.is_ok():
            return Err(default_groups_res.err_value)
        default_groups = default_groups_res.ok_value
        if not default_groups:
            return Ok({
                "message": "没有找到默认用户组",
                "total_users": 0,
                "users_assigned": 0,
                "default_groups": []
            })
        # 2. 获取所有激活的用户
        users_res = await TortoiseIrModelDataReflect.get(
            "users",
            {"active": True}
        )
        if not users_res.is_ok():
            return Err(users_res.err_value)
        users = users_res.ok_value
        if not users:
            return Ok({
                "message": "没有找到激活的用户",
                "total_users": 0,
                "users_assigned": 0,
                "default_groups": []
            })
        # 3. 为每个用户检查并添加默认用户组
        users_assigned = 0
        users_skipped = 0
        group_ids = [group.id for group in default_groups]
        for user in users:
            # 检查用户当前已有的组
            user_groups_res = await TortoiseIrModelDataReflect.get_model("users")
            if user_groups_res.is_ok():
                if hasattr(user, 'groups'):
                    current_groups = await user.groups.all()
                    current_group_ids = [group.id for group in current_groups]
                    # 找出用户没有的默认组
                    groups_to_add = [
                        group_id for group_id in group_ids
                        if group_id not in current_group_ids
                    ]
                    # 如果有需要添加的组
                    if groups_to_add:
                        # 使用 many2many 方法添加关系
                        add_res = await TortoiseIrModelDataReflect.many2many(
                            user,
                            {"groups": groups_to_add}
                        )

                        if add_res.is_ok():
                            users_assigned += 1
                        else:
                            print(f"为用户 {user.id} 添加默认组失败: {add_res.err_value}")
                            users_skipped += 1
                    else:
                        users_skipped += 1
                else:
                    # 如果用户模型没有 groups 字段，尝试直接添加
                    add_res = await TortoiseIrModelDataReflect.many2many(
                        user,
                        {"groups": group_ids}
                    )
                    if add_res.is_ok():
                        users_assigned += 1
                    else:
                        logger.info(f"为用户 {user.id} 添加默认组失败: {add_res.err_value}")
                        users_skipped += 1
            else:
                users_skipped += 1
        # 4. 返回处理结果
        return Ok({
            "message": "默认用户组分配完成",
            "total_users": len(users),
            "users_assigned": users_assigned,
            "users_skipped": users_skipped,
            "default_groups": [group.name for group in default_groups],
            "default_group_ids": group_ids
        })
    except Exception as exc:
        return Err(exc)


async def boot(srv, loop):
    from core.servers.parse2xml import Parse2XML
    from conf.settings import BASE_DIR, INSTALL_APPS
    parse = Parse2XML()

    for app_name in INSTALL_APPS:
        try:
            app_path = BASE_DIR / app_name.replace('.', '/')
            manifest_path = app_path / 'manifest.json'
            if not manifest_path.exists():
                logger.warning(f"Manifest file not found for app {app_name}: {manifest_path}")
                continue
            await parse.parse(app_name.split('.')[-1], manifest_path)
        except Exception as exc:
            logger.error(f"Error processing app {app_name}: {str(exc)}")
    # 为所有用户分配默认用户组
    t = await assign_default_groups_to_users()
    if t.is_ok():
        logger.info(t.ok_value)
    else:
        logger.error(t.err_value)
    logger.info("All apps initialized successfully")
