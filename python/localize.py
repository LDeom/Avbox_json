import json
import asyncio
import aiohttp
import time
import os
import hashlib

API_LINKS_FILE = "apilinks.txt"
OUTPUT_JSON = "output/tvbox_localized.json"
TIMEOUT = 10

# 记录统计信息
stats = {"jar": 0, "js": 0, "ext": 0}

async def download_asset(session, url, folder, repo_base_url):
    """下载远程资产并返回本地化后的加速链接"""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return url
        
    try:
        async with session.get(url, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                content = await resp.read()
                
                # 获取文件后缀 (例如 .jar, .js, .json, .txt)
                ext = url.split("?")[0].split(".")[-1]
                if ext not in ["jar", "js", "json", "txt", "m3u"]:
                    ext = "bin"
                    
                # 计算 MD5 防重复
                md5_hash = hashlib.md5(content).hexdigest()[:8]
                local_path = f"{folder}/asset_{md5_hash}.{ext}"
                
                # 保存到本地文件夹
                if not os.path.exists(local_path):
                    with open(local_path, "wb") as f:
                        f.write(content)
                    stats[folder] += 1
                    print(f"[✅ 私有化成功] {local_path} <- {url}")
                
                # 拼接返回你的 GitHub 加速链接
                return f"{repo_base_url}/{local_path}"
    except Exception as e:
        print(f"[❌ 私有化失败] {url} : {e}")
        pass
        
    # 如果下载失败，退回使用原始链接
    return url

async def localize_site(session, site, repo_base_url):
    """处理单个站点里的 ext 和 api 依赖"""
    # 1. 私有化 API 脚本 (如果是 .js 结尾的 DRpy 脚本)
    api_url = site.get("api", "")
    if isinstance(api_url, str) and api_url.startswith("http") and ".js" in api_url:
        site["api"] = await download_asset(session, api_url, "js", repo_base_url)
        
    # 2. 私有化 ext 扩展配置 (很多高质量源的路由或配置写在独立的 json/txt 里)
    ext_url = site.get("ext", "")
    if isinstance(ext_url, str) and ext_url.startswith("http"):
        site["ext"] = await download_asset(session, ext_url, "ext", repo_base_url)
    # 有些 ext 是列表格式，遍历下载
    elif isinstance(ext_url, list):
        new_ext_list = []
        for u in ext_url:
            if isinstance(u, str) and u.startswith("http"):
                new_ext_list.append(await download_asset(session, u, "ext", repo_base_url))
            else:
                new_ext_list.append(u)
        site["ext"] = new_ext_list
        
    return site

async def main():
    # 获取你的 GitHub 仓库路径，比如 YOUR_NAME/TVBOX_REPO
    repo_name = os.getenv("GITHUB_REPOSITORY", "YOUR_NAME/YOUR_REPO")
    # 构建你的 CDN 加速前缀
    repo_base_url = f"https://ghfast.top/https://raw.githubusercontent.com/{repo_name}/main"
    
    with open(API_LINKS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    async with aiohttp.ClientSession() as session:
        print(f"=== 开始拉取总配置 ===")
        # 这里简单起见，只拉取 apilinks.txt 里的第一条作为主配置进行深度私有化
        target_url = urls[0].split(",")[-1].strip()
        
        async with session.get(target_url) as resp:
            data = await resp.json(content_type=None)
            
        print(f"\n=== 1. 开始私有化 Spider JAR ===")
        spider_url = data.get("spider", "")
        if spider_url:
            data["spider"] = await download_asset(session, spider_url, "jar", repo_base_url)
            
        print(f"\n=== 2. 开始并发私有化 JS 和 EXT 依赖 ===")
        sites = data.get("sites", [])
        tasks = [localize_site(session, site, repo_base_url) for site in sites]
        data["sites"] = await asyncio.gather(*tasks)
        
        # 写入最终私有化配置
        os.makedirs("output", exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🎉 深度私有化完成！")
        print(f"📦 共下载 JAR: {stats['jar']} 个")
        print(f"📦 共下载 JS: {stats['js']} 个")
        print(f"📦 共下载 EXT: {stats['ext']} 个")

if __name__ == "__main__":
    asyncio.run(main())
