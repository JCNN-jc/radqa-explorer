# Windows 本机检查

请将整个 ZIP 解压到新文件夹。需要 Python 3.10 或以上版本。

1. 双击 `01_install.bat`，等待依赖安装完成。出现错误时保留报错。
2. 双击 `03_run_checks.bat`。预期显示 7 个测试 OK 和自检 PASS。日志保存在 `verification/windows/`。
3. 双击 `02_start_app.bat`，保持窗口打开。若询问邮箱，留空回车。打开终端打印的 Local URL，通常为 http://localhost:8501。若端口被占用，以实际打印的 URL 为准。
4. 按 `WINDOWS_CHECKLIST.md` 检查浏览器。不要把尚未检查的项目填为通过。

如果双击窗口退出，请在当前文件夹打开 PowerShell，运行对应 `.bat`，例如 `.\02_start_app.bat`，并复制完整报错。停止旧版本请在旧窗口按 Ctrl+C。

这里的 Linux 测试结果不代表你的 Windows 电脑已经测试通过。
