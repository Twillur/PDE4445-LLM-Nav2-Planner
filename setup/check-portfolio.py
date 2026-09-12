"""Check the curated site with a real browser, plus local link integrity."""
import argparse
import asyncio
import functools
import json
import threading
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from playwright.async_api import async_playwright, expect

ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/"_site"
OUTPUT=ROOT/"docs/portfolio/test-output"

class References(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ("href","src","poster") and value: self.links.append(value)

def check_links():
    checked=0
    for source in (SITE/"docs/portfolio").glob("*.html"):
        parser=References(); parser.feed(source.read_text(encoding="utf-8"))
        for url in parser.links:
            parts=urlsplit(url)
            if parts.scheme or not parts.path: continue
            target=(source.parent/unquote(parts.path)).resolve()
            assert target.is_relative_to(SITE.resolve()), (source,url,"outside site")
            assert target.exists(), (source,url,"missing local target")
            checked+=1
    return checked

class PortfolioPage:
    def __init__(self,page,base):
        self.page=page; self.base=base
        self.route=page.get_by_label("Choose a recorded route")
        self.play=page.get_by_role("button",name="Play replay",exact=True)
    async def open(self):
        await self.page.goto(self.base+"/docs/portfolio/",wait_until="networkidle")
        await expect(self.page.get_by_role("heading",name="From instructions to robot motion.")).to_be_visible()
    async def check_interactions(self):
        await self.page.get_by_role("button",name="Maps",exact=True).click()
        await expect(self.page.locator("#filter-count")).to_have_text("2 figures")
        await self.page.get_by_role("button",name="Results",exact=True).click()
        await expect(self.page.locator("#filter-count")).to_have_text("3 figures")
        await self.page.get_by_role("button",name="All figures",exact=True).click()
        await self.route.select_option("0")
        await expect(self.page.locator("#route-targets li")).to_have_count(1)
        await self.play.click()
        await self.page.wait_for_function("Number(document.getElementById('route-progress').value)>0")
        await self.page.get_by_role("button",name="Pause replay",exact=True).click()
        await self.route.select_option("2")
        await expect(self.page.locator("#route-targets li")).to_have_count(5)
        await self.page.get_by_label("Replay position").evaluate("el=>{el.value=1000;el.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert await self.page.get_by_label("Replay position").input_value()=="1000"
        async with self.page.expect_download() as download:
            await self.page.get_by_role("link",name="Download presentation pack",exact=False).click()
        downloaded=await download.value
        assert downloaded.suggested_filename=="presentation-pack.zip"
        await self.page.evaluate("window.scrollTo(0,0)")

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

async def check_live_links(request,base):
    targets=set()
    for name in ("index.html","hardware.html","reproduce.html"):
        url=base+"/docs/portfolio/"+name
        response=await request.get(url)
        assert response.ok,(url,response.status)
        parser=References(); parser.feed(await response.text())
        for link in parser.links:
            parts=urlsplit(link)
            if parts.scheme or not parts.path: continue
            target=urljoin(url,link).split("#",1)[0]
            assert target.startswith(base+"/"),(url,link,"outside site")
            targets.add(target)
    semaphore=asyncio.Semaphore(8)
    async def check(url):
        async with semaphore:
            response=await request.head(url)
            assert response.ok,(url,response.status)
    await asyncio.gather(*(check(url) for url in sorted(targets)))
    return len(targets)

async def main(live_base=None):
    OUTPUT.mkdir(parents=True,exist_ok=True)
    server=None
    if live_base:
        base=live_base.rstrip("/")
        link_count=None
    else:
        link_count=check_links()
        server=ThreadingHTTPServer(("127.0.0.1",0),functools.partial(QuietHandler,directory=str(SITE)))
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        base=f"http://127.0.0.1:{server.server_port}"
    try:
        async with async_playwright() as p:
            if live_base:
                request=await p.request.new_context()
                try:
                    link_count=await check_live_links(request,base)
                finally:
                    await request.dispose()
            browser=await p.chromium.launch(headless=True)
            async def check(name,width,height,path,interactions=False):
                context=await browser.new_context(viewport={"width":width,"height":height},accept_downloads=True,reduced_motion="reduce")
                await context.tracing.start(screenshots=True,snapshots=True)
                page=await context.new_page(); errors=[]
                page.on("pageerror",lambda exc: errors.append(str(exc)))
                try:
                    if interactions:
                        view=PortfolioPage(page,base); await view.open(); await view.check_interactions()
                    else:
                        await page.goto(base+path,wait_until="networkidle")
                        await expect(page.get_by_role("heading",level=1)).to_be_visible()
                    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth"),f"Horizontal overflow: {name}"
                    assert not errors,errors
                    # Trigger lazy images throughout the page before a complete screenshot.
                    await page.evaluate("document.querySelectorAll('img').forEach(img=>img.loading='eager')")
                    await page.wait_for_function("Array.from(document.images).every(img=>img.complete && img.naturalWidth>0)")
                    await page.screenshot(path=str(OUTPUT/f"{name}.png"),full_page=True,animations="disabled")
                    if name=="desktop" and not live_base:
                        await page.screenshot(path=str(ROOT/"docs/portfolio/media/portfolio-preview.png"),animations="disabled")
                    return {"case":name,"passed":True,"console_errors":errors}
                finally:
                    await context.tracing.stop(path=str(OUTPUT/f"{name}-trace.zip")); await context.close()
            results=await asyncio.gather(
                check("desktop",1440,1000,"/docs/portfolio/",True),
                check("mobile",390,844,"/docs/portfolio/",True),
                check("hardware",1440,1000,"/docs/portfolio/hardware.html"),
                check("reproduce",390,844,"/docs/portfolio/reproduce.html"),
            )
            await browser.close()
        summary={"local_html_references_checked":link_count,"browser_checks":results,"scope":"Curated static export served locally; no GitHub deployment performed."}
        if live_base:
            summary={"live_unique_references_checked":link_count,"browser_checks":results,"scope":"Published GitHub Pages site","base_url":base}
        destination=OUTPUT/"live-verification.json" if live_base else ROOT/"docs/portfolio/verification.json"
        destination.write_text(json.dumps(summary,indent=2),encoding="utf-8")
        print(json.dumps(summary,indent=2))
    finally:
        if server:
            server.shutdown(); server.server_close()

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",help="Check an already deployed site instead of the local export")
    asyncio.run(main(parser.parse_args().base_url))
