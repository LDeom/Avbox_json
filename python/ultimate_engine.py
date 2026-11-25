import json,asyncio,aiohttp,time,os,hashlib
API_LINKS_FILE="apilinks.txt"; OUTPUT_SINGLE="output/single_core.json"; OUTPUT_MULTI="output/multi_repo.json"; OUTPUT_DASHBOARD="output/dashboard.md"; TIMEOUT=5
BANNED_KEYWORDS=["广告","福利","充值","VIP","微信","公众号","发卡","购","买","赌场","澳门"]
base_config={"spider":"","wallpaper":"https://api.likepoems.com/img/bing","sites":[],"lives":[],"parses":[],"ijk":[{"group":"软解码","options":[{"category":4,"name":"opensles","value":"0"},{"category":4,"name":"framedrop","value":"1"},{"category":4,"name":"reconnect","value":"1"}]}]}
stats={"total_scanned":0,"l1_passed":0,"l2_passed":0,"ads_blocked":0,"jar_localized":0}
async def localize_jar(session,url,repo):
 if not url or not url.startswith("http"): return url
 try:
  async with session.get(url,timeout=10) as r:
   if r.status==200:
    b=await r.read(); h=hashlib.md5(b).hexdigest()[:8]; p=f"jar/spider_{h}.jar"
    if not os.path.exists(p):
     with open(p,"wb") as f:f.write(b)
     stats["jar_localized"]+=1
    return f"https://ghfast.top/https://raw.githubusercontent.com/{repo}/main/{p}"
 except Exception: pass
 return url
async def fetch(session,url):
 try:
  async with session.get(url,timeout=TIMEOUT) as r:
   if r.status==200:
    d=json.loads(await r.text());stats["total_scanned"]+=len(d.get("sites",[]));return d
 except Exception: pass
 return None
async def validate(session,s):
 n=s.get("name","");api=s.get("api","")
 if any(w in n for w in BANNED_KEYWORDS):stats["ads_blocked"]+=1;return None
 if not api or not api.startswith("http"):return s
 try:
  t=time.time()
  async with session.get(api,timeout=TIMEOUT) as r:
   if r.status==200:
    stats["l1_passed"]+=1;stats["l2_passed"]+=1;print(f"[HTTP200] {n} {int((time.time()-t)*1000)}ms");return s
 except Exception: pass
 return None
async def main():
 repo=os.getenv("GITHUB_REPOSITORY","LDeom/Avbox_json");os.makedirs("output",exist_ok=True);os.makedirs("jar",exist_ok=True)
 with open(API_LINKS_FILE,encoding="utf-8") as f:urls=[x.strip() for x in f if x.strip() and not x.startswith("#")]
 async with aiohttp.ClientSession() as session:
  data=await asyncio.gather(*(fetch(session,u) for u in urls));sites={};lives={};parses={};jar="https://raw.githubusercontent.com/FongMi/CatVodSpider/main/jar/custom_spider.jar"
  for d in data:
   if not d:continue
   if d.get("spider"):jar=d["spider"]
   for k,field in ((sites,"sites"),(lives,"lives"),(parses,"parses")):
    for x in d.get(field,[]):
     name=x.get("name")
     if name and name not in k:k[name]=x
  valid=[x for x in await asyncio.gather(*(validate(session,s) for s in sites.values())) if x]
  base_config["spider"]=await localize_jar(session,jar,repo);base_config["sites"]=valid;base_config["lives"]=list(lives.values());base_config["parses"]=list(parses.values())
  with open(OUTPUT_SINGLE,"w",encoding="utf-8") as f:json.dump(base_config,f,ensure_ascii=False,indent=2)
  link=f"https://ghfast.top/https://raw.githubusercontent.com/{repo}/main/{OUTPUT_SINGLE}"
  with open(OUTPUT_MULTI,"w",encoding="utf-8") as f:json.dump({"urls":[{"url":link,"name":"五合一聚合仓"}]},f,ensure_ascii=False,indent=2)
  with open(OUTPUT_DASHBOARD,"w",encoding="utf-8") as f:f.write("# 聚合体检\n\n"+"\n".join(f"- {k}: {v}" for k,v in stats.items()))
if __name__=="__main__":asyncio.run(main())
