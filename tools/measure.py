import csv, os, json, re, collections
csv.field_size_limit(10**9)
G="/home/victor/Games/starsector"
SPEC={  # rel -> columnas traducibles (derivado del diff PT)
 "data/campaign/abilities.csv":["name","desc"],
 "data/campaign/commodities.csv":["name"],
 "data/campaign/industries.csv":["name","desc"],
 "data/campaign/market_conditions.csv":["name","desc"],
 "data/campaign/rules.csv":["text","options"],
 "data/campaign/special_items.csv":["name","desc"],
 "data/campaign/submarkets.csv":["name","desc"],
 "data/characters/personalities.csv":["name","desc"],
 "data/characters/skills/aptitude_data.csv":["name","description"],
 "data/characters/skills/skill_data.csv":["name","description"],
 "data/hullmods/hull_mods.csv":["name","desc"],
 "data/hulls/ship_data.csv":["name","designation","logistics n/a reason"],
 "data/shipsystems/ship_systems.csv":["name"],
 "data/strings/descriptions.csv":["text1","text2","text3","text4","text5"],
 "data/weapons/weapon_data.csv":["name","primaryRoleStr","speedStr","trackingStr","accuracyStr","customPrimary","customPrimaryHL","customAncillary"],
}
tot_s=tot_c=0; uniq=set()
print(f"{'archivo':50s} {'strings':>8s} {'chars':>9s}")
for rel,cols in SPEC.items():
    p=os.path.join(G,rel)
    with open(p,encoding="cp1252",newline="") as f: rr=list(csv.reader(f))
    hdr=rr[0]; idx=[hdr.index(c) for c in cols if c in hdr]
    s=c=0
    for row in rr[1:]:
        for i in idx:
            if i<len(row):
                v=row[i].strip()
                if v and not v.isdigit(): s+=1; c+=len(v); uniq.add(v)
    print(f"{rel:50s} {s:8d} {c:9d}"); tot_s+=s; tot_c+=c
print(f"{'TOTAL CSV':50s} {tot_s:8d} {tot_c:9d}   unicos={len(uniq)}")
