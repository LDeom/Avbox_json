import json
import asyncio
import aiohttp
import time
import os
import hashlib
import re

API_LINKS_FILE = "apilinks.txt"
OUTPUT_SINGLE = "output/single_core.json"
OUTPUT_MULTI = "output/multi_repo.json"
OUTPUT_LIVE = "output/live_only.txt"
OUTPUT_DASHBOARD = "output/dashboard.md"
TIMEOUT = 5

BANNED_KEYWORDS = ["广告", "福利", "充值", "VIP", "微信", "公众号", "发卡", "购", "买", "赌场", "澳门"]

base_config = {
    "spider": "",
    "wallpaper": "https://api.likepoems.com/img/bing",
    "sites": [],
    "lives": [],
    "parses": [],
    "ijk": [
        {"group": "软解码", "options": [{"category": 4, "name": "opensles", "value": "0"}, {"category": 4, "name": "framedrop", "value": "1"}, {"category": 4, "name": "reconnect", "value": "1"}]}
    ]
}

stats = {"total_scanned": 0, "l1_passed": 0, "l2_passed": 0, "ads_blocked": 0, "jar_localized": 0}

async def localize_jar(session, jar_url, repo_name="YOUR_GITHUB_REPO"):
    if not jar_url or not jar_url.startswith("http"):
        return jar_url
    try:
        async with session.get(jar_url, timeout=10) as resp:
            if resp.status == 200:
                content = await resp.read()
                md5_hash = hashlib.md5(content).hexdigest()[:8]
                local_filename = f"jar/spider_{md5_hash}.jar"
                if not os.path.exists(local_filename):
                    with open(local_filename, "wb") as f:
                        f.write(content)
                    stats["jar_localized"] += 1
                return f"https://ghfast.top/https://raw.githubusercontent.com/{repo_name}/main/{local_filename}"
    except Exception:
        pass
    return jar_url

async def fetch_and_extract(session, name, url):
    try:
        async with session.get(url, timeout=TIMEOUT) as resp:
            if resp.status == 200:
                data = json.loads(await resp.text())
                stats["total_scanned"] += len(data.get("sites", []))
                return data
    except Exception:
        pass
    return None

async def l1_l2_validate(session, site):
    name = site.get("name", "")
    api_url = site.get("api", "")
    if any(banned in name for banned in BANNED_KEYWORDS):
        stats["ads_blocked"] += 1
        return None
    if not api_url or not api_url.startswith("http"):
        return site
    try:
        start_time = time.time()
        async with session.get(api_url, timeout=TIMEOUT) as response:
            if response.status == 200:
                stats["l1_passed"] += 1
                delay = int((time.time() - start_time) * 1000)
                stats["l2_passed"] += 1
                print(f"[L2 pass] {name} | delay: {delay}ms")
                return site
    except Exception:
        pass
    return None

async def main():
    repo_name = os.getenv("GITHUB_REPOSITORY", "YOUR_NAME/YOUR_REPO")
    os.makedirs("output", exist_ok=True)
    os.makedirs("jar", exist_ok=True)
    with open(API_LINKS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    async with aiohttp.ClientSession() as session:
        raw_jsons = await asyncio.gather(*(fetch_and_extract(session, f"source_{i}", url) for i, url in enumerate(urls)))
        all_sites, all_lives, all_parses = {}, {}, {}
        main_jar = "https://raw.githubusercontent.com/FongMi/CatVodSpider/main/jar/custom_spider.jar"
        for data in raw_jsons:
            if not data:
                continue
            if data.get("spider"):
                main_jar = data["spider"]
            for field, bucket in (("sites", all_sites), ("lives", all_lives), ("parses", all_parses)):
                for item in data.get(field, []):
                    name = item.get("name")
                    if name and name not in bucket:
                        bucket[name] = item

        valid_sites = [s for s in await asyncio.gather(*(l1_l2_validate(session, s) for s in all_sites.values())) if s]
        base_config["spider"] = await localize_jar(session, main_jar, repo_name)
        base_config["sites"] = valid_sites
        base_config["lives"] = list(all_lives.values())
        base_config["parses"] = list(all_parses.values())

        with open(OUTPUT_SINGLE, "w", encoding="utf-8") as f:
            json.dump(base_config, f, ensure_ascii=False, indent=2)
        link = f"https://ghfast.top/https://raw.githubusercontent.com/{repo_name}/main/{OUTPUT_SINGLE}"
        with open(OUTPUT_MULTI, "w", encoding="utf-8") as f:
            json.dump({"urls": [{"url": link, "name": "五合一终极旗舰仓"}]}, f, ensure_ascii=False, indent=2)
        with open(OUTPUT_DASHBOARD, "w", encoding="utf-8") as f:
            f.write("## 聚合体检面板\n\n")
            for key, value in stats.items():
                f.write(f"- {key}: {value}\n")
        print("Aggregation complete.")

if __name__ == "__main__":
    asyncio.run(main())
