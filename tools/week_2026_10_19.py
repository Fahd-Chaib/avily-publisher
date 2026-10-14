import json, subprocess, os
V="/home/claude/avily"
S="/tmp/claude-0/-home-claude-avily-publisher/f66ff47c-2cb9-56b1-bee9-bed7cbbc7ee0/scratchpad/specs"; os.makedirs(S,exist_ok=True)
NOTES={"04":("Prune Ambrée","prune noire, ambre et bois de vanille","#prune #vanille"),
       "26":("Pistache Caramel","pistache et caramel salé","#pistache #caramel"),
       "86":("Fruit du Dragon","jasmin du Brésil et fruit du dragon rose","#jasmin #fruitdudragon"),
       "95":("Violette Vanille","orchidée vanille, violette sucrée et bois de santal","#violette #vanille")}
WEEK=[("2026-10-19","n86_eau","86","Rose, fruitée, fraîche. Voici la N°86.","Team 86 ou team 04 ?","AVILY_n86_eau_hook.mp4"),
      ("2026-10-20","n26_cafe","26","Une brume qui sent le café pistache ?","Team café ou team thé ?","AVILY_n26_cafe_hook.mp4"),
      ("2026-10-21","n95_sucre","95","Une pluie de sucre et de violette.","Tu la portes le jour ou le soir ?","AVILY_n95_sucre_hook.mp4"),
      ("2026-10-23","n86_douche","86","Après la douche, tu mets quoi ?","Douche du matin ou du soir ?","AVILY_n86_douche_hook.mp4"),
      ("2026-10-25","n95_coiffeuse","95","Ta routine du soir, il lui manque ça.","Team violette ou team vanille ?","AVILY_n95_coiffeuse_hook.mp4")]
for day,slug,n,hook,q,f in WEEK:
    name,notes,tags=NOTES[n]
    base=f"Brume parfumée 250 ml · 59 DH · Paiement à la livraison partout au Maroc 🇲🇦"
    ig=(f"N°{n} {name} : {hook}\n{q} Dis-le en commentaire 👇\n\n"
        f"Notes : {notes}.\n{base}\nCommande par le lien dans la bio.\n\n"
        f"#brumeparfumee #bodymist #parfummaroc #beautemaroc {tags} #avily")
    tt=(f"N°{n} {name} 🇲🇦 {q} 👇\nBrume parfumée (body mist) {notes} · 250 ml · 59 DH · paiement à la livraison partout au Maroc. "
        f"Commande sur avily.youcan.store\n#brumeparfumee #bodymist #parfummaroc #beautemaroc {tags}")
    yt_title=f"{hook.rstrip('.')} · Brume {name} N°{n} #Shorts"
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
