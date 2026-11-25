import json
import asyncio
import aiohttp
import time
import os
import hashlib
import glob

API_LINKS_FILE = "apilinks.txt"
OUTPUT_JSON = "output/tvbox_localized.json"
TIMEOUT = 12

# 伪装为标准客户端/浏览器，绕过常见防火墙拦截
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

stats = {"jar": 0, "js": 0, "ext": 0, "deleted": 0}
active_assets = set()

async def download_asset(session, url, folder, repo_base_url):
    """下载远程资产并返回本地化后的加速链接"""
    if not url or not isinstance(url, str) or not url.startswith("http"):
        return url
        
    # 处理部分源中 spider 链接后面带有 ;md5;xxxx 的参数情况
    clean_url = url.split(";")[0].strip()
    suffix_part = ";" + ";".join(url.split(";")[1:]) if ";" in url else ""
        
    try:
        async with session.get(clean_url, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                content = await resp.read()
                if not content:
                    return url
                
                ext = clean_url.split("?")[0].split(".")[-1].lower()
                if ext not in ["jar", "js", "json", "txt", "m3u", "py"]:
                    ext = "bin"
                    
                md5_hash = hashlib.md5(content).hexdigest()[:8]
                local_path = f"{folder}/asset_{md5_hash}.{ext}"
                active_assets.add(local_path)
                
                if not os.path.exists(local_path):
                    with open(local_path, "wb") as f:
                        f.write(content)
                    stats[folder] += 1
                    print(f"[✅ 获取新版本] {local_path} <- {clean_url}")
                else:
                    print(f"[⚡ 版本无变化] {local_path}")
                
                return f"{repo_base_url}/{local_path}{suffix_part}"
    except Exception as e:
        print(f"[⚠️ 资产下载跳过] {clean_url} : {e}")
        
    return url

async def localize_site(session, site, repo_base_url):
    """处理单个站点里的 ext 和 api 依赖"""
    api_url = site.get("api", "")
    if isinstance(api_url, str) and api_url.startswith("http") and (".js" in api_url or ".py" in api_url):
        site["api"] = await download_asset(session, api_url, "js", repo_base_url)
        
    ext_url = site.get("ext", "")
    if isinstance(ext_url, str) and ext_url.startswith("http"):
        site["ext"] = await download_asset(session, ext_url, "ext", repo_base_url)
    elif isinstance(ext_url, list):
        new_ext_list = []
        for u in ext_url:
            if isinstance(u, str) and u.startswith("http"):
                new_ext_list.append(await download_asset(session, u, "ext", repo_base_url))
            else:
                new_ext_list.append(u)
        site["ext"] = new_ext_list
        
    return site

def cleanup_old_assets():
    """清理历史遗留的旧版本 jar/js/ext"""
    print("\n=== 3. 开始执行历史旧版本清理 ===")
    for folder in ["jar", "js", "ext"]:
        local_files = glob.glob(f"{folder}/*")
        for file_path in local_files:
            if file_path.endswith(".gitkeep"):
                continue
            normalized_path = file_path.replace("\\", "/")
            if normalized_path not in active_assets:
                os.remove(file_path)
                stats["deleted"] += 1
                print(f"[🗑️ 自动清理旧版本] {normalized_path}")

async def fetch_valid_config(session, lines):
    """遍历种子列表，直到成功拉取到合法的 JSON 配置"""
    for line in lines:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        name = parts[0] if len(parts) > 1 else "默认源"
        urls = parts[1:] if len(parts) > 1 else [parts[0]]
        
        for target_url in urls:
            if not target_url.startswith("http"):
                continue
            print(f"\n=== 尝试拉取配置 [{name}]: {target_url} ===")
            try:
                async with session.get(target_url, timeout=15) as resp:
                    if resp.status != 200:
                        print(f"[⚠️ 状态码异常] {resp.status}，尝试下一个备用链接...")
                        continue
                    
                    raw_text = await resp.text(errors="ignore")
                    # 剔除可能存在的单行注释 // 后尝试解析
                    cleaned_lines = [l for l in raw_text.splitlines() if not l.strip().startswith("//")]
                    cleaned_text = "\n".join(cleaned_lines).strip()
                    
                    data = json.loads(cleaned_text)
                    if isinstance(data, dict) and ("sites" in data or "spider" in data):
                        print(f"[✅ 成功解析配置] 来源: {name}")
                        return data
                    else:
                        print("[⚠️ 内容不符合 TVBox 规范]，尝试下一个...")
            except json.decoder.JSONDecodeError:
                print(f"[⚠️ 返回非标准 JSON (可能触发防爬虫盾)]，前150字符: {raw_text[:150]!r}")
            except Exception as e:
                print(f"[⚠️ 网络请求异常] {e}")
                
    return None

async def main():
    repo_name = os.getenv("GITHUB_REPOSITORY", "YOUR_NAME/YOUR_REPO")
    repo_base_url = f"https://ghfast.top/https://raw.githubusercontent.com/{repo_name}/main"
    
    os.makedirs("output", exist_ok=True)
    for d in ["jar", "js", "ext"]:
        os.makedirs(d, exist_ok=True)
        
    if not os.path.exists(API_LINKS_FILE):
        print(f"❌ 未找到 {API_LINKS_FILE} 文件")
        return

    with open(API_LINKS_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not lines:
        print("❌ apilinks.txt 为空")
        return

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        data = await fetch_valid_config(session, lines)
        if not data:
            print("\n❌ 所有配置的种子接口均拉取失败，本次保留历史文件，安全退出。")
            return
            
        print("\n=== 1. 检测并更新 Spider JAR ===")
        spider_url = data.get("spider", "")
        if spider_url:
            data["spider"] = await download_asset(session, spider_url, "jar", repo_base_url)
            
        print("\n=== 2. 检测并更新 JS 和 EXT 依赖 ===")
        sites = data.get("sites", [])
        tasks = [localize_site(session, site, repo_base_url) for site in sites]
        data["sites"] = await asyncio.gather(*tasks)
        
        cleanup_old_assets()
        
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("\n🎉 自动更新检测完成！")
        print(f"📥 下载新 JAR: {stats['jar']} 个")
        print(f"📥 下载新 JS: {stats['js']} 个")
        print(f"📥 下载新 EXT: {stats['ext']} 个")
        print(f"🧹 清理旧文件: {stats['deleted']} 个")

if __name__ == "__main__":
    asyncio.run(main())
