# encoding: utf-8
import os
import json
import time
import traceback
import shutil
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
CONFIG_JSON_FILE = 'config.json'
ARCHIVE_EXT = ('.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.gz', '.bz2')


class ConfigInfo:
    __slots__ = ('_package_file_path', '_jar_name', '_is_exists_config', '_jar_extra_args', '_health_url')

    def __init__(self, package_file_path: str, jar_name: str, jar_extra_args=None, health_url=None, *,
                 is_exists_config: bool = False):
        if jar_extra_args is None:
            jar_extra_args = []
        self._package_file_path: str = package_file_path
        self._jar_name: str = jar_name
        self._jar_extra_args = jar_extra_args
        self._health_url = health_url
        self._is_exists_config: bool = is_exists_config

    @property
    def is_exists_config(self):
        return self._is_exists_config

    @property
    def package_file_path(self):
        return self._package_file_path

    @property
    def jar_name(self):
        return self._jar_name

    @property
    def jar_extra_args(self):
        return self._jar_extra_args

    @property
    def health_url(self):
        return self._health_url


def get_package_file_path(config_info: ConfigInfo):
    """
     返回server jar文件的完整路径
    :param config_info:
    :return: 压缩包父目录,压缩包文件名(不带后缀)
    """
    parent_dir = os.path.dirname(config_info.package_file_path)
    base_name = os.path.splitext(os.path.basename(config_info.package_file_path))[0]
    return parent_dir, base_name


def get_full_jar_path(config_info: ConfigInfo):
    """
     返回server jar文件的完整路径
    :param config_info:
    :return: jar文件的完整路径,jar文件的父目录
    """
    parent_dir = os.path.dirname(config_info.package_file_path)
    base_name = os.path.splitext(os.path.basename(config_info.package_file_path))[0]
    return os.path.join(parent_dir, base_name, config_info.jar_name), os.path.join(parent_dir, base_name)


def get_config_info() -> ConfigInfo:
    if os.path.exists(CONFIG_JSON_FILE):
        with open(CONFIG_JSON_FILE, 'r', encoding="utf-8") as json_file:
            json_str = json_file.read()
            if json_str:
                server_config = json.loads(json_str)
                server_package = str(server_config.get('package_file_path'))
                if not server_package:
                    console.print("配置文件中未找到服务程序路径，请检查配置文件", style='bold red')
                    return ConfigInfo('', '')
                if not server_package.lower().endswith(ARCHIVE_EXT):
                    console.print(f"服务程序文件 {server_package} 不是支持的归档格式，请检查配置文件", style='bold red')
                    return ConfigInfo('', '')
                server_jar = str(server_config.get('jar_name'))
                if not server_jar:
                    console.print("配置文件中未找到服务程序名称，请检查配置文件", style='bold red')
                    return ConfigInfo(server_package, '')
                if not server_jar.lower().endswith('.jar'):
                    console.print(f"服务程序名称 {server_jar} 不是支持的 jar 格式，请检查配置文件", style='bold red')
                    return ConfigInfo(server_package, '')
                jar_extra_args = server_config.get('jar_extra_args', [])
                health_url = server_config.get('health_url')
                return ConfigInfo(server_package, server_jar, jar_extra_args, health_url, is_exists_config=True)
            else:
                console.print("配置文件为空，请检查配置文件", style='bold red')
                return ConfigInfo('', '')
    else:
        console.print("配置文件不存在，请检查配置文件 config.json", style='bold red')
        return ConfigInfo('', '')


def unpack_server_package_check(config_info: ConfigInfo) -> bool:
    if not os.path.exists(config_info.package_file_path):
        console.print(f"服务程序文件 {config_info.package_file_path} 不存在，请检查配置文件", style='bold red')
        return False
    parent_dir, base_name = get_package_file_path(config_info)
    target_directory_name = os.path.join(parent_dir, base_name)
    if os.path.exists(target_directory_name):
        console.print(f"目标目录 {target_directory_name} 已存在，跳过解压操作", style='bold yellow')
    else:
        try:
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          transient=True, console=console) as prog:
                prog.add_task(f"正在解压 {config_info.package_file_path} ...", total=None)
                shutil.unpack_archive(config_info.package_file_path, parent_dir)
        except Exception:
            console.print(f"服务程序解压失败，错误信息：{traceback.format_exc()}", style='bold red')
            return False
            # 检索文件，是否存在运行服务文件
        if not os.path.isfile(os.path.join(str(target_directory_name), config_info.jar_name)):
            console.print(f"服务程序解压完成，但未找到运行服务文件 {config_info.jar_name}", style='bold yellow')
            return False
        else:
            console.print(f"服务程序解压完成，目标目录：{target_directory_name}", style='bold green')
    console.print("服务安装成功，请运行 server_cli start 启动服务", style='bold green')
    return True
