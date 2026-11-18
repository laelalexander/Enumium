"""Down Home Creole factory data, copied from https://silocloud.dev/factory/ (api/state) on 2026-11-17.

The site marks nearly every value as a placeholder (formulas, costs, UPCs, line speeds). Running this file
writes site.json, which every design tool in this project reads. Nothing here is invented: where the site
had no value the field is absent and the design basis (design/design-basis.json) states the assumption.
"""
import json, pathlib

# id: (name, group, bulk density g/mL, major allergen or "")
ING = {
    "salt": ("Salt, fine flake", "Base", 1.2, ""), "paprika": ("Paprika, ground (120 ASTA)", "Pepper & chile", 0.45, ""),
    "smoked-paprika": ("Paprika, smoked", "Pepper & chile", 0.45, ""), "garlic": ("Garlic, granulated", "Allium", 0.72, ""),
    "onion": ("Onion, powder", "Allium", 0.55, ""), "black-pepper": ("Black pepper, ground 30 mesh", "Pepper & chile", 0.5, ""),
    "black-pepper-coarse": ("Black pepper, coarse 16 mesh", "Pepper & chile", 0.45, ""),
    "white-pepper": ("White pepper, ground", "Pepper & chile", 0.55, ""), "red-pepper": ("Red pepper, crushed", "Pepper & chile", 0.35, ""),
    "cayenne": ("Cayenne pepper, 40K HU", "Pepper & chile", 0.45, ""), "bell-pepper": ("Bell pepper, dehydrated granules", "Vegetable", 0.3, ""),
    "celery-seed": ("Celery seed, whole", "Seed", 0.5, ""), "oregano": ("Oregano, rubbed", "Herb", 0.2, ""),
    "thyme": ("Thyme, rubbed", "Herb", 0.3, ""), "parsley": ("Parsley flakes", "Herb", 0.08, ""), "basil": ("Basil, rubbed", "Herb", 0.15, ""),
    "rosemary": ("Rosemary, cut", "Herb", 0.3, ""), "lemon-peel": ("Lemon peel granules", "Citrus", 0.5, ""),
    "citric-acid": ("Citric acid, fine granular", "Acid", 0.9, ""), "sugar": ("Cane sugar, fine", "Sweetener", 0.85, ""),
    "natural-flavor": ("Natural flavor (spray dried)", "Flavor", 0.5, ""), "silicon-dioxide": ("Silicon dioxide", "Processing aid", 0.1, ""),
    "wheat-flour": ("Wheat flour, enriched", "Flour", 0.55, "Wheat"), "corn-flour": ("Yellow corn flour", "Flour", 0.7, ""),
    "baking-powder": ("Baking powder, double acting", "Leavening", 0.9, ""), "onion-gran": ("Onion, granulated (not powder)", "Allium", 0.68, ""),
    "chili-powder": ("Chili powder, no salt added", "Pepper & chile", 0.5, ""), "lemon-pepper": ("Lemon pepper, salt-free / low salt", "Pepper & chile", 0.6, ""),
    "italian-herbs": ("Italian herb medley", "Herb", 0.18, ""), "spinach-powder": ("Spinach powder, dehydrated", "Vegetable", 0.45, ""),
    "kale-powder": ("Kale powder, dehydrated", "Vegetable", 0.42, ""), "beet-powder": ("Beet root powder", "Vegetable", 0.6, ""),
    "tomato-powder": ("Tomato powder, spray dried", "Vegetable", 0.62, ""), "red-bell-pepper": ("Red bell pepper, dehydrated granules", "Vegetable", 0.38, ""),
    "turmeric": ("Turmeric, ground", "Spice", 0.55, ""), "ginger": ("Ginger, ground", "Spice", 0.45, ""),
    "cinnamon": ("Cinnamon, ground (cassia)", "Spice", 0.5, ""), "blueberry-powder": ("Blueberry powder, freeze dried", "Fruit", 0.5, ""),
    "pea-protein": ("Pea protein isolate", "Protein", 0.42, ""), "oat-flour": ("Oat flour, whole grain", "Flour", 0.5, ""),
    "ww-flour": ("Whole wheat flour, heat-treated", "Flour", 0.55, "Wheat"), "flaxseed-meal": ("Flaxseed, milled", "Seed", 0.4, ""),
    "baking-soda": ("Sodium bicarbonate", "Leavening", 1.1, ""), "rice-flour": ("Rice flour, white", "Flour", 0.7, ""),
    "corn-starch": ("Corn starch", "Flour", 0.6, ""),
}
# wet-line ingredients listed on the site but outside the dry line: tomato puree, water, vinegar, diced onion,
# olive oil, crushed tomato, ginger/garlic puree, honey, xanthan.

F = {  # formula id: (product id, name, {ingredient: % w/w})
    "f-orig": ("p-orig", "Creole Chameleon Original", dict(salt=38, paprika=14, garlic=11, onion=9, **{"black-pepper": 7, "red-pepper": 6, "bell-pepper": 4.5, "celery-seed": 3}, oregano=2.5, thyme=2, cayenne=1.5, parsley=1, **{"natural-flavor": 0.5})),
    "f-fire": ("p-fire", "Creole Chameleon Fire Blend", dict(salt=32, cayenne=14, paprika=12, garlic=10, **{"red-pepper": 9}, onion=8, **{"black-pepper": 7, "bell-pepper": 3}, oregano=2, thyme=1.5, **{"celery-seed": 1}, parsley=0.5)),
    "f-lemp": ("p-lemp", "Creole Chameleon Lemon Pepper", {"salt": 30, "black-pepper-coarse": 28, "lemon-peel": 16, "garlic": 8, "onion": 6, "citric-acid": 5, "natural-flavor": 3, "parsley": 2, "sugar": 2}),
    "f-garl": ("p-garl", "Creole Chameleon Garlic Herb", {"garlic": 38, "salt": 32, "onion": 12, "black-pepper": 6, "basil": 3, "oregano": 3, "parsley": 2, "thyme": 2, "rosemary": 2}),
    "f-blkn": ("p-blkn", "Creole Chameleon Blackened", {"paprika": 26, "salt": 22, "garlic": 12, "onion": 10, "black-pepper": 8, "cayenne": 7, "thyme": 6, "oregano": 5, "white-pepper": 4}),
    "f-caml": ("p-caml", "Creole Camilian Standard", {"salt": 25, "paprika": 15, "garlic": 12, "onion-gran": 12, "chili-powder": 10, "lemon-pepper": 7, "cayenne": 5, "oregano": 5, "italian-herbs": 5, "parsley": 4}),
    "f-ncgb": ("p-ncgb", "N-Constant GreenBoost Blend", {"spinach-powder": 30, "kale-powder": 18, "parsley": 12, "garlic": 10, "onion": 8, "basil": 7, "lemon-peel": 6, "salt": 5, "black-pepper": 4}),
    "f-ncnc": ("p-ncnc", "N-Constant NeuroClarity", {"cinnamon": 30, "turmeric": 25, "blueberry-powder": 20, "ginger": 15, "sugar": 7, "black-pepper": 3}),
    "f-lyrb": ("p-lyrb", "Lycopoise Red Pepper Boost", {"red-bell-pepper": 28, "tomato-powder": 22, "paprika": 16, "smoked-paprika": 8, "garlic": 8, "onion": 7, "salt": 7, "cayenne": 2, "oregano": 2}),
    "f-lthr": ("p-lthr", "Lyco-Tomato Herb Rub", {"tomato-powder": 30, "garlic": 14, "onion": 12, "basil": 10, "oregano": 10, "salt": 10, "thyme": 6, "black-pepper": 5, "red-pepper": 3}),
    "f-ngrb": ("p-ngrb", "Nitro-Green Rub", {"spinach-powder": 26, "parsley": 18, "garlic": 14, "basil": 12, "lemon-peel": 6, "salt": 10, "celery-seed": 6, "black-pepper": 5, "beet-powder": 3}),
    "f-vfrb": ("p-vfrb", "Vascular Fire Rub", {"paprika": 24, "smoked-paprika": 14, "garlic": 13, "salt": 13, "onion": 10, "cayenne": 8, "black-pepper": 7, "oregano": 5, "sugar": 6}),
    "f-efap": ("p-efap", "EndoFlex All-Purpose Blend", {"garlic": 22, "onion": 18, "salt": 18, "paprika": 12, "black-pepper": 9, "turmeric": 7, "thyme": 5, "parsley": 4, "ginger": 3, "oregano": 2}),
    "f-batter": ("p-batter", "Creole Fish Fry Batter Mix (concept)", {"corn-flour": 52, "wheat-flour": 30, "salt": 6, "paprika": 4, "garlic": 2.5, "baking-powder": 2, "black-pepper": 1.5, "cayenne": 1.2, "onion": 0.8}),
    "f-ncpm": ("p-ncpm", "N-Constant Protein Pancake & Waffle Mix", {"ww-flour": 38, "oat-flour": 22, "pea-protein": 20, "sugar": 6, "beet-powder": 4, "baking-powder": 4, "flaxseed-meal": 3, "cinnamon": 1.5, "salt": 1, "baking-soda": 0.5}),
    "f-afcb": ("p-afcb", "Air-Fry Crisp Batter", {"wheat-flour": 44, "corn-flour": 22, "rice-flour": 12, "corn-starch": 6, "salt": 4.5, "paprika": 3.5, "garlic": 2.5, "baking-powder": 2.5, "onion": 2, "black-pepper": 1}),
}

# container id: (format, name, brimful mL, tare g, width in, height in)
PKG = {
    "jar-12": ("JAR", "PET jar, 89 mm neck (12 oz fill)", 700, 38, 3.4, 6.1),
    "shaker-4": ("SHAKER", "PET shaker, 53 mm neck (4 oz fill)", 235, 18, 2.3, 4.6),
    "shaker-250": ("SHAKER", "Clear round PET shaker jar, 8.4 fl oz (248 mL)", 248, 26, 2.6, 4.3),
    "shaker-320": ("SHAKER", "PET shaker, 53 mm neck, 320 mL", 320, 24, 2.6, 5.6),
    "pouch-12": ("POUCH", "Stand-up zip pouch, printed, window", 760, 12, 6.5, 9.0),
    "tub-5lb": ("TUB", "HDPE food-service tub, 1.25 gal", 4730, 230, 8.0, 7.5),
    "box-16": ("BOX", "Folding carton + poly liner (16 oz)", 1150, 55, 5.5, 8.0),
}
CLOSURES = {"cap-89": "89 mm dual-flap sifter cap + induction liner", "cap-53": "53 mm sifter cap + liner",
            "cap-53-flip": "53 mm flip-top sifter cap + liner", "lid-tub": "Tamper-evident tub lid"}
LABELS = {"lbl-12": (9.5, 3.5), "lbl-4": (6.5, 2.5), "lbl-84": (7.5, 2.75), "lbl-4-tall": (7.75, 3.0), "lbl-tub": None}

# sku: (product, format, net oz, container, closure, label, case count, line category)
SKU = [
    ("s-orig-12j", "p-orig", "SHAKER", 12, "shaker-4", "cap-53", "lbl-4", 12, "seasoning"),
    ("s-orig-12p", "p-orig", "POUCH", 12, "pouch-12", None, None, 12, "seasoning"),
    ("s-orig-4s", "p-orig", "SHAKER", 4, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-orig-80t", "p-orig", "TUB", 80, "tub-5lb", "lid-tub", "lbl-tub", 4, "seasoning"),
    ("s-caml-4s", "p-caml", "SHAKER", 3.5, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
] + [(f"s-{p}-12j", f"p-{p}", "JAR", 12, "jar-12", "cap-89", "lbl-12", 12, "seasoning") for p in ("fire", "lemp", "garl", "blkn")] \
  + [(f"s-{p}-4s", f"p-{p}", "SHAKER", 4, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning") for p in ("fire", "lemp", "garl", "blkn")] + [
    ("s-ncgb-2", "p-ncgb", "SHAKER", 2, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-ncnc-4", "p-ncnc", "SHAKER", 4, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-lyrb-4", "p-lyrb", "SHAKER", 4, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-lthr-3", "p-lthr", "SHAKER", 3, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-ngrb-175", "p-ngrb", "SHAKER", 1.75, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-vfrb-4", "p-vfrb", "SHAKER", 4, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-efap-35", "p-efap", "SHAKER", 3.5, "shaker-250", "cap-53-flip", "lbl-84", 12, "seasoning"),
    ("s-batter-16b", "p-batter", "BOX", 16, "box-16", None, None, 12, "dry-boxed"),
    ("s-ncpm-16", "p-ncpm", "BOX", 16, "box-16", None, None, 12, "dry-boxed"),
    ("s-afcb-20", "p-afcb", "BOX", 20, "box-16", None, None, 12, "dry-boxed"),
]
SITE_PROCESS = {
    "batch_lb": 250, "ribbon_blender": "RB-202 10 cu ft, 10 HP, 30 rpm", "blend_cv_spec_pct": 5, "tracer": "salt",
    "mix_time_min": 12, "premix_rule": "ingredients under 2% go into a V-blender premix (PM-201)", "scale_resolution_g": 0.1,
    "fill_loss_pct": 1.0, "underweight_rule": "reject any unit below declared net (NIST Handbook 133 cited)",
    "lot_code": "DHyyjjj-B## plus best-by", "shelf_life_months": 24, "labor_rate_usd_h": 18, "overhead_pct": 18,
    "launch": "2027-04-01, 11 SKUs; first production runs due 2027-03-08..19",
    "stations": ["RM store", "WS-101/102 weigh & dispense", "PM-201 premix V-blender", "RB-202 ribbon blender", "QC lab",
                 "SC-205 sifter + metal detector", "FL-301 auger filler", "CP-302 capper/sealer", "LB-303 labeler + coder",
                 "CW-304 checkweigher", "CS-305 case packer", "PL-306 palletizer", "FG finished goods"],
    "site_flags": ["DH-CC-ORIG-12S puts 12 oz in a 235 mL shaker: 264% of brimful (site flags it)",
                   "Front-of-pack 'Gluten Free' claim needs <20 ppm testing; wheat products share the plant"],
}


def build():
    ing = {k: dict(name=v[0], group=v[1], density=v[2], allergen=v[3]) for k, v in ING.items()}
    forms = {}
    for fid, (pid, name, lines) in F.items():
        tot = sum(lines.values())
        dens = 1 / sum((p / tot) / ING[i][2] for i, p in lines.items())
        alg = sorted({ING[i][3] for i in lines if ING[i][3]})
        forms[fid] = dict(product=pid, name=name, lines=lines, blend_density=round(dens, 3), allergens=alg,
                          minors=[i for i, p in lines.items() if p < 2])
    pkg = {k: dict(format=v[0], name=v[1], brimful_ml=v[2], tare_g=v[3], width_in=v[4], height_in=v[5]) for k, v in PKG.items()}
    skus = [dict(id=s[0], product=s[1], format=s[2], net_oz=s[3], net_g=round(s[3] * 28.3495, 1), container=s[4], closure=s[5],
                 label=s[6], case_count=s[7], category=s[8]) for s in SKU]
    prod2f = {v["product"]: k for k, v in forms.items()}
    for s in skus:
        f = forms[prod2f[s["product"]]]
        vol = s["net_g"] / f["blend_density"]
        s["fill_pct_of_brimful"] = round(100 * vol / pkg[s["container"]]["brimful_ml"], 1)
        s["formula"] = prod2f[s["product"]]
    return dict(source="https://silocloud.dev/factory/ (api/state), read 2026-11-17", placeholder_note=__doc__.strip().splitlines()[2],
                ingredients=ing, formulas=forms, packaging=pkg, closures=CLOSURES, labels=LABELS, skus=skus, process=SITE_PROCESS)


if __name__ == "__main__":
    out = pathlib.Path(__file__).with_name("site.json")
    out.write_text(json.dumps(build(), indent=1))
    d = json.loads(out.read_text())
    print(len(d["ingredients"]), "ingredients,", len(d["formulas"]), "dry formulas,", len(d["skus"]), "dry SKUs")
    for s in d["skus"]:
        if s["fill_pct_of_brimful"] > 95:
            print("  DOES NOT FIT:", s["id"], s["fill_pct_of_brimful"], "% of brimful")
