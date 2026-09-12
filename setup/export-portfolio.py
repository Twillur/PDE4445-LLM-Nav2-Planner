"""Create a curated static-site export and slide-media bundle, without publishing."""
import argparse
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
PORTFOLIO=ROOT/"docs/portfolio"

def bundle():
    target=PORTFOLIO/"media/presentation-pack.zip"
    files=list((PORTFOLIO/"assets").glob("*.png"))+list((PORTFOLIO/"assets").glob("*.svg"))+list((PORTFOLIO/"assets").glob("*.pdf"))
    files += [PORTFOLIO/"media"/name for name in ["warehouse-overview.png","warehouse-goal.png","robot-detail.png","warehouse-navigation.mp4","warehouse-navigation.vtt","navigation-log.txt"]]
    files += [PORTFOLIO/"MEDIA.md",PORTFOLIO/"EVIDENCE.md",ROOT/"report/revised/main.pdf",ROOT/"report/revised/REVIEW_NOTES.md"]
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for file in files: archive.write(file,file.relative_to(ROOT).as_posix())
    print(f"Presentation pack: {len(files)} files, {target.stat().st_size/1e6:.2f} MB")

def site():
    output=ROOT/"_site"
    # A fresh destination prevents stale files from an older export leaking in.
    if output.exists(): raise SystemExit("_site already exists; inspect it before creating a fresh export.")
    directories=["docs/portfolio","docs/validation","report/revised","src","schema","dataset","map","prompts","ros2_ws/src/nl_nav2_executor","setup"]
    excluded={"frames","ros-logs","odometry","__pycache__","test-output"}
    suffixes={".html",".css",".js",".json",".jsonl",".csv",".md",".txt",".svg",".png",".jpg",".pdf",".mp4",".vtt",".zip",".py",".sh",".ps1",".tex",".bib",".dat",".yaml",".xml",".world",".pgm"}
    for directory in directories:
        for file in (ROOT/directory).rglob("*"):
            if not file.is_file() or file.is_symlink() or any(part in excluded for part in file.parts): continue
            if file.suffix not in suffixes or file.name.startswith("preview-"): continue
            dest=output/file.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(file,dest)
    # Evidence links are intentionally published; credentials and raw run storage are not.
    for name in ["20260801_145855_openai_gpt-4o-mini_v1.jsonl","20260801_151047_openai_gpt-4o-mini_v2.jsonl","20260807_154902_openai_gpt-4o-mini_v3.jsonl","l45_grades.json"]:
        dest=output/"results"/name; dest.parent.mkdir(exist_ok=True)
        shutil.copy2(ROOT/"results"/name,dest)
    (output/"index.html").write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=docs/portfolio/"><title>Robotics research portfolio</title><a href="docs/portfolio/">Open the research portfolio</a></html>',encoding="utf-8")
    (output/".nojekyll").touch()
    assert not list(output.rglob(".env"))
    print(f"Curated site exported to {output}; no publication performed.")

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--site",action="store_true"); args=parser.parse_args()
    bundle()
    if args.site: site()
