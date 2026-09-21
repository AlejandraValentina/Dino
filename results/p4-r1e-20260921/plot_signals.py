import gzip,json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
here=Path(__file__).resolve().parent
old=here.parent/"p4-r1-20260921/run/artifacts/cases"
paths=[old/f"blowdown_N{n}_CFL0.4.json.gz" for n in (100,200,400)]
paths.append(here/"run/artifacts/cases/blowdown_N800_CFL0.4.json.gz")
fig,axes=plt.subplots(2,1,figsize=(10,8),layout="constrained")
for path in paths:
 row=json.loads(gzip.decompress(path.read_bytes()));s=row["signal"]
 for ax in axes:ax.plot([t*1000 for t in s["times"]],[p/1000 for p in s["pressure"]],label=f"N={row['N']}",linewidth=1.2)
axes[0].set_title("P4-R1E · Descarga completa · x=0,1 m · CFL 0,4")
axes[1].set_title("Detalle poscierre · misma señal, sin modificar el observable")
axes[1].set_xlim(190/18,220/18);axes[1].set_ylim(100.15,101.35)
for ax in axes:
 ax.axvline(190/18,color="gray",linestyle=":",label="Cierre 270°")
 ax.set_xlabel("Tiempo físico [ms]");ax.set_ylabel("Presión [kPa]");ax.grid(alpha=.2);ax.legend(fontsize=8)
for ext in ("png","svg"):
 path=here/f"signals.{ext}";fig.savefig(path,dpi=150)
 if ext=="svg":path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines())+"\n",encoding="utf-8")
