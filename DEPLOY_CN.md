# RadQA Explorer 公开部署

1. 解压 ZIP。将 `radqa-explorer` 文件夹内的内容上传到 GitHub 仓库。确认仓库根目录直接包含 `app.py`、`requirements.txt`、`src/` 和 `data/`。
2. 在 Streamlit Community Cloud 选择该 GitHub 仓库。分支填写实际分支（通常是 `main`）；入口填 `app.py`。如可选择 Python 版本，选本包已验证的 Python 3.12。
3. 发布应用并确认应用可公开访问。复制应用页面的 URL。GitHub 仓库链接只用于展示代码。
4. 用无痕窗口打开应用链接，确认访客无需登录。检查默认峰值 10 mm、distal R80 11 mm；上传 `data/fixtures/upload_shifted_curve.csv`，参考源选 Bundled synthetic teaching data，确认差值 +2 mm；点击下载并检查比较 CSV。
5. 验收成功后保存应用 URL，供 ChiEAC 周报或最终交付使用。

`requirements.txt` 与 `requirements_app.txt` 依赖版本一致。后者保留以兼容之前的 Windows 启动说明。

## 2026-11-10 验证记录

- Python 3.12 环境安装依赖成功。7 个单元测试、计算自检通过。
- Linux 上的 Streamlit AppTest 验证默认指标、上传与 +2 mm 参考比较，以及比较 CSV 内容与已验收样例逐字节一致。
- 本轮系统浏览器无法启动，因此本轮没有重新验证浏览器下载；先前完整浏览器验证记录仍在 `verification/`。
- GitHub 未推送、应用未部署。无痕窗口验收和 Windows 本机检查待完成。
