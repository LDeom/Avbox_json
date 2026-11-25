# 🚀 TVBox 五合一终极聚合矩阵

本项目整合多来源 TVBox 配置，定时抓取、筛选并输出聚合配置。

## 功能
- 抓取 apilinks.txt 中的配置链接
- 合并 sites、lives、parses
- 根据名称关键词过滤部分不需要的站点
- 检测站点 API 连通性
- 下载并私有化主 Spider JAR（成功时）
- 输出单仓、多仓配置与诊断面板

## 部署
GitHub Actions 每12小时自动运行，也支持手动触发。
仓库 Settings -> Actions -> General 中需允许 Actions 写入内容。
