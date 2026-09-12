"""Capture public product-page views for a dated, attributed hardware study."""
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(__file__).resolve().parent.parent / "docs/portfolio/media/hardware"
SOURCES = [
    ("waffle-pi", "https://en.robotis.com/shop_en/item.php?it_id=901-0119-302", "TURTLEBOT3 Waffle Pi"),
    ("jetson-orin", "https://www.seeedstudio.com/NVIDIAr-Jetson-Orintm-Nano-Super-Developer-Kit-Bundle.html", "NVIDIA"),
    ("rplidar", "https://www.dfrobot.com/product-1125.html", "RPLIDAR A1M8"),
    ("raspberry-pi", "https://www.adafruit.com/product/5813", "Raspberry Pi 5"),
]

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True)
        async def capture(slug,url,title):
            page=await browser.new_page(viewport={"width":1280,"height":1200},device_scale_factor=1)
            try:
                await page.goto(url,wait_until="domcontentloaded",timeout=45000)
                headings=page.get_by_role("heading").filter(has_text=title)
                await headings.first.wait_for(state="visible",timeout=15000) # product title may repeat in sticky purchase panel
                heading=headings.first
                await heading.evaluate("el => window.scrollTo(0, Math.max(0, el.getBoundingClientRect().top + window.scrollY - 160))")
                try:
                    await page.wait_for_load_state("networkidle", timeout=20000)
                except Exception:
                    pass # vendor analytics may keep connections open
                if slug == "rplidar":
                    global_site=page.get_by_text("Global Site",exact=True)
                    if await global_site.is_visible():
                        await global_site.click()
                        await page.get_by_text("Please select the site you would like to browse:",exact=True).wait_for(state="hidden")
                await page.screenshot(path=str(OUT/f"{slug}.png"),animations="disabled")
                return {"id":slug,"source":url,"resolved_url":page.url,"captured_utc":datetime.now(timezone.utc).isoformat(),"status":"captured","image":f"{slug}.png","owner":"Original vendor; screenshot retained for attributed product comparison"}
            except Exception as exc:
                return {"id":slug,"source":url,"status":"unavailable","error":str(exc).splitlines()[0]}
            finally:
                await page.close()
        selected=[s for s in SOURCES if not sys.argv[1:] or s[0] in sys.argv[1:]]
        results=await asyncio.gather(*(capture(*s) for s in selected))
        if sys.argv[1:] and (OUT/"sources.json").exists():
            existing=json.loads((OUT/"sources.json").read_text(encoding="utf-8"))
            updated={r["id"]:r for r in results}
            results=[updated.get(r["id"],r) for r in existing]
        (OUT/"sources.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
        print(json.dumps(results,indent=2))
        await browser.close()

asyncio.run(main())
