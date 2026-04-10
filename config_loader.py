# encoding: utf-8
import os
import json
import time
import traceback
import shutil
from pathlib import Path
import subprocess
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
JAR_START_TIMEOUT = 7
CONFIG_JSON_FILE = 'config.json'
SERVER_PID_FILE = 'java_server.pid'
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


def server_is_online(health_url: str) -> bool:
    try:
        res = requests.get(health_url, timeout=3)
        return res.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.RequestException:
        return False

def get_pid_by_server_name(service_name: str) -> int:
    """
     获取服务PID
    :param service_name: 服务名
    :return: 进程ID
    """
    sub_process = subprocess.run(f"ps -ef|grep {service_name}",
                                 shell=True, stdout=subprocess.PIPE, text=True)
    for line in sub_process.stdout.splitlines():
        if f"{service_name}" in line and "grep" not in line:
            return int(line.split()[1])
    return -1


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


def server_is_online_by_pid_file(config_info: ConfigInfo, jar_parent_path: str, jar_file_path: str) -> bool:
    # 先判断是否存在PID文件，如果有，检测服务是否存在
    path = Path(jar_parent_path)
    files = [file for file in path.iterdir() if file.is_file() and file.name.lower().endswith('.pid')]
    if len(files) == 0:
        # 没有pid文件则通过服务器心跳检测和ps -ef 去判断服务是否存在，存在，写入pid文件(没有pid文件)
        if config_info.health_url and server_is_online(config_info.health_url):
            console.print(f"{config_info.jar_name}服务已启动", style='bold yellow')
            return True
    else:
        for file in files:
            with open(file, 'r') as pid_file:
                pid = pid_file.read()
                if not pid:
                    continue
                if is_running(int(pid)):
                    console.print(f"服务已启动，pid: {pid}", style='bold yellow')
                    return True

    if not os.path.isfile(jar_file_path):
        console.print(f"启动失败 {jar_file_path} 不存在", style='bold red')
        return False
    return True


def is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def write_pid(pid: int, jar_parent_path: str):
    # 写入pid文件
    with open(os.path.join(jar_parent_path, SERVER_PID_FILE), 'w') as pid_file:
        pid_file.write(str(pid))


def run_server(config_info: ConfigInfo, jar_parent_path: str) -> bool:
    with Progress(SpinnerColumn(), TextColumn("[process.description]{task.description}]"),
                  transient=True, console=console) as prog:
        prog.add_task(f"正在启动服务 {config_info.jar_name} ...", total=None)
        server_process = subprocess.Popen(["java", "-jar", *config_info.jar_extra_args, config_info.jar_name],
                                          cwd=jar_parent_path,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          text=True)
        time.sleep(JAR_START_TIMEOUT)
        pid = server_process.pid
        if server_process.poll() is None:
            console.print(Panel(
                f"[bold green]服务已启动！[/]\n\n"
                f"  服务名：[bold]{config_info.jar_name}[/]\n"
                f"  PID   ：[bold]{pid}[/]\n",
                title="[green]✔ 启动成功[/]",
                border_style="green"
            ))
        else:
            stdout, _ = server_process.communicate()
            console.print(f"服务启动失败，错误信息：\n{stdout}", style='bold red', markup=False)
            return False
        console.print(f"服务启动成功，进程ID：{pid}", style='bold green')
        write_pid(pid, jar_parent_path)
        return True
