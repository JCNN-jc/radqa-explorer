# GitHub 上传说明

建议仓库名：`radqa-explorer`。

建议 Description：Educational depth–dose CSV analysis with distal R80, reference comparison, input validation, and traceable reports.

先将 ZIP 全部解压。把 `radqa-explorer` 文件夹内的内容上传到仓库根目录，确保 `README.md` 和 `app.py` 直接位于根目录，而不是多套一层文件夹。保留 `docs/images`、`src`、`tests`、`data`、`verification` 的目录结构。

如果使用 Git，在此文件夹中执行：

```bash
git init
git add .
git commit -m "Prepare RadQA Explorer v0.4 portfolio release"
git branch -M main
```

然后使用你创建的空仓库的真实地址添加 remote 并 push。这里没有预填用户名或仓库地址，也没有替你创建或发布仓库。不要把 ZIP 本身作为唯一的仓库文件上传。

上传后查看 README 两张截图能否显示；点击代码和验证记录确认路径有效。Windows 本机检查未完成时，保留 README 中的待确认说明。项目中未实现的功能已标为 future work。
