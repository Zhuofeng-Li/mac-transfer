# mac-transfer

将这台 Mac 的操作设置迁移到新 Mac。最新快照：**2026-11-03**。

## 新电脑恢复

先安装 Xcode Command Line Tools（`xcode-select --install`），然后：

```bash
git clone https://github.com/Zhuofeng-Li/mac-transfer.git ~/mac-transfer
bash ~/mac-transfer/bootstrap.sh
```

安装 Input Source Pro、搜狗输入法等手动安装项目。启动 Alfred 和 Typeless 各一次，让它们生成本机配置，然后退出 Alfred、Rectangle、Input Source Pro、Scroll Reverser、Snipaste、Cursor、Karabiner 设置窗口、f.lux、IINA 和 Typeless。

```bash
# 先预览；不修改设置
python3 ~/mac-transfer/settings/restore.py --dry-run
# 恢复设置
python3 ~/mac-transfer/settings/restore.py
# 安装 Cursor 扩展（bootstrap 已执行过则可省略）
bash ~/mac-transfer/cursor/install-extensions.sh
```

需要 Python 3.9 或更高版本。恢复后注销并重新登录；在系统设置中重新授权辅助功能、输入监控和屏幕录制。权限和软件许可证不会通过配置文件迁移。

恢复会把原有文件和偏好设置备份到 `~/Library/Application Support/mac-transfer/backups/<时间>/`。系统偏好按键合并；文件以快照替换，Cursor 若原来使用同步软链接，会先备份内容并改为本地文件，避免覆盖同步目标。Alfred 本机配置会映射到新电脑的 localhash，并尊重新电脑现有的 Alfred 配置目录。Input Source Pro 的数据库会整体替换，所以请在新电脑建立新规则之前恢复。

## 已备份内容

| 项目 | 内容 | 状态 |
|---|---|---|
| Alfred 5 | 呼出快捷键、默认搜索范围和文件类型 | 当前配置包没有 Workflows、Snippets 或 Themes |
| Rectangle | 自定义快捷键、默认快捷键方案、后续执行行为 | 已导出 |
| Karabiner-Elements | 1 个 Profile、7 条复杂规则、自定义规则文件 | 与本机核对一致 |
| Input Source Pro | 指示器、默认输入法、5 条应用记录和数据库结构 | 默认输入法是搜狗；当前无浏览器规则/快捷键组，应用记录未指定固定输入法 |
| Scroll Reverser | 滚动反转、触控板行为 | 已导出 |
| macOS | 已设置的系统快捷键、键盘偏好、触控板/鼠标手势、Dock 和 Finder 行为 | 仅选取操作偏好，不包含最近文件、Dock 固定项目或个人文本替换 |
| Cursor | 编辑器设置、快捷键、25 个扩展 | 去掉远程主机列表、主机端口映射、云项目名和旧机器工作目录；本机 Snippets 目录为空 |
| Typeless | 听写、Ask Anything、翻译、粘贴上次结果的快捷键；语言、启动、浮条、音效、外观偏好 | 按键合并，保留新电脑的其余设置；不含账号、麦克风硬件 ID、录音和听写历史 |
| fish | 当前 config.fish | 当前文件只有交互式 Shell 占位块，已更新旧快照 |
| Snipaste | config.ini 中的界面/截图偏好 | 不含截图历史；当前没有自定义快捷键条目 |
| f.lux | 色温、过渡和起床时间 | 不包含定位信息；新电脑需重新设定位置 |
| IINA | 控制栏位置、音量 | 不包含播放历史 |

准确文件清单见 `settings/manifest.json`。Karabiner、Cursor 和 fish 沿用原仓库目录，其余快照位于 `settings/`。

## 尚需手动处理

- Hidden Bar、1Focus：沙盒内的实际偏好尚未成功读取，本次不声称已备份。
- Typeless 个人词典：没有在本地配置文件中找到独立词典；新电脑登录后检查账户同步。快捷键与操作偏好已备份。
- `.zshrc`：包含本机 SSH 密码辅助脚本的调用，不上传；SSH 密钥、密码辅助脚本、Git 凭据也不上传。
- Alfred Powerpack 等许可证、浏览器账户、聊天记录、VPN/远程网络登录：单独迁移或重新登录。
- 触控板/鼠标设置可能受新硬件和 macOS 版本影响，恢复后检查手势与快捷键。
- Input Source Pro 当前为 build 520 的数据库；新电脑优先使用同版本或兼容的新版本，恢复后检查应用规则。
- 如果希望继续用 fish 作为登录 Shell，安装完成后自行执行 `chsh -s "$(command -v fish)"`（必要时先把该路径加入 `/etc/shells`）。

## 后续更新

此仓库公开。只提交审核过的设置，不要提交整个 `Library`、应用数据库目录、`.ssh`、`.env`、工作流密钥或历史记录。原来的 `mackup.cfg` 保留供参考；新的安装流程不再自动运行 `mackup restore`，以免它覆盖这份快照。

`settings/restore.py` 是恢复工具，不会自动重新采集旧电脑的新设置。更新配置快照后再提交：

```bash
cd ~/mac-transfer
git diff
git add <已审核的文件>
git commit -m "Update Mac settings snapshot"
git push
```
