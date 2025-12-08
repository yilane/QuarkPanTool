# -*- coding: utf-8 -*-
"""
夸克网盘业务逻辑封装层 - 独立实现，不依赖 QuarkPanFileManager
"""
import sys
import os
import re
import time
import random
import asyncio
import httpx
from typing import Optional, Dict, List, Any

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import (
    UserInfo,
    CreateDirResponse,
    TransferInfo,
    TransferAndShareResponse,
    TaskStatusResponse,
)
from utils import get_timestamp


class QuarkService:
    """夸克网盘服务封装类 - 完全独立实现，避免依赖 QuarkPanFileManager"""

    def __init__(self, cookies: str):
        """
        初始化服务

        Args:
            cookies: Cookie 字符串
        """
        self.cookies = cookies
        self.headers: Dict[str, str] = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)'
                          ' Chrome/94.0.4606.71 Safari/537.36 Core/1.94.225.400 QQBrowser/12.2.5544.400',
            'origin': 'https://pan.quark.cn',
            'referer': 'https://pan.quark.cn/',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': self.cookies,
        }

    async def verify_cookies(self) -> UserInfo:
        """
        验证 Cookies 并获取用户信息

        Returns:
            用户信息

        Raises:
            Exception: Cookies 无效时抛出异常
        """
        params = {
            'fr': 'pc',
            'platform': 'pc',
        }

        try:
            async with httpx.AsyncClient() as client:
                timeout = httpx.Timeout(60.0, connect=60.0)
                response = await client.get(
                    'https://pan.quark.cn/account/info',
                    params=params,
                    headers=self.headers,
                    timeout=timeout
                )
                json_data = response.json()

                # 检查响应是否有效
                if json_data.get('data') and json_data['data'].get('nickname'):
                    nickname = json_data['data']['nickname']
                    return UserInfo(nickname=nickname)
                else:
                    # Cookie 无效
                    raise Exception("Cookies 无效或已过期，请检查 Cookie 是否正确")

        except httpx.TimeoutException:
            raise Exception("请求超时，请检查网络连接")
        except httpx.RequestError as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except KeyError:
            raise Exception("响应数据格式异常，Cookie 可能无效")
        except Exception as e:
            if "Cookies 无效" in str(e):
                raise
            raise Exception(f"验证 Cookie 失败: {str(e)}")

    async def create_directory(
        self,
        dir_name: str,
        parent_dir_id: str = "0"
    ) -> CreateDirResponse:
        """
        创建网盘目录（如果目录已存在，则返回已存在目录的fid）

        Args:
            dir_name: 目录名称
            parent_dir_id: 父目录 ID，默认为根目录

        Returns:
            创建结果（包含目录fid、目录名称、父目录ID）

        Raises:
            Exception: 创建失败时抛出异常（不包括同名冲突）
        """
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            '__dt': random.randint(100, 9999),
            '__t': get_timestamp(13),
        }

        json_data = {
            'pdir_fid': parent_dir_id,
            'file_name': dir_name,
            'dir_path': '',
            'dir_init_lock': False,
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(
                'https://drive-pc.quark.cn/1/clouddrive/file',
                params=params,
                json=json_data,
                headers=self.headers,
                timeout=timeout
            )
            result = response.json()
            if result.get("code") == 0:
                # 创建成功，返回新创建的目录信息
                return CreateDirResponse(
                    fid=result["data"]["fid"],
                    dir_name=dir_name,
                    parent_dir_id=parent_dir_id
                )
            elif result.get("code") == 23008:
                # 目录同名冲突，查询已存在的目录并返回其fid
                file_list_result = await self.get_sorted_file_list(
                    pdir_fid=parent_dir_id,
                    size='100'
                )

                # 在父目录下查找同名文件夹
                if file_list_result.get('data') and file_list_result['data'].get('list'):
                    for item in file_list_result['data']['list']:
                        # 匹配目录名称，且必须是文件夹类型
                        if item.get('file_name') == dir_name and item.get('dir') is True:
                            return CreateDirResponse(
                                fid=item['fid'],
                                dir_name=dir_name,
                                parent_dir_id=parent_dir_id
                            )

                # 如果没有找到对应的文件夹，抛出异常
                raise Exception(f"文件夹同名冲突但无法找到已存在的目录：{dir_name}")
            else:
                raise Exception(f"创建目录失败：{result.get('message', '未知错误')}")

    @staticmethod
    def get_pwd_id(share_url: str) -> str:
        """从分享链接中提取 pwd_id"""
        return share_url.split('?')[0].split('/s/')[-1]

    async def get_stoken(self, pwd_id: str, password: str = '') -> str:
        """获取分享链接的 stoken"""
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            '__dt': random.randint(100, 9999),
            '__t': get_timestamp(13),
        }
        api = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token"
        data = {"pwd_id": pwd_id, "passcode": password}

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(api, json=data, params=params, headers=self.headers, timeout=timeout)
            json_data = response.json()
            if json_data['status'] == 200 and json_data['data']:
                return json_data["data"]["stoken"]
            else:
                raise Exception(f"获取 stoken 失败：{json_data.get('message', '未知错误')}")

    async def get_detail(self, pwd_id: str, stoken: str, pdir_fid: str = '0'):
        """获取分享文件详情"""
        api = "https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail"
        page = 1
        file_list: List[Dict[str, Any]] = []

        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    'pr': 'ucpro',
                    'fr': 'pc',
                    'uc_param_str': '',
                    "pwd_id": pwd_id,
                    "stoken": stoken,
                    'pdir_fid': pdir_fid,
                    'force': '0',
                    "_page": str(page),
                    '_size': '50',
                    '_sort': 'file_type:asc,updated_at:desc',
                    '__dt': random.randint(200, 9999),
                    '__t': get_timestamp(13),
                }

                timeout = httpx.Timeout(60.0, connect=60.0)
                response = await client.get(api, headers=self.headers, params=params, timeout=timeout)
                json_data = response.json()

                is_owner = json_data['data']['is_owner']
                _total = json_data['metadata']['_total']
                if _total < 1:
                    return is_owner, file_list

                _size = json_data['metadata']['_size']
                _count = json_data['metadata']['_count']
                _list = json_data["data"]["list"]

                for file in _list:
                    d: Dict[str, Any] = {
                        "fid": file["fid"],
                        "file_name": file["file_name"],
                        "file_type": file["file_type"],
                        "dir": file["dir"],
                        "pdir_fid": file["pdir_fid"],
                        "include_items": file.get("include_items", ''),
                        "share_fid_token": file["share_fid_token"],
                        "status": file["status"]
                    }
                    file_list.append(d)

                if _total <= _size or _count < _size:
                    return is_owner, file_list

                page += 1

    async def get_sorted_file_list(self, pdir_fid='0', page='1', size='100', fetch_total='false', sort=''):
        """获取文件列表"""
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
            'pdir_fid': pdir_fid,
            '_page': page,
            '_size': size,
            '_fetch_total': fetch_total,
            '_fetch_sub_dirs': '1',
            '_sort': sort,
            '__dt': random.randint(100, 9999),
            '__t': get_timestamp(13),
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.get(
                'https://drive-pc.quark.cn/1/clouddrive/file/sort',
                params=params,
                headers=self.headers,
                timeout=timeout
            )
            return response.json()

    async def get_share_save_task_id(self, pwd_id: str, stoken: str, fid_list: List[str],
                                     share_fid_tokens: List[str], to_pdir_fid: str = '0') -> str:
        """获取转存任务 ID"""
        task_url = "https://drive.quark.cn/1/clouddrive/share/sharepage/save"
        params = {
            "pr": "ucpro",
            "fr": "pc",
            "uc_param_str": "",
            "__dt": random.randint(600, 9999),
            "__t": get_timestamp(13),
        }
        data = {
            "fid_list": fid_list,
            "fid_token_list": share_fid_tokens,
            "to_pdir_fid": to_pdir_fid,
            "pwd_id": pwd_id,
            "stoken": stoken,
            "pdir_fid": "0",
            "scene": "link"
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(task_url, json=data, headers=self.headers, params=params, timeout=timeout)
            json_data = response.json()
            if json_data.get('data') and json_data['data'].get('task_id'):
                return json_data['data']['task_id']
            else:
                raise Exception(f"获取转存任务 ID 失败：{json_data.get('message', '未知错误')}")

    async def submit_task(self, task_id: str, retry: int = 50):
        """提交并等待任务完成"""
        for i in range(retry):
            await asyncio.sleep(random.randint(500, 1000) / 1000)

            submit_url = (
                f"https://drive-pc.quark.cn/1/clouddrive/task?pr=ucpro&fr=pc&uc_param_str=&"
                f"task_id={task_id}&retry_index={i}&__dt=21192&__t={get_timestamp(13)}"
            )

            async with httpx.AsyncClient() as client:
                timeout = httpx.Timeout(60.0, connect=60.0)
                response = await client.get(submit_url, headers=self.headers, timeout=timeout)
                json_data = response.json()

            if json_data['message'] == 'ok':
                if json_data['data']['status'] == 2:
                    return json_data
            else:
                if json_data.get('code') == 32003:
                    raise Exception("转存失败，网盘容量不足")
                elif json_data.get('code') == 41013:
                    raise Exception("目标文件夹不存在")
                else:
                    raise Exception(f"任务失败：{json_data.get('message', '未知错误')}")

        raise Exception("任务超时")

    async def get_share_task_id(self, fid_list: List[str], file_name: str, url_type: int = 1,
                                expired_type: int = 2, password: str = '') -> str:
        """
        获取分享任务 ID

        Args:
            fid_list: 文件 ID 列表(支持单个或多个文件)
            file_name: 分享标题
            url_type: 分享类型(1=公开 2=加密)
            expired_type: 分享时长(1=永久 2=1天 3=7天 4=30天)
            password: 分享密码(加密时使用)

        Returns:
            分享任务 ID
        """
        from utils import generate_random_code

        json_data = {
            "fid_list": fid_list if isinstance(fid_list, list) else [fid_list],
            "title": file_name,
            "url_type": url_type,
            "expired_type": expired_type
        }
        if url_type == 2:
            json_data["passcode"] = password if password else generate_random_code()

        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(
                'https://drive-pc.quark.cn/1/clouddrive/share',
                params=params,
                json=json_data,
                headers=self.headers,
                timeout=timeout
            )
            result = response.json()
            if result.get('data') and result['data'].get('task_id'):
                return result['data']['task_id']
            else:
                raise Exception(f"获取分享任务 ID 失败：{result.get('message', '未知错误')}")

    async def get_share_id(self, task_id: str, retry: int = 30) -> str:
        """
        获取分享 ID（带轮询机制）

        Args:
            task_id: 分享任务 ID
            retry: 最大重试次数，默认30次

        Returns:
            分享 ID

        Raises:
            Exception: 获取失败或超时时抛出异常
        """
        for i in range(retry):
            # 等待任务处理
            await asyncio.sleep(random.randint(500, 1000) / 1000)

            params = {
                'pr': 'ucpro',
                'fr': 'pc',
                'uc_param_str': '',
                'task_id': task_id,
                'retry_index': str(i),
            }

            async with httpx.AsyncClient() as client:
                timeout = httpx.Timeout(60.0, connect=60.0)
                response = await client.get(
                    'https://drive-pc.quark.cn/1/clouddrive/task',
                    params=params,
                    headers=self.headers,
                    timeout=timeout
                )
                result = response.json()

                # 检查响应状态
                if result.get('message') == 'ok' and result.get('data'):
                    data = result['data']

                    # 检查任务状态
                    status = data.get('status')

                    # status = 2 表示任务完成
                    if status == 2 and data.get('share_id'):
                        return data['share_id']
                    # status = 1 表示任务失败
                    elif status == 1:
                        raise Exception(f"分享任务失败：{data.get('task_title', '未知错误')}")
                    # status = 0 或其他表示任务进行中，继续轮询
                else:
                    # 如果响应异常，继续重试
                    continue

        # 超过重试次数
        raise Exception(f"获取分享 ID 超时，任务可能仍在处理中（task_id: {task_id}）")

    async def submit_share(self, share_id: str) -> tuple:
        """提交分享并获取分享链接"""
        params = {
            'pr': 'ucpro',
            'fr': 'pc',
            'uc_param_str': '',
        }

        json_data = {
            'share_id': share_id,
        }

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.post(
                'https://drive-pc.quark.cn/1/clouddrive/share/password',
                params=params,
                json=json_data,
                headers=self.headers,
                timeout=timeout
            )
            result = response.json()
            if result.get('data'):
                share_url = result['data']['share_url']
                title = result['data']['title']
                if 'passcode' in result['data']:
                    share_url = share_url + f"?pwd={result['data']['passcode']}"
                return share_url, title
            else:
                raise Exception(f"提交分享失败：{result.get('message', '未知错误')}")

    async def transfer_and_share(
        self,
        share_url: str,
        save_dir_id: str = "0",
        share_expire_type: int = 2,
        share_url_type: int = 1,
        share_password: str = ""
    ) -> TransferAndShareResponse:
        """
        转存分享链接并生成新的分享链接

        Args:
            share_url: 要转存的分享链接
            save_dir_id: 保存目录 ID
            share_expire_type: 分享时长（1=永久 2=1天 3=7天 4=30天）
            share_url_type: 分享类型（1=公开 2=加密）
            share_password: 分享密码

        Returns:
            转存和分享结果

        Raises:
            Exception: 转存或分享失败时抛出异常
        """
        # 1. 解析分享链接
        pwd_id = self.get_pwd_id(share_url)
        match_password = re.search("pwd=(.*?)(?=$|&)", share_url)
        password = match_password.group(1) if match_password else ""

        if not pwd_id:
            raise Exception("分享链接格式不正确")

        # 2. 获取 stoken
        stoken = await self.get_stoken(pwd_id, password)

        # 3. 获取文件详情
        is_owner, data_list = await self.get_detail(pwd_id, stoken)

        if not data_list:
            raise Exception("分享链接中没有文件")

        if is_owner == 1:
            raise Exception("该文件已存在于您的网盘中，无需再次转存")

        # 4. 统计文件信息
        files_count = 0
        folders_count = 0
        files_list: List[str] = []
        folders_list: List[str] = []

        for data in data_list:
            if data['dir']:
                folders_count += 1
                folders_list.append(data["file_name"])
            else:
                files_count += 1
                files_list.append(data["file_name"])

        # 5. 执行转存
        fid_list = [i["fid"] for i in data_list]
        share_fid_token_list = [i["share_fid_token"] for i in data_list]

        task_id = await self.get_share_save_task_id(
            pwd_id, stoken, fid_list, share_fid_token_list, to_pdir_fid=save_dir_id
        )

        # 6. 等待转存完成
        result = await self.submit_task(task_id)
        save_dir_name = result['data']['save_as'].get('to_pdir_name', '根目录')

        # 7. 获取转存后的文件 ID 列表(分享转存的文件本身,而不是保存目录)
        # 等待一小段时间，确保文件已经出现在目录中
        await asyncio.sleep(1.0)

        # 获取保存目录下的文件列表
        try:
            json_data = await self.get_sorted_file_list(pdir_fid=save_dir_id, size='100')
        except Exception as e:
            raise Exception(f"获取目录文件列表失败：{str(e)}")

        # 检查 API 返回数据
        if not json_data.get('data'):
            raise Exception(f"目录文件列表返回数据异常：{json_data.get('message', '未知错误')}")

        if not json_data['data'].get('list'):
            # 如果目录为空或刚创建，list 可能为空，使用保存目录本身作为分享对象
            print(f"[调试] 目录 {save_dir_id} 中未找到文件列表，将分享整个目录")
            share_fid_list = [save_dir_id]
            target_name = save_dir_name
        else:
            # 根据文件名匹配找到转存后的文件
            share_fid_list: List[str] = []
            share_file_names: List[str] = []

            print(f"[调试] 开始匹配转存的 {len(data_list)} 个文件")
            for data in data_list:
                target_file_name = data['file_name']
                target_is_dir = data['dir']

                # 在目录文件列表中查找匹配的文件
                found = False
                for item in json_data['data']['list']:
                    if item.get('file_name') == target_file_name and item.get('dir') == target_is_dir:
                        share_fid_list.append(item['fid'])
                        share_file_names.append(item['file_name'])
                        found = True
                        print(f"[调试] 找到文件: {target_file_name} (fid: {item['fid']})")
                        break

                if not found:
                    print(f"[调试] 未找到文件: {target_file_name}")

            # 如果没有找到任何文件,则使用保存目录(兜底方案)
            if not share_fid_list:
                print(f"[调试] 未匹配到任何文件，将分享整个保存目录: {save_dir_name}")
                share_fid_list = [save_dir_id]
                target_name = save_dir_name
            else:
                # 分享标题:单个文件用文件名,多个文件用第一个文件名或保存目录名
                if len(share_fid_list) == 1:
                    target_name = share_file_names[0]
                else:
                    target_name = f"{share_file_names[0]} 等{len(share_fid_list)}个文件"
                print(f"[调试] 匹配到 {len(share_fid_list)} 个文件，准备分享")

        # 8. 生成分享链接
        try:
            print(f"[调试] 开始创建分享任务，fid_list: {share_fid_list}, 标题: {target_name}")
            share_task_id = await self.get_share_task_id(
                fid_list=share_fid_list,
                file_name=target_name,
                url_type=share_url_type,
                expired_type=share_expire_type,
                password=share_password
            )
            print(f"[调试] 分享任务创建成功，task_id: {share_task_id}")

            print(f"[调试] 开始获取分享 ID...")
            share_id = await self.get_share_id(share_task_id)
            print(f"[调试] 分享 ID 获取成功: {share_id}")

            print(f"[调试] 开始提交分享...")
            new_share_url, share_title = await self.submit_share(share_id)
            print(f"[调试] 分享链接生成成功: {new_share_url}")
        except Exception as e:
            print(f"[错误] 生成分享链接失败: {str(e)}")
            raise Exception(f"生成分享链接失败: {str(e)}")

        # 9. 返回结果
        transfer_info = TransferInfo(
            file_count=files_count,
            folder_count=folders_count,
            file_list=files_list,
            folder_list=folders_list,
            save_dir_name=save_dir_name
        )

        return TransferAndShareResponse(
            transfer_info=transfer_info,
            share_url=new_share_url,
            share_title=share_title
        )

    async def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """
        查询任务状态

        Args:
            task_id: 任务 ID

        Returns:
            任务状态信息

        Raises:
            Exception: 查询失败时抛出异常
        """
        submit_url = (
            f"https://drive-pc.quark.cn/1/clouddrive/task?pr=ucpro&fr=pc&uc_param_str=&"
            f"task_id={task_id}&retry_index=0&__dt=21192&__t={get_timestamp(13)}"
        )

        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(60.0, connect=60.0)
            response = await client.get(submit_url, headers=self.headers, timeout=timeout)
            json_data = response.json()

            if json_data.get('message') != 'ok':
                raise Exception(f"查询任务失败：{json_data.get('message', '未知错误')}")

            data = json_data.get('data', {})
            status = data.get('status', 0)
            task_title = data.get('task_title', '')

            # 计算进度
            progress = None
            if 'finished_amount' in data and 'total_amount' in data:
                total = data['total_amount']
                if total > 0:
                    progress = int((data['finished_amount'] / total) * 100)

            message = None
            if status == 1:
                message = "任务失败"
            elif status == 2:
                message = "任务成功"
            else:
                message = "任务进行中"

            return TaskStatusResponse(
                task_id=task_id,
                status=status,
                task_title=task_title,
                progress=progress,
                message=message,
                result=data
            )
