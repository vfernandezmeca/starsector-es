import json, os, re, difflib, collections
G="/home/victor/Games/starsector"; D="/home/victor/Downloads/PTBR 154 0.0.7 2026-06-21T14-52Z yvgMZtERg/portugues-brasileiro"
def rel_all(ext):
    out=[]
    for root,_,fs in os.walk(D):
        for fn in fs:
            r=os.path.relpath(os.path.join(root,fn),D)
            if r.endswith(ext) and os.path.exists(os.path.join(G,r)): out.append(r)
    return sorted(out)
def rd(p): return open(p,encoding="utf-8",errors="replace").read().splitlines()

# 1) which JSON keys changed (line-based heuristic: capture key on changed lines)
for ext in (".json",".faction",".variant",".skill",".txt"):
    keys=collections.Counter(); nfiles=0; nlines=0
    for r in rel_all(ext):
        a,b=rd(os.path.join(G,r)),rd(os.path.join(D,r)); nfiles+=1
        for ln in difflib.unified_diff(a,b,n=0,lineterm=""):
            if ln.startswith("-") and not ln.startswith("---"):
                nlines+=1
                m=re.match(r'\s*"([^"]+)"\s*:',ln[1:])
                keys[m.group(1) if m else "<no-key>"]+=1
    print(f"\n=== {ext}  files={nfiles} changed_lines={nlines} ===")
    for k,v in keys.most_common(25): print(f"  {v:5d}  {k}")
