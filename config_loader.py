# encoding: utf-8
import os
import json
import signal
import time
import traceback
import shutil
import shlex
import subprocess
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
JAR_START_TIMEOUT = 7
CONFIG_JSON_FILE = 'config.json'
SERVER_PID_FILE = 'java_server.pid'
ARCHIVE_EXT = ('.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz', '.gz', '.bz2')


class ConfigInfo:
    __slots__ = ('_package_file_path', '_jar_name', '_is_exists_config', '_jvm_args', '_health_url')

    def __init__(self, package_file_path: str, jar_name: str, jvm_args=None, health_url=None, *,
                 is_exists_config: bool = False):
        if jvm_args is None:
            jvm_args = []
        self._package_file_path: str = package_file_path
        self._jar_name: str = jar_name
        self._jvm_args = jvm_args
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
    def jvm_args(self):
        return self._jvm_args

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
    """
    检查服务是否在线
    :param health_url: 健康检查URL
    :return: True表示服务在线，False表示服务离线或无法连接
    """
    try:
        res = requests.get(health_url, timeout=3)
        return res.status_code == 200
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.RequestException:
        return False


def get_pid_by_pid_file(jar_parent_path: str) -> int:
    """
    通过PID文件/进程获取服务PID
    :param jar_parent_path: jar文件的父目录路径
    :return: 进程ID，若不存在或无法读取则返回-1
    """
    pid_file = os.path.join(jar_parent_path, SERVER_PID_FILE)
    if not os.path.isfile(pid_file):
        return -1
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
    except ValueError:
        return -1
    return pid if is_running(pid) else -1


def get_pid_by_pid_jar_path(jar_path: str) -> int:
    try:
        result = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False
        )
    except OSError:
        return -1

    jar_path = os.path.abspath(jar_path)
    jar_name = os.path.basename(jar_path)

    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        pid, args = parts
        if "java" not in args:
            continue
        if "-jar" not in args:
            continue
        try:
            command_args = shlex.split(args)
        except ValueError:
            command_args = args.split()
        jar_arg = ""
        try:
            jar_arg = command_args[command_args.index("-jar") + 1]
        except (ValueError, IndexError):
            pass
        if jar_arg and (os.path.abspath(jar_arg) == jar_path or os.path.basename(jar_arg) == jar_name):
            try:
                return int(pid)
            except ValueError:
                return -1
    return -1


def get_config_info() -> ConfigInfo:
    """
    从配置文件中获取服务配置信息
    :return: ConfigInfo对象，包含服务程序路径和名称
    """
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
                jvm_args = server_config.get('jvm_args', [])
                health_url = server_config.get('health_check_url')
                return ConfigInfo(server_package, server_jar, jvm_args, health_url, is_exists_config=True)
            else:
                console.print("配置文件为空，请检查配置文件", style='bold red')
                return ConfigInfo('', '')
    else:
        # console.print("配置文件不存在，请检查配置文件 config.json", style='bold red')
        return ConfigInfo('', '')


def unpack_server_package_check(config_info: ConfigInfo) -> bool:
    """
     解压服务程序包并校验
    :param config_info: ConfigInfo对象，包含服务程序路径和名称
    :return: True表示已解压，False表示未解压或解压失败
    """
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


def server_is_online_by_health_url(config_info: ConfigInfo) -> bool:
    return bool(config_info.health_url and server_is_online(config_info.health_url))


def is_running(pid: int) -> bool:
    if pid == -1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def write_pid(pid: int, jar_parent_path: str):
    # 写入pid文件
    with open(os.path.join(jar_parent_path, SERVER_PID_FILE), 'w') as pid_file:
        pid_file.write(str(pid))


def remove_pid(jar_parent_path: str):
    pid_file_path = os.path.join(jar_parent_path, SERVER_PID_FILE)
    if os.path.isfile(pid_file_path):
        os.remove(pid_file_path)


def read_pid_file(jar_parent_path: str, jar_name: str) -> int:
    pid = -1
    if os.path.isfile(os.path.join(jar_parent_path, SERVER_PID_FILE)):
        with open(os.path.join(jar_parent_path, SERVER_PID_FILE), 'r') as pid_file:
            pid = int(pid_file.read().strip())
    if pid > -1:
        return pid
    else:
        return get_pid_by_pid_jar_path(jar_name)


def print_server_status(jar_name: str, pid: int, server_status: str):
    pid = -1 if server_status == "OFFLINE" else pid
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("SERVER_NAME", justify="center")
    table.add_column("PID", justify="center")
    table.add_column("STATUS", justify="center")
    table.add_row(jar_name.replace(".jar", "").upper(),
                  "NONE" if pid == -1 else str(pid),
                  server_status)
    console.print(f'================服务状态===================')
    console.print(table)


def run_server(config_info: ConfigInfo, jar_parent_path: str) -> bool:
    with Progress(SpinnerColumn(), TextColumn("[process.description]{task.description}"),
                  transient=True, console=console) as prog:
        prog.add_task(f"正在启动服务 {config_info.jar_name} ...", total=None)
        jar_file_path = os.path.join(jar_parent_path, config_info.jar_name)
        try:
            server_process = subprocess.Popen(["java", *config_info.jvm_args, "-jar", jar_file_path],
                                              cwd=jar_parent_path,
                                              stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL,
                                              text=True,
                                              start_new_session=True)
        except FileNotFoundError:
            console.print("服务启动失败，未找到 java 命令或服务目录不存在", style='bold red')
            return False
        except OSError as exc:
            console.print(f"服务启动失败，错误信息：{exc}", style='bold red')
            return False
        time.sleep(JAR_START_TIMEOUT)
        pid = server_process.pid
        if not is_running(pid):
            console.print("服务启动失败，进程已退出", style='bold red')
            return False
        write_pid(pid, jar_parent_path)
        if config_info.health_url and server_is_online_by_health_url(config_info):
            print_server_status(jar_name=config_info.jar_name, pid=pid, server_status="ONLINE")
            return True
        if config_info.health_url:
            console.print(f"{config_info.jar_name}进程已启动，但健康检查未通过，pid: {pid}", style='bold yellow')
            return True
        print_server_status(jar_name=config_info.jar_name, pid=pid, server_status="ONLINE")
        return True


def kill_server(pid: int, jar_name: str, jar_parent_path: str, force: bool = False):
    if not is_running(pid):
        remove_pid(jar_parent_path)
        console.print(f"服务不存在", style='bold yellow')
        return
    signum = signal.SIGKILL if force else signal.SIGTERM
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  transient=True, console=console) as prog:
        prog.add_task("正在停止服务...", total=None)
        try:
            os.killpg(os.getpgid(pid), signum)
            time.sleep(5)
            if is_running(pid):
                console.print("服务仍在运行，请使用--force 强制停止....")
            remove_pid(jar_parent_path)
        except ProcessLookupError:
            console.print(f"服务不存在", style='bold yellow')
        except PermissionError:
            console.print("权限不足，请尝试使用 sudo 或管理员权限执行操作")
    return
