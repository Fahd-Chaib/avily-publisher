import json, subprocess, os
V="/home/claude/avily"
S="/tmp/claude-0/-home-claude/f66ff47c-2cb9-56b1-bee9-bed7cbbc7ee0/scratchpad/specs"; os.makedirs(S,exist_ok=True)
NOTES={"04":("Prune Ambrée","prune noire, ambre et bois de vanille","#prune #vanille"),
       "26":("Pistache Caramel","pistache et caramel salé","#pistache #caramel"),
       "86":("Fruit du Dragon","jasmin du Brésil et fruit du dragon rose","#jasmin #fruitdudragon"),
       "95":("Violette Vanille","orchidée vanille, violette sucrée et bois de santal","#violette #vanille")}
WEEK=[("2026-10-13","n26_caramel","26","Une brume qui sent la pistache caramel ?","Team gourmand ou team frais ?","AVILY_n26_caramel_hook.mp4"),
      ("2026-10-14","n95_violettes","95","Violette sucrée, vanille douce.","Team 95 ou team 86 ?","AVILY_n95_violettes_hook.mp4"),
      ("2026-10-15","n04_fumee","04","Chaude, ambrée, un peu mystérieuse.","Tu l'imagines sur toi ?","AVILY_n04_fumee_hook.mp4"),
      ("2026-10-16","n86_jasmin","86","Jasmin et fruit du dragon.","Tu la mets après la douche ou avant de sortir ?","AVILY_n86_jasmin_hook.mp4"),
      ("2026-10-17","n26_pluie","26","Pistache. Caramel. Sur ta peau.","Team gourmand ou team frais ?","AVILY_n26_pluie_hook.mp4"),
      ("2026-10-18","n04_zoom","04","59 DH, tu paies à la réception.","Team 04 ou team 26 ?","AVILY_n04_zoom_hook.mp4")]
for day,slug,n,hook,q,f in WEEK:
    name,notes,tags=NOTES[n]
    base=f"Brume parfumée 250 ml · 59 DH · Paiement à la livraison partout au Maroc 🇲🇦"
    ig=(f"N°{n} {name} : {hook}\n{q} Dis-le en commentaire 👇\n\n"
        f"Notes : {notes}.\n{base}\nCommande par le lien dans la bio.\n\n"
        f"#brumeparfumee #bodymist #parfummaroc #beautemaroc {tags} #avily")
    tt=(f"N°{n} {name} 🇲🇦 {q} 👇\nBrume parfumée (body mist) {notes} · 250 ml · 59 DH · paiement à la livraison partout au Maroc. "
        f"Commande sur avily.youcan.store\n#brumeparfumee #bodymist #parfummaroc #beautemaroc {tags}")
    yt_title=f"Brume parfumée {name} N°{n} · 59 DH au Maroc #Shorts"
    yt_desc=(f"{hook} La brume parfumée N°{n} {name} d'AVILY : {notes}.\n\n"
             f"✔ 250 ml · 59 DH\n✔ Paiement à la livraison, partout au Maroc\n✔ Duo 99 DH · Trio 135 DH · Coffret des 4 : 169 DH\n\n"
             f"Commander : https://avily.youcan.store\n\n"
             f"Une brume (body mist) est plus légère qu'un parfum : elle se revaporise dans la journée.\n\n"
             f"#brumeparfumee #bodymist #parfummaroc #Shorts")
    spec={"slug":slug,"publish_at":f"{day}T20:00:00","timezone":"Africa/Casablanca",
          "platforms":["youtube","instagram","tiktok"],
          "instagram":{"caption":ig},"tiktok":{"caption":tt},
          "youtube":{"title":yt_title[:100],"description":yt_desc,
                     "tags":["brume parfumée","body mist","parfum Maroc","brume parfumée Maroc",name.lower(),f"N°{n}","AVILY","parfum pas cher","beauté Maroc"]}}
    sp=f"{S}/{slug}.json"; json.dump(spec,open(sp,"w"),ensure_ascii=False,indent=2)
    subprocess.run(["python3","tools/enqueue.py",f"{V}/{f}",sp],check=True)
