import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config_loader


class ConfigLoaderPidTest(unittest.TestCase):
    # PID 查找优先匹配完整 JAR 路径，避免同名 JAR 误匹配。
    @patch("config_loader.subprocess.run")
    def test_get_pid_by_pid_jar_path_matches_absolute_jar_path(self, run):
        run.return_value = SimpleNamespace(
            stdout="12345 java -Xmx1g -jar /tmp/assistant/assistant-server-1.0.jar\n"
        )

        pid = config_loader.get_pid_by_pid_jar_path(
            "/tmp/assistant/assistant-server-1.0.jar"
        )

        self.assertEqual(pid, 12345)


class ConfigLoaderRunServerTest(unittest.TestCase):
    def setUp(self):
        # run_server 测试只验证 Python 启动逻辑，不真实启动 Java。
        self.config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            ["-Xmx512m"],
            "",
            is_exists_config=True,
        )

    # 无 health_url 时，只能确认进程已启动，并写入 PID。
    @patch("config_loader.write_pid")
    @patch("config_loader.print_server_status")
    @patch("config_loader.is_running")
    @patch("config_loader.time.sleep")
    @patch("config_loader.subprocess.Popen")
    def test_run_server_reports_process_started_without_health_url(
        self,
        popen,
        sleep,
        is_running,
        print_server_status,
        write_pid,
    ):
        popen.return_value = SimpleNamespace(pid=12345)
        is_running.return_value = True

        result = config_loader.run_server(self.config, "/tmp/assistant")

        self.assertTrue(result)
        popen.assert_called_once()
        self.assertEqual(
            popen.call_args.args[0],
            [
                "java",
                "-Xmx512m",
                "-jar",
                "/tmp/assistant/assistant-server-1.0.jar",
            ],
        )
        self.assertEqual(popen.call_args.kwargs["stdout"], config_loader.subprocess.DEVNULL)
        self.assertEqual(popen.call_args.kwargs["stderr"], config_loader.subprocess.DEVNULL)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        write_pid.assert_called_once_with(12345, "/tmp/assistant")
        print_server_status.assert_called_once_with(
            jar_name="assistant-server-1.0.jar",
            pid=12345,
            server_status="ONLINE",
        )

    # 有 health_url 且检查通过时，才把服务状态打印为 ONLINE。
    @patch("config_loader.write_pid")
    @patch("config_loader.server_is_online_by_health_url")
    @patch("config_loader.print_server_status")
    @patch("config_loader.is_running")
    @patch("config_loader.time.sleep")
    @patch("config_loader.subprocess.Popen")
    def test_run_server_reports_online_when_health_check_passes(
        self,
        popen,
        sleep,
        is_running,
        print_server_status,
        server_is_online_by_health_url,
        write_pid,
    ):
        config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            [],
            "http://127.0.0.1:8080/health",
            is_exists_config=True,
        )
        popen.return_value = SimpleNamespace(pid=12345)
        is_running.return_value = True
        server_is_online_by_health_url.return_value = True

        result = config_loader.run_server(config, "/tmp/assistant")

        self.assertTrue(result)
        write_pid.assert_called_once_with(12345, "/tmp/assistant")
        server_is_online_by_health_url.assert_called_once_with(config)
        print_server_status.assert_called_once_with(
            jar_name="assistant-server-1.0.jar",
            pid=12345,
            server_status="ONLINE",
        )

    # 有 health_url 但检查失败时，不应误报 ONLINE。
    @patch("config_loader.write_pid")
    @patch("config_loader.server_is_online_by_health_url")
    @patch("config_loader.print_server_status")
    @patch("config_loader.is_running")
    @patch("config_loader.time.sleep")
    @patch("config_loader.subprocess.Popen")
    def test_run_server_does_not_report_online_when_health_check_fails(
        self,
        popen,
        sleep,
        is_running,
        print_server_status,
        server_is_online_by_health_url,
        write_pid,
    ):
        config = config_loader.ConfigInfo(
            "/tmp/assistant.zip",
            "assistant-server-1.0.jar",
            [],
            "http://127.0.0.1:8080/health",
            is_exists_config=True,
        )
        popen.return_value = SimpleNamespace(pid=12345)
        is_running.return_value = True
        server_is_online_by_health_url.return_value = False

        result = config_loader.run_server(config, "/tmp/assistant")

        self.assertTrue(result)
        write_pid.assert_called_once_with(12345, "/tmp/assistant")
        server_is_online_by_health_url.assert_called_once_with(config)
        print_server_status.assert_not_called()

    # Java 进程启动后很快退出时，run_server 应返回失败且不写 PID。
    @patch("config_loader.write_pid")
    @patch("config_loader.is_running")
    @patch("config_loader.time.sleep")
    # Popen 抛异常时，CLI 应友好失败，而不是把堆栈暴露给用户。
    @patch("config_loader.subprocess.Popen")
    def test_run_server_returns_false_when_process_exits(
        self,
        popen,
        sleep,
        is_running,
        write_pid,
    ):
        popen.return_value = SimpleNamespace(pid=12345)
        is_running.return_value = False

        result = config_loader.run_server(self.config, "/tmp/assistant")

        self.assertFalse(result)
        write_pid.assert_not_called()

    @patch("config_loader.subprocess.Popen")
    def test_run_server_returns_false_when_popen_fails(self, popen):
        popen.side_effect = FileNotFoundError

        result = config_loader.run_server(self.config, "/tmp/assistant")

        self.assertFalse(result)

    # 兼容历史启动方式：命令行里可能只有相对 JAR 文件名。
    @patch("config_loader.subprocess.run")
    def test_get_pid_by_pid_jar_path_matches_relative_jar_name(self, run):
        run.return_value = SimpleNamespace(
            stdout="12345 java -Xmx1g -Xms1024M -jar assistant-server-1.0.jar\n"
        )

        pid = config_loader.get_pid_by_pid_jar_path(
            "/Users/elliotk/project/python-project/server_cli/assistant-server-1.0.jar"
        )

        self.assertEqual(pid, 12345)


if __name__ == "__main__":
    unittest.main()
