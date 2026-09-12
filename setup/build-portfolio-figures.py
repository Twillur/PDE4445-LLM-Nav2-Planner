"""Export presentation figures from archived data and actual warehouse geometry.

Run with the project virtual environment after installing Matplotlib.
Only docs/portfolio/assets is written; archived results are read-only.
"""
import hashlib
import json
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/portfolio/assets"
OUT.mkdir(parents=True, exist_ok=True)
INK, MUTED, TEAL, ORANGE, BLUE = "#162b3b", "#627384", "#087f8c", "#d56b35", "#4777ba"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "text.color": INK, "axes.labelcolor": INK,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#cbd6df", "svg.fonttype": "none",
                     "savefig.facecolor": "#ffffff"})

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def save(fig, name):
    for ext in ("svg", "png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=190, bbox_inches="tight", pad_inches=.25)
    plt.close(fig)

world = ET.parse(ROOT / "ros2_ws/src/nl_nav2_executor/worlds/warehouse.world")
geometry = []
for model in world.findall(".//model"):
    pose, size = model.findtext("pose"), model.findtext("link/collision/geometry/box/size")
    if pose and size:
        x, y, *_ = map(float, pose.split())
        w, h, _ = map(float, size.split())
        geometry.append((x-w/2, y-h/2, w, h, model.attrib["name"]))
locations = read("map/warehouse_map.json")["locations"]

def floor(ax):
    ax.set_facecolor("#f3f6f8")
    for x, y, w, h, name in geometry:
        ax.add_patch(Rectangle((x,y), w,h, color="#bac6d0" if "shelf" in name else "#718391"))
    ax.set(xlim=(-.5,20.5), ylim=(-.5,20.5), xlabel="East / x (m)", ylabel="North / y (m)")
    ax.set_aspect("equal")
    ax.set_xticks([0,5,10,15,20]); ax.set_yticks([0,5,10,15,20])
    ax.grid(alpha=.13)
    for i, x in enumerate((6,9,12), 1):
        ax.text(x,9,f"AISLE {i}", ha="center", rotation=90, fontsize=8, color=MUTED)

fig, (ax, legend) = plt.subplots(1,2,figsize=(13,7),gridspec_kw={"width_ratios":[1.3,1]})
floor(ax); legend.axis("off")
for i, (name, pos) in enumerate(locations.items(), 1):
    ax.scatter(pos["x"],pos["y"],s=28,color=TEAL,zorder=3)
    # Two names share the southwest coordinate; show their identifiers together.
    if name == "corner_sw":
        continue
    label = "01 / 13" if name == "charging_dock" else f"{i:02d}"
    ax.annotate(label,(pos["x"],pos["y"]),xytext=(4,5),textcoords="offset points",fontsize=8)
for i, (name,pos) in enumerate(locations.items(),1):
    legend.text(0,1-i*.047,f"{i:02d}  {name}",fontsize=10,fontfamily="DejaVu Sans Mono")
fig.suptitle("20 names. One shared map.",fontsize=23,ha="left",x=.08,weight="bold")
fig.text(.08,.005,"Generated from warehouse_map.json and the Gazebo world's collision geometry. The occupancy map is scripted, not SLAM.",fontsize=10,color=MUTED)
save(fig,"semantic-map")

run = "docs/validation/gazebo-20260911T213643Z"
fig, axes = plt.subplots(1,3,figsize=(15,5.7))
route_data = []
for ax, case, title, color in zip(axes,["v2-L1-01-trial0","v2-L2-01-trial0","v2-L3-01-trial0"],
                                ["L1 · Direct / 1 goal","L2 · East wall / 3 goals","L3 · Patrol / 5 goals"],[TEAL,BLUE,ORANGE]):
    floor(ax)
    points=read(f"{run}/{case}/trajectory-sampled.json")
    plan=read(f"{run}/{case}/plan.json")
    ax.plot([p["x"] for p in points],[p["y"] for p in points],color=color,lw=2.4)
    for i,step in enumerate(plan["plan"],1):
        if step["action"] != "navigate": continue
        p=locations[step["target"]]
        ax.scatter(p["x"],p["y"],s=80,color=color,edgecolor="white",zorder=5)
        ax.annotate(str(i),(p["x"],p["y"]),xytext=(6,5),textcoords="offset points",weight="bold",color=color)
    ax.set_title(title,loc="left",weight="bold",pad=15)
    route_data.append({"case":case,"title":title,"points":points,"plan":plan})
fig.suptitle("Where the robot actually travelled",x=.08,ha="left",fontsize=23,weight="bold")
fig.subplots_adjust(top=.79,bottom=.19,wspace=.25)
fig.text(.08,.035,"Recorded odometry · three selected saved-plan replays · 9/9 goals corroborated within 0.25 m\nThese runs predate the later runtime corrections; they do not test conditional fallback behaviour.",fontsize=10,color=MUTED)
save(fig,"recorded-routes")
(OUT/"routes.json").write_text(json.dumps({"locations":locations,"geometry":geometry,"runs":route_data}),encoding="utf-8")

versions={}
for version,file in [("v1","20260801_145855_openai_gpt-4o-mini_v1.jsonl"),("v2","20260801_151047_openai_gpt-4o-mini_v2.jsonl")]:
    rows=[json.loads(line) for line in (ROOT/"results"/file).read_text(encoding="utf-8").splitlines() if line.strip()]
    versions[version]=rows
scores=[sum(r["level"]==level and r["parse_ok"] and r["schema_error"] is None and r["map_error"] is None and r["semantic"]=="pass" for r in versions["v2"]) for level in [1,2,3]]
assert scores == [58,57,57]
fig,(a,b)=plt.subplots(1,2,figsize=(12,5.7),gridspec_kw={"width_ratios":[3,2]})
for ax,labels,values,counts,color,title in [(a,["L1\nDirect","L2\nSpatial","L3\nMulti-step"],[n/60*100 for n in scores],[f"{n}/60" for n in scores],TEAL,"Automatic matching · 60 records per level"),
    (b,["L4\nConditional","L5\nAmbiguous"],[55,85],["11/20","17/20"],ORANGE,"Item summary · 20 items per level")]:
    ax.bar(labels,values,color=color,width=.55)
    ax.set_ylim(0,112); ax.set_yticks([0,25,50,75,100]); ax.set_title(title,loc="left",fontsize=11)
    ax.grid(axis="y",alpha=.15); ax.set_axisbelow(True)
    for i,(v,n) in enumerate(zip(values,counts)): ax.text(i,v+3,f"{v:.1f}%\n{n}",ha="center",fontsize=11,weight="bold")
a.set_ylabel("Strict semantic success (%)")
fig.suptitle("A reliability dip at conditional instructions",x=.08,ha="left",fontsize=22,weight="bold")
fig.subplots_adjust(top=.76,bottom=.24,wspace=.3)
fig.text(.08,.035,"Different scoring units: do not treat these bars as one pooled benchmark. L5 may succeed by asking for clarification.\nL4 versus L5: descriptive gap; Fisher two-sided p = 0.082. Mechanism evidence matters more than the raw difference.",fontsize=10,color=MUTED)
save(fig,"reliability")

fig,ax=plt.subplots(figsize=(10,5.2))
for offset,version,color in [(-.18,"v1","#aebac4"),(.18,"v2",TEAL)]:
    vals=[sum(r["level"]==level and r["parse_ok"] and r["schema_error"] is None and r["map_error"] is None and r["semantic"]=="pass" for r in versions[version])/3 for level in [1,2,3]]
    bars=ax.bar(np.arange(3)+offset,vals,width=.34,color=color,label=version)
    ax.bar_label(bars,fmt="%.1f",padding=4)
ax.set(xticks=range(3),xticklabels=["L1 · Direct","L2 · Spatial","L3 · Multi-step"],ylim=(0,22),ylabel="Mean successful commands / 20")
ax.legend(frameon=False); ax.grid(axis="y",alpha=.12); ax.set_axisbelow(True)
ax.set_title("Prompt refinement: 85.0% → 95.6% on L1–L3",loc="left",pad=25,fontsize=19,weight="bold")
fig.text(.08,-.02,"153/180 → 172/180 automatic passes. Three trials per command; seven L1–L3 commands improved, none regressed.",fontsize=10,color=MUTED)
save(fig,"prompt-comparison")

lat=[r["latency_s"] for r in versions["v2"]]
fig,ax=plt.subplots(figsize=(10,4.6))
ax.hist(lat,bins=24,color=TEAL,edgecolor="white")
for value,label,color in [(statistics.median(lat),"Median 2.08 s",INK),(statistics.quantiles(lat,n=100,method="exclusive")[94],"p95 3.63 s",ORANGE)]:
    ax.axvline(value,color=color,ls="--",lw=1.7,label=label)
ax.set(xlabel="Recorded planner-call latency (s)",ylabel="Records")
ax.legend(frameon=False); ax.set_title("One model call, typically about two seconds",loc="left",pad=20,fontsize=19,weight="bold")
fig.text(.08,-.04,"v2 · n=300 · mean 2.23 s · exclusive-quantile p95. This is translation latency, not robot mission duration.",fontsize=10,color=MUTED)
save(fig,"latency")

def diagram(title,subtitle,filename,boxes,edges,size=(14,6)):
    fig,ax=plt.subplots(figsize=size)
    ax.set(xlim=(0,14),ylim=(0,6)); ax.axis("off")
    for x,y,w,h,text,color in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.04,rounding_size=.12",facecolor=color,edgecolor="none"))
        ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=11,color="white",linespacing=1.6)
    for x1,y1,x2,y2,label in edges:
        ax.annotate("",xy=(x2,y2),xytext=(x1,y1),arrowprops={"arrowstyle":"->","color":MUTED,"lw":1.6})
        if label: ax.text((x1+x2)/2,(y1+y2)/2+.15,label,ha="center",fontsize=9,color=MUTED)
    ax.text(0,5.8,title,fontsize=23,weight="bold")
    ax.text(0,.1,subtitle,fontsize=10,color=MUTED,linespacing=1.5)
    save(fig,filename)

diagram("From typed instruction to robot motion", "Current runtime, 12 September 2026. The August evaluation used its own archived validators.\nJSON describes intent; the executor and Nav2 handle motion. Coordinate output is excluded; incorrect names and plans remain possible.","architecture",[
    (0,3.1,2,1.1,"Typed English\noperator input",INK),(2.5,3.1,2,1.1,"One LLM call\ngpt-4o-mini",TEAL),(5,3.1,1.8,1.1,"JSON plan\nnamed targets",INK),
    (7.3,3.1,2,1.1,"Execution gate\nstructure + map",TEAL),(9.8,3.1,1.8,1.1,"Executor\nfile / stdin",INK),(12.1,3.1,1.8,1.1,"Nav2\nGazebo robot",TEAL),
    (5,1.1,1.8,1,"Clarification\nno movement",ORANGE),(7.3,1.1,2,1,"Semantic map\n20 locations",BLUE)],
    [(2,3.65,2.5,3.65,""),(4.5,3.65,5,3.65,""),(6.8,3.65,7.3,3.65,""),(9.3,3.65,9.8,3.65,""),(11.6,3.65,12.1,3.65,""),(5.9,3.1,5.9,2.1,"defer"),(8.3,2.1,8.3,3.1,"")])
diagram("The missing branch, made explicit", "Saved L4-12 example. v3 adds a fallback field plus prompt instructions.\nThe new executor passes controlled software checks; obstacle-triggered Gazebo fallback validation and full v3 semantic grading remain outstanding.","fallback",[
    (.2,3.6,3.8,1,"v2 · unconditional sequence\nA then B",ORANGE),(.2,1.7,3.8,1,"Condition in a comment\nhas no control-flow effect",INK),
    (5,3.6,3.8,1,"v3 · primary succeeds\nvisit A only",TEAL),(5,1.7,3.8,1,"v3 · primary fails\ntry B once",BLUE),
    (10,3.6,3.8,1,"A and B both fail\nreport incomplete",INK),(10,1.7,3.8,1,"Unknown fallback name\nreject before movement",ORANGE)],[(2.1,3.6,2.1,2.7,""),(6.9,3.6,6.9,2.7,"otherwise")])
diagram("A proposed physical robot", "Future hardware concept; nothing on this diagram has been purchased or validated as a complete assembly.\nKeep cloud language planning initially. A Jetson is an optional compute upgrade for later perception or local-model experiments.","hardware-architecture",[
    (.1,3.5,2.3,1,"Operator laptop\ntyped command",INK),(3,3.5,2.3,1,"Cloud model API\nJSON response",TEAL),(6,3.5,2.8,1,"Onboard Linux + ROS2\nPi / optional Orin",INK),(10,3.5,3.5,1,"OpenCR / motor control\nencoders + drive motors",BLUE),
    (6,1.3,2.8,1,"LiDAR + wheel odometry\nIMU for localisation",TEAL),(10,1.3,3.5,1,"Battery + protected rails\nphysical stop + mounts",ORANGE)],
    [(2.4,4,3,4,""),(5.3,4,6,4,""),(8.8,4,10,4,"USB / serial"),(7.4,2.3,7.4,3.5,"sensors"),(11.7,2.3,11.7,3.5,"power")])

manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in (".svg",".png",".pdf",".json")}
(OUT/"figure-hashes.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(f"Exported eight figure families, route data and hashes to {OUT}")
