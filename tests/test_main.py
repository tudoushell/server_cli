import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config_loader
import main


class MainCliTest(unittest.TestCase):
    def setUp(self):
        # CliRunner 直接调用 Typer app，避免通过真实 shell 启动命令。
        self.runner = CliRunner()
        # 大多数 CLI 测试共用一份有效配置，具体分支再按需覆盖。
        self.config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            ["-Xmx512m"],
            "",
            is_exists_config=True,
        )

    def invoke(self, *args):
        return self.runner.invoke(main.app, list(args))

    # deploy: 没有 config.json 且没有命令行参数时，应直接返回，不执行解压。
    @patch("main.config_loader.unpack_server_package_check")
    @patch("main.config_loader.get_config_info")
    def test_deploy_returns_when_config_is_missing(self, get_config_info, unpack):
        get_config_info.return_value = config_loader.ConfigInfo("", "")

        result = self.invoke("deploy")

        self.assertEqual(result.exit_code, 0)
        unpack.assert_not_called()

    # deploy: 有 config.json 时，优先使用配置文件中的信息。
    @patch("main.config_loader.unpack_server_package_check")
    @patch("main.config_loader.get_config_info")
    def test_deploy_unpacks_when_config_exists(self, get_config_info, unpack):
        get_config_info.return_value = self.config
        unpack.return_value = True

        result = self.invoke("deploy")

        self.assertEqual(result.exit_code, 0)
        unpack.assert_called_once_with(self.config)

    # deploy: 没有 config.json 时，允许通过命令行参数临时构造 ConfigInfo。
    @patch("main.config_loader.unpack_server_package_check")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_config_info")
    def test_deploy_uses_command_line_args_when_config_is_missing(
        self,
        get_config_info,
        isfile,
        unpack,
    ):
        get_config_info.return_value = config_loader.ConfigInfo("", "")
        isfile.return_value = True
        unpack.return_value = True

        result = self.invoke(
            "deploy",
            "--package",
            "/tmp/assistant.zip",
            "--jar",
            "assistant-server-1.0.jar",
        )

        self.assertEqual(result.exit_code, 0)
        unpack.assert_called_once()
        config_info = unpack.call_args.args[0]
        self.assertEqual(config_info.package_file_path, "/tmp/assistant.zip")
        self.assertEqual(config_info.jar_name, "assistant-server-1.0.jar")
        self.assertEqual(config_info.jvm_args, [])
        self.assertTrue(config_info.is_exists_config)

    # deploy: 缺少 package 时不能继续解压，否则会在文件检查阶段误报或异常。
    @patch("main.config_loader.unpack_server_package_check")
    @patch("main.config_loader.get_config_info")
    def test_deploy_returns_when_package_arg_is_missing_and_config_is_missing(
        self,
        get_config_info,
        unpack,
    ):
        get_config_info.return_value = config_loader.ConfigInfo("", "")

        result = self.invoke("deploy", "--jar", "assistant-server-1.0.jar")

        self.assertEqual(result.exit_code, 0)
        unpack.assert_not_called()

    # deploy: package 路径不存在时，应该停止在参数校验阶段。
    @patch("main.config_loader.unpack_server_package_check")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_config_info")
    def test_deploy_returns_when_package_file_does_not_exist(
        self,
        get_config_info,
        isfile,
        unpack,
    ):
        get_config_info.return_value = config_loader.ConfigInfo("", "")
        isfile.return_value = False

        result = self.invoke(
            "deploy",
            "--package",
            "/tmp/missing.zip",
            "--jar",
            "assistant-server-1.0.jar",
        )

        self.assertEqual(result.exit_code, 0)
        isfile.assert_called_once_with("/tmp/missing.zip")
        unpack.assert_not_called()

    # start: 没有 config.json 时，可以通过 install_dir/jar/jvm 命令行参数启动。
    @patch("main.config_loader.run_server")
    @patch("main.config_loader.server_is_online_by_health_url")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.os.path.isfile")
    @patch("main.os.path.isdir")
    @patch("main.config_loader.get_config_info")
    def test_start_uses_command_line_args_when_config_is_missing(
        self,
        get_config_info,
        isdir,
        isfile,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        server_is_online_by_health_url,
        run_server,
    ):
        install_dir = "/Users/elliotk/tmp/assistant"
        jar_name = "assistant-server-1.0.jar"
        jar_file_path = f"{install_dir}/{jar_name}"
        get_config_info.return_value = config_loader.ConfigInfo("", "")
        isdir.return_value = True
        isfile.return_value = True
        get_full_jar_path.return_value = (jar_file_path, install_dir)
        get_pid_by_pid_file.return_value = -1
        get_pid_by_pid_jar_path.return_value = -1
        server_is_online_by_health_url.return_value = False

        result = self.invoke(
            "start",
            "--install-dir",
            install_dir,
            "--jar",
            jar_name,
            "--jvm=-Xms500m -Xmx512m",
        )

        self.assertEqual(result.exit_code, 0)
        isdir.assert_called_once_with(install_dir)
        isfile.assert_any_call(jar_file_path)
        get_full_jar_path.assert_called_once()
        config_info = get_full_jar_path.call_args.args[0]
        self.assertEqual(config_info.package_file_path, jar_file_path)
        self.assertEqual(config_info.jar_name, jar_name)
        self.assertEqual(config_info.jvm_args, ["-Xms500m", "-Xmx512m"])
        get_pid_by_pid_file.assert_called_once_with(install_dir)
        get_pid_by_pid_jar_path.assert_called_once_with(jar_file_path)
        server_is_online_by_health_url.assert_not_called()
        run_server.assert_called_once_with(config_info, install_dir)

    # start: 没有已运行进程，且 JAR 存在时才真正调用 run_server。
    @patch("main.config_loader.run_server")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.server_is_online_by_health_url")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_start_runs_server_when_not_already_running(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        server_is_online_by_health_url,
        isfile,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = -1
        get_pid_by_pid_jar_path.return_value = -1
        server_is_online_by_health_url.return_value = False
        isfile.return_value = True

        result = self.invoke("start")

        self.assertEqual(result.exit_code, 0)
        get_pid_by_pid_jar_path.assert_called_once_with(
            "/tmp/assistant/assistant-server-1.0.jar"
        )
        server_is_online_by_health_url.assert_not_called()
        run_server.assert_called_once_with(self.config, "/tmp/assistant")

    # start: PID 文件中的进程还活着时，只补写 PID 并返回，不重复启动。
    @patch("main.config_loader.run_server")
    @patch("main.config_loader.write_pid")
    @patch("main.config_loader.server_is_online_by_health_url")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_start_writes_pid_and_returns_when_service_is_running(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        server_is_online_by_health_url,
        write_pid,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = 12345

        result = self.invoke("start")

        self.assertEqual(result.exit_code, 0)
        write_pid.assert_called_once_with(12345, "/tmp/assistant")
        server_is_online_by_health_url.assert_not_called()
        run_server.assert_not_called()

    # start: 配置了 health_url 时，已有进程还需要额外判断健康检查。
    @patch("main.config_loader.run_server")
    @patch("main.config_loader.write_pid")
    @patch("main.config_loader.server_is_online_by_health_url")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_start_checks_health_when_existing_pid_and_health_url_configured(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        server_is_online_by_health_url,
        write_pid,
        run_server,
    ):
        config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            ["-Xmx512m"],
            "http://127.0.0.1:8080/health",
            is_exists_config=True,
        )
        get_config_info.return_value = config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = 12345
        server_is_online_by_health_url.return_value = False

        result = self.invoke("start")

        self.assertEqual(result.exit_code, 0)
        write_pid.assert_called_once_with(12345, "/tmp/assistant")
        server_is_online_by_health_url.assert_called_once_with(config)
        run_server.assert_not_called()

    # start: JAR 文件不存在时不能调用 run_server。
    @patch("main.config_loader.run_server")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.server_is_online_by_health_url")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_start_does_not_run_when_jar_file_is_missing(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        server_is_online_by_health_url,
        isfile,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = -1
        get_pid_by_pid_jar_path.return_value = -1
        server_is_online_by_health_url.return_value = False
        isfile.return_value = False

        result = self.invoke("start")

        self.assertEqual(result.exit_code, 0)
        server_is_online_by_health_url.assert_not_called()
        run_server.assert_not_called()

    # restart: 服务已运行时，必须先停止原进程，再启动新进程。
    @patch("main.config_loader.run_server")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.kill_server")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_restart_stops_existing_process_then_starts(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        kill_server,
        isfile,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = 12345
        isfile.return_value = True

        result = self.invoke("restart")

        self.assertEqual(result.exit_code, 0)
        get_pid_by_pid_jar_path.assert_not_called()
        kill_server.assert_called_once_with(
            12345,
            "assistant-server-1.0.jar",
            "/tmp/assistant",
            False,
        )
        run_server.assert_called_once_with(self.config, "/tmp/assistant")

    # restart: 服务未运行时，不调用 kill_server，直接进入启动流程。
    @patch("main.config_loader.run_server")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.kill_server")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_restart_starts_when_service_is_not_running(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        kill_server,
        isfile,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = -1
        get_pid_by_pid_jar_path.return_value = -1
        isfile.return_value = True

        result = self.invoke("restart")

        self.assertEqual(result.exit_code, 0)
        kill_server.assert_not_called()
        run_server.assert_called_once_with(self.config, "/tmp/assistant")

    # restart: 重启前发现 JAR 不存在时，不应执行启动。
    @patch("main.config_loader.run_server")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.kill_server")
    @patch("main.config_loader.get_pid_by_pid_jar_path")
    @patch("main.config_loader.get_pid_by_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_restart_does_not_start_when_jar_file_is_missing(
        self,
        get_config_info,
        get_full_jar_path,
        get_pid_by_pid_file,
        get_pid_by_pid_jar_path,
        kill_server,
        isfile,
        run_server,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        get_pid_by_pid_file.return_value = -1
        get_pid_by_pid_jar_path.return_value = -1
        isfile.return_value = False

        result = self.invoke("restart")

        self.assertEqual(result.exit_code, 0)
        kill_server.assert_not_called()
        run_server.assert_not_called()

    # status: 没有 health_url 时，只根据 PID 是否存活判断状态。
    @patch("main.config_loader.print_server_status")
    @patch("main.config_loader.is_running")
    @patch("main.config_loader.read_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_status_uses_pid_when_health_url_is_empty(
        self,
        get_config_info,
        get_full_jar_path,
        read_pid_file,
        is_running,
        print_server_status,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        read_pid_file.return_value = 12345
        is_running.return_value = True

        result = self.invoke("status")

        self.assertEqual(result.exit_code, 0)
        print_server_status.assert_called_once_with(
            "assistant-server-1.0.jar",
            12345,
            "ONLINE",
        )

    # status: 配置了 health_url 时，PID 存活且健康检查通过才算 ONLINE。
    @patch("main.config_loader.print_server_status")
    @patch("main.config_loader.server_is_online")
    @patch("main.config_loader.is_running")
    @patch("main.config_loader.read_pid_file")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_status_requires_health_check_when_configured(
        self,
        get_config_info,
        get_full_jar_path,
        read_pid_file,
        is_running,
        server_is_online,
        print_server_status,
    ):
        config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            ["-Xmx512m"],
            "http://127.0.0.1:8080/health",
            is_exists_config=True,
        )
        get_config_info.return_value = config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        read_pid_file.return_value = 12345
        is_running.return_value = True
        server_is_online.return_value = False

        result = self.invoke("status")

        self.assertEqual(result.exit_code, 0)
        print_server_status.assert_called_once_with(
            "assistant-server-1.0.jar",
            12345,
            "OFFLINE",
        )

    # log: 默认读取服务目录下的 server.log，并只显示最近指定行数。
    @patch("main.subprocess.run")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_log_tails_default_log_file_from_config(
        self,
        get_config_info,
        get_full_jar_path,
        isfile,
        run,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        isfile.return_value = True

        result = self.invoke("log", "--lines", "20")

        self.assertEqual(result.exit_code, 0)
        isfile.assert_called_once_with("/tmp/assistant/server.log")
        run.assert_called_once_with(["tail", "-n", "20", "/tmp/assistant/server.log"])

    # log: --follow 打开实时跟踪，命令参数应包含 tail -f。
    @patch("main.subprocess.run")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_log_follows_log_file(
        self,
        get_config_info,
        get_full_jar_path,
        isfile,
        run,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        isfile.return_value = True

        result = self.invoke("log", "--follow", "--lines", "50")

        self.assertEqual(result.exit_code, 0)
        run.assert_called_once_with(["tail", "-f", "-n", "50", "/tmp/assistant/server.log"])

    # log: 相对日志路径会按服务目录解析。
    @patch("main.subprocess.run")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_log_uses_relative_log_file_from_service_dir(
        self,
        get_config_info,
        get_full_jar_path,
        isfile,
        run,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        isfile.return_value = True

        result = self.invoke("log", "--log-file", "logs/app.log")

        self.assertEqual(result.exit_code, 0)
        isfile.assert_called_once_with("/tmp/assistant/logs/app.log")
        run.assert_called_once_with(["tail", "-n", "100", "/tmp/assistant/logs/app.log"])

    # log: 绝对日志路径直接使用，不再拼接服务目录。
    @patch("main.subprocess.run")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info")
    def test_log_uses_absolute_log_file(
        self,
        get_config_info,
        get_full_jar_path,
        isfile,
        run,
    ):
        get_config_info.return_value = self.config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        isfile.return_value = True

        result = self.invoke("log", "--log-file", "/var/log/app.log")

        self.assertEqual(result.exit_code, 0)
        isfile.assert_called_once_with("/var/log/app.log")
        run.assert_called_once_with(["tail", "-n", "100", "/var/log/app.log"])

    # log: 没有 config.json 时，可以通过 install_dir/jar 定位默认日志文件。
    @patch("main.subprocess.run")
    @patch("main.os.path.isfile")
    @patch("main.config_loader.get_full_jar_path")
    @patch("main.config_loader.get_config_info_by_args")
    @patch("main.config_loader.get_config_info")
    def test_log_uses_command_line_args_when_config_is_missing(
        self,
        get_config_info,
        get_config_info_by_args,
        get_full_jar_path,
        isfile,
        run,
    ):
        config = config_loader.ConfigInfo(
            "/tmp/assistant/assistant-server-1.0.jar",
            "assistant-server-1.0.jar",
            [],
            "",
            is_exists_config=True,
        )
        get_config_info.return_value = config_loader.ConfigInfo("", "")
        get_config_info_by_args.return_value = config
        get_full_jar_path.return_value = (
            "/tmp/assistant/assistant-server-1.0.jar",
            "/tmp/assistant",
        )
        isfile.return_value = True

        result = self.invoke(
            "log",
            "--install-dir",
            "/tmp/assistant",
            "--jar",
            "assistant-server-1.0.jar",
        )

        self.assertEqual(result.exit_code, 0)
        get_config_info_by_args.assert_called_once_with(
            "/tmp/assistant",
            "assistant-server-1.0.jar",
        )
        run.assert_called_once_with(["tail", "-n", "100", "/tmp/assistant/server.log"])

    # log: lines 必须是正数，非法时不执行 tail。
    @patch("main.subprocess.run")
    def test_log_returns_when_lines_is_not_positive(self, run):
        result = self.invoke("log", "--lines", "0")

        self.assertEqual(result.exit_code, 0)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
