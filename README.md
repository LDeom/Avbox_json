# TVBox 五合一终极聚合矩阵

自动聚合 TVBox 配置源、关键词过滤、生成单仓/多仓配置及体检报告，并尝试将主 spider JAR 本地化。

## 自动部署
- GitHub Actions 每 12 小时运行，并支持手动运行。
- Settings → Actions → General → Workflow permissions 需允许写入。
- 成功运行后生成 output 配置和 dashboard，以及 jar/ 目录中的 JAR 文件。

订阅链接：
`https://ghfast.top/https://raw.githubusercontent.com/LDeom/Avbox_json/main/output/single_core.json`

注意：当前引擎所谓 L2 检查仅是HTTP状态码检查的简化实现，不能保证源实际可播放；关键词过滤也不是全面广告检测，请验证输出。
