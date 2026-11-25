# 📦 TVBox 深度私有化中心 (Deep Localizer)

这个项目的唯一目的，就是**防止上游作者删库跑路或接口失效**。

它不仅仅聚合 JSON，它会像爬虫一样，把你指定的 TVBox 接口里引用的 **所有外部依赖文件** 全部下载到你自己的 GitHub 仓库中，并自动把 JSON 里的链接替换成你自己的直连加速链接。

## 🛡️ 私有化范围
1. **`spider` (JAR包)**：TVBox 的核心爬虫引擎（下载至 `jar/` 目录）。
2. **`api` (JS插件)**：DRpy 或其他 JavaScript 编写的站点解析插件（下载至 `js/` 目录）。
3. **`ext` (外部配置)**：很多精品源会把复杂的路由规则、分类写在外部的 `.json` 或 `.txt` 中（下载至 `ext/` 目录）。

所有的文件下载后都会进行 **MD5 哈希去重**，不会让你的仓库无限膨胀。

## 🚀 部署步骤
1. 推送所有文件到 GitHub。
2. 确保开启了 Actions 的 `Read and write permissions`。
3. 运行 Actions。
4. 你的仓库中会自动多出 `jar/`, `js/`, `ext/` 文件夹，里面装满了原作者的源码文件！
5. 在客户端使用 `output/tvbox_localized.json` 即可体验绝对稳定的私有化资源。
