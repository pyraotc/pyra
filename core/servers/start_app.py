#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import os.path as osp
from result import Result, Ok, Err

logger = logging.getLogger(__name__)

t1 = f"""#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

t2 = """{
  "name": "%s",
  "version": "1.0.0"
}
"""

t3 = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from tortoise import models, fields
"""


def create_app(name: str) -> Result[bool, Exception]:
    try:
        logger.info(f'Creating app {name}!')
        base_dir = f"apps/{name}"

        if osp.exists(base_dir):
            logger.info(f'App {name} already exists!')
            return Ok(True)
        # 创建应用目录
        os.makedirs(base_dir, exist_ok=True)

        # 创建 __init__.py包文件
        init_file = osp.join(base_dir, "__init__.py")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(t1)
            logger.info(f'{base_dir}/__init__.py created!')
        # 创建manifest.json文件
        manifest_json_file = osp.join(base_dir, "manifest.json")
        with open(manifest_json_file, "w", encoding="utf-8") as f:
            f.write(t2 % name)
            logger.info(f'{base_dir}/manifest.json created!')
        # 创建子目录
        subdirs = ["models", "serialize", "views", "tasks"]
        for subdir in subdirs:
            subdir_path = osp.join(base_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)
            logger.info(f' {subdir_path} created!')

            # 为每个子目录创建 __init__.py 文件
            init_file = osp.join(subdir_path, "__init__.py")
            if subdir == "models":
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(t3)
            else:
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write(t1)
        # 创建静态目录
        statics = ['data', 'templates', 'static']
        for static in statics:
            subdir_path = osp.join(base_dir, static)
            os.makedirs(subdir_path, exist_ok=True)
            logger.info(f' {subdir_path} created!')
        logger.info(f"App {name} create successfully!")
        return Ok(True)
    except Exception as exc:
        return Err(exc)
