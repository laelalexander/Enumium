"""Equipment list for the Down Home Creole dry blending and packing plant (Growth option, 6,000 lb/day).

Every bought item is a real catalog product. For each one:
  model / mpn    the maker's model or material number; "confirm" means the exact suffix comes on the quote
  specs          the figures the design depends on, each with its source tag
  source         the page the figures were read from (read 2026-11-17)
  supplier       who sells it (maker direct or a distributor); capital equipment is built to order, so
                 "stock" is a quoted lead time, not shelf stock. Lead times are filled from quotes.
  qty_basis      why this many: traced to the design basis, the line balance or the layout
  price          documented (a published price) or estimate (Claude's budget figure, not a quote)
  sanitary       food-safety notes the food-safety check reads (contact surfaces, washdown, dust)
Footprints are L x W x H in mm; "documented" when from the maker, otherwise "estimate".
Running this file writes equipment.json.
"""
import json, pathlib

E = []


def eq(tag, area, name, maker, model, specs, source, supplier, qty, qty_basis, price, footprint, fp_src,
       power=None, air_cfm=0.0, sanitary="", alternates=(), rate=None, kind="buy", contact=False, dust_cfm=0, confirm=""):
    E.append(dict(tag=tag, area=area, name=name, maker=maker, model=model, specs=specs, source=source, supplier=supplier,
                  qty=qty, qty_basis=qty_basis, price=price, footprint_mm=footprint, footprint_src=fp_src, power=power,
                  air_cfm=air_cfm, sanitary=sanitary, alternates=list(alternates), rate=rate, kind=kind,
                  product_contact=contact, dust_cfm=dust_cfm, confirm=confirm))


MT = "Mettler-Toledo (direct, mt.com) or authorized dealer"
FLX = "Flexicon Corp. (direct, Bethlehem PA)"
ROSS = "Charles Ross & Son (direct, Hauppauge NY)"
RA = "Rockwell Automation distributor (e.g., Rexel / Werner Electric)"

# ---------------------------------------------------------------- 100 receiving and storage
eq("RCV-101", "Receiving", "Receiving floor scale + terminal (verify inbound weights)", "Mettler-Toledo",
   "PBA655 floor scale 48x48 in, 5,000 lb + IND570 terminal (material no. on quote)",
   {"capacity": "5,000 lb [2,268 kg] (estimate of size chosen)", "terminal": "IND570, Ethernet/IP option (documented)"},
   "https://www.mt.com/dam/ind/IND_PDF/2021/Brochures/44098288_B_MAR_BR_PBA655x_USA.pdf", MT, 1,
   "one receiving dock", {"usd": 9500, "src": "estimate"}, [1219, 1219, 100], "estimate", "120 V 1-ph", 0,
   "painted or SS platform outside the processing zone", confirm="platform size and capacity on quote")
eq("WH-102", "Storage", "Selective pallet rack, 3 beam levels + floor, 96 in beams", "Steel King",
   "SK2000 boltless selective rack (frames 42 in deep, 96 in beams)",
   {"positions_per_bay": "8 (2 per level x 4 levels) (calculated)", "beam_capacity": "per load chart (documented by maker)"},
   "https://www.steelking.com/pallet-rack/", "Steel King dealer / local rack installer", 26,
   "rack positions = raw 2-week stock + packaging 2-week + FG 3-day (plant.py storage calc); 26 bays", {"usd": 650, "src": "estimate", "per": "bay"},
   [2438, 1067, 4877], "estimate", None, 0, "keep 18 in [457 mm] from walls for inspection and pest control")
eq("WH-103", "Storage", "Allergen (wheat) segregation cage with lockable door", "WireCrafters",
   "Style 840 woven wire partition, 10 ft high, sliding door",
   {"height": "10 ft [3,048 mm] (assumed)", "use": "wheat flour, whole wheat flour stored apart (site: 2 ingredients carry wheat)"},
   "https://www.wirecrafters.com/products/wire-partitions/", "WireCrafters dealer", 1, "one allergen store",
   {"usd": 7800, "src": "estimate"}, [6096, 3048, 3048], "estimate", None, 0, "yellow-coded tools stay inside the cage")
eq("FL-104", "Storage", "Electric counterbalance forklift (no LPG in food or dust zones)", "Toyota Material Handling",
   "Core Electric 8FBE20U, 4,000 lb", {"capacity": "4,000 lb [1,814 kg] (documented)", "fuel": "electric, no exhaust"},
   "https://www.toyotaforklift.com/lifts/electric-motor-rider-forklifts/core-electric-forklift", "Toyota Material Handling dealer", 1,
   "bulk bags 1,000-2,000 lb on and off discharger frames; one truck covers 6-8 bag moves per day", {"usd": 38000, "src": "estimate"},
   [3200, 1100, 2100], "estimate", "battery charger 208 V 3-ph", 0, "electric only; charge outside the processing zone")
eq("PJ-105", "Storage", "Electric walkie pallet jack", "Crown", "WP 3200 Series", {"capacity": "4,500 lb (documented)"},
   "https://www.crown.com/en-us/forklifts/walkie-pallet-jack-wp-3200.html", "Crown dealer", 2,
   "one in receiving / storage, one at the pack line end", {"usd": 6500, "src": "estimate", "per": "each"}, [1900, 700, 1300], "estimate")

# ---------------------------------------------------------------- 200 weigh and dispense, premix
eq("WS-201", "Weigh & dispense", "Major-ingredient floor scale + terminal (bags into batch tote)", "Mettler-Toledo",
   "PBA655 washdown floor scale 36x36 in, 1,000 lb + IND570 terminal",
   {"capacity": "1,000 lb x 0.2 lb (estimate of build)", "terminal": "IND570 with Ethernet; MES reads weight (calculated need)"},
   "https://www.mt.com/IND570", MT, 1, "major ingredients >= 2% of a batch are weighed bag-wise here (site premix rule)",
   {"usd": 8200, "src": "estimate"}, [914, 914, 90], "estimate", "120 V", 0, "stainless washdown version", confirm="material no.")
eq("WS-202", "Weigh & dispense", "Bench scale 60 kg for partial bags", "Mettler-Toledo", "ICS685 bench scale, 60 kg (ICS685k-60LA/f, confirm)",
   {"capacity": "60 kg [132 lb]", "readability": "2 g (estimate for class)", "interfaces": "Ethernet/RS232 (documented for ICS685)"},
   "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/bench-scales/checkweigher/ICS685/ICS685k-count-6SM-f.html", MT, 1,
   "partial bags of majors", {"usd": 3200, "src": "estimate"}, [600, 500, 900], "estimate", "120 V", 0, "stainless", confirm="exact 60 kg model")
eq("WS-203", "Weigh & dispense", "Micro-ingredient scale 6 kg x 0.1 g (minors under 2%)", "Mettler-Toledo",
   "ICS685s-6SM/f, material no. 22023053",
   {"capacity": "6 kg [12 lb] (documented)", "readability": "0.1 g; certified 1 g (documented)", "interfaces": "RS232, Ethernet option (documented)"},
   "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/bench-scales/bench-scale/compact-scale-ics685s-6sm-f-22023053.html", MT, 1,
   "site scale resolution 0.1 g for minors; one premix weigh station", {"usd": 2600, "src": "estimate"}, [240, 200, 95], "documented", "120 V")
eq("WS-204", "Weigh & dispense", "Dust extraction arm at weigh bench", "Nederman", "FX2 extraction arm, 2 m reach, 100 mm",
   {"airflow": "350-450 cfm per arm at the hood (estimate)", "reach": "2 m [6.6 ft] (documented range)"},
   "https://www.nederman.com/en-us/products/extraction-arms", "Nederman distributor", 2, "one per weigh bench (majors, minors)",
   {"usd": 2400, "src": "estimate", "per": "each"}, [300, 300, 2600], "estimate", None, 0, "duct to DC-310", dust_cfm=400)
eq("WS-205", "Weigh & dispense", "Cordless barcode scanner (lot scan of every ingredient bag)", "Zebra", "DS3678-SR rugged cordless",
   {"drop": "rated for industrial use, IP65 (documented class)", "codes": "1D/2D, GS1-128"},
   "https://www.zebra.com/us/en/products/scanners/rugged-scanners/ds3600-series.html", "Zebra partner (e.g., CDW, Barcodes Inc.)", 3,
   "weigh majors, weigh minors, pack line hopper charge", {"usd": 600, "src": "estimate", "per": "each"}, [200, 80, 120], "estimate")
eq("WS-206", "Weigh & dispense", "Thermal transfer printer for bag, premix and tote labels", "Zebra", "ZT411 203 dpi, ZT41142-T010000Z",
   {"print_width": "4.09 in [104 mm] (documented)", "language": "ZPL"}, "https://www.zebra.com/us/en/products/printers/industrial/zt400-series.html",
   "Zebra partner", 2, "weigh room + blending room", {"usd": 1900, "src": "estimate", "per": "each"}, [495, 269, 324], "documented", "120 V")
eq("WS-207", "Weigh & dispense", "Stainless all-in-one panel PC for weigh & dispense screens", "Advantech", "UTC-520 21.5 in (IP65 front)",
   {"display": "21.5 in touch", "front": "IP65 (documented, confirm)"}, "https://www.advantech.com/en-us/products/utc-500-series",
   "Advantech distributor", 3, "weigh room, blending room, packing hall", {"usd": 2100, "src": "estimate", "per": "each"}, [540, 60, 340], "estimate",
   "120 V", confirm="stainless VESA mount and IP rating")
eq("PM-210", "Weigh & dispense", "Premix V-cone blender for minors (<2%) with carrier salt", "Charles Ross & Son", "VCB-5 V-cone blender",
   {"working_capacity": "5 cu ft [142 L] (documented)", "motor": "5 HP, 24 rpm (documented)"},
   "https://cdn.mixers.com/Specifications/VCB%20Spec%20Sheet.pdf", ROSS, 1,
   "premix = minors + carrier salt to ~10% of the main batch: 1,100 lb x 10% / 31 lb per cu ft = 3.5 cu ft < 5 (line balance)",
   {"usd": 42000, "src": "estimate"}, [2413, 1600, 2489], "documented", "480 V 3-ph, 5 HP", 0,
   "304/316 SS contact parts, polished; intensifier bar optional", contact=True, rate={"cycle_min": 20})

# ---------------------------------------------------------------- 300 blending, sifting, metal detection
eq("BD-301", "Blending", "Bag dump station with integral dust collector and flexible screw conveyor to blender", "Flexicon",
   "TIP-TITE / Bag Dump Station with integral dust collector + FLEXI-DISC or flexible screw conveyor (configuration on quote)",
   {"dust": "integral cartridge collector, reverse-pulse (documented)", "conveyor": "flexible screw to blender inlet"},
   "https://flexicon.com/configurations/bag-dump-station/", FLX, 1, "all bagged majors and the premix go in through one dump point",
   {"usd": 46000, "src": "estimate"}, [1520, 1220, 2440], "estimate", "480 V 3-ph", 4, "sanitary 304 SS, 3-A/USDA options (documented)",
   contact=True, rate={"lb_per_h": 6000, "src": "assumed for 3.5 in screw on spices, confirm"})
eq("BB-302", "Blending", "Bulk bag discharger for salt with flexible screw conveyor to blender", "Flexicon",
   "BULK-OUT BFC bulk bag discharger + flexible screw conveyor", {"bag": "up to 4,000 lb FIBC (documented class)", "salt_share": "18-38% of seasonings (site)"},
   "https://flexicon.com/products/bulk-bag-discharger/", FLX, 1, "salt is the single biggest ingredient (site formulas); bulk bags avoid 50 lb bag dumping",
   {"usd": 52000, "src": "estimate"}, [2030, 2030, 4270], "estimate", "480 V 3-ph", 4, "sanitary SS, spout access chamber with dust seal",
   contact=True, dust_cfm=300)
eq("RB-303", "Blending", "Ribbon blender, 36 cu ft working, sanitary", "Charles Ross & Son", "42N-36 ribbon blender, 304 SS, sanitary finish",
   {"working_capacity": "36 cu ft [1,019 L] (documented)", "full_capacity": "41 cu ft (documented)", "motor": "15 HP, 40 rpm (documented)",
    "dims_in": "115 x 49 x 92 (documented)"}, "https://cdn.mixers.com/Specifications/42N Spec Sheet 2022.pdf", ROSS, 1,
   "line balance (design/out/line-balance.md): 36 batches/week at 36 cu ft = 78% of blender time; 25 cu ft = 93%, over the 85% limit",
   {"usd": 98000, "src": "estimate"}, [2921, 1245, 2337], "documented", "480 V 3-ph, 15 HP", 2,
   "clean-out door, flush discharge valve, load cells option (documented), Ra <= 0.8 um contact", contact=True, dust_cfm=200,
   rate={"working_cuft": 36, "mix_min": 12})
eq("SC-304", "Blending", "Sanitary vibratory sifter (scalping 12 mesh) with discharge magnet", "Kason", "Vibroscreen K48-1-SS (48 in) ultra-sanitary, same series as the documented K30-1-SS",
   {"diameter": "48 in [1,219 mm] (series documented at 30 in; 48 in size on quote)", "magnet": "removable sanitary magnet at discharge (documented)",
    "rate": "~6,000 lb/h on 12 mesh spice blends (estimate, confirm by test); sets blender discharge time"},
   "https://www.petfoodindustry.com/production/product/15453212/kason-corp-vibroscreen-model-k30-1-ss-30-inch-screener",
   "Kason Corp. (direct, Millburn NJ)", 1, "every batch is sifted once at blender discharge (site: Sift & Metal Detect station)",
   {"usd": 24000, "src": "estimate"}, [1450, 1450, 1250], "estimate", "480 V 3-ph", 0, "gap-free screen frames, quick clamps, 3-A (documented)",
   contact=True, dust_cfm=200, rate={"lb_per_h": 6000}, confirm="48 in model and rate by test sift")
eq("MD-305", "Blending", "Gravity-fall metal detector with diverter reject", "Mettler-Toledo Safeline", "Gravity Fall Profile, 150 mm aperture, Y-valve reject (material 2801546900 family)",
   {"aperture": "up to 300 mm (documented); 150 mm chosen", "reject": "open diverter, Y-valve or Sealtite (documented)", "ip": "IP65/IP66 (documented)"},
   "https://ds-rgr.mt.com/us/en/home/products/Product-Inspection_1/safeline-metal-detection/Gravity-Fall-Profile-Metal-Detector.html", MT, 1,
   "CCP-1 metal: one detector after the sifter, before the bulk bag", {"usd": 38000, "src": "estimate"}, [600, 500, 900], "estimate",
   "120 V", 2, "stainless finish version; reject to locked container", contact=True)
eq("BF-306", "Blending", "Bulk bag filler with load cells (one bag = one batch, held for QC release)", "Flexicon",
   "BASIC bulk bag filler, sanitary SS, load cells, vibratory densification deck",
   {"scale": "load cells, weight-controlled fill (documented)", "deck": "vibratory densification (documented)"},
   "https://flexicon.com/products/bulk-bag-fillers/", FLX, 1, "one blender, one discharge point", {"usd": 48000, "src": "estimate"},
   [2130, 2130, 4270], "estimate", "480 V 3-ph", 3, "inflatable spout seal, vent to DC-310", contact=True, dust_cfm=300)

eq("FC-307", "Blending", "Flexible screw conveyor: metal detector outlet hopper up to the bulk bag filler inlet", "Flexicon",
   "Flexible screw conveyor, 4.5 in, sanitary floor hopper (model on quote)", {"lift": "about 4.5 m [15 ft] (layout ASM-001)", "rate": "6,000 lb/h (assumed, matches SC-304)"},
   "https://flexicon.com/products/flexible-screw-conveyors/", FLX, 1, "one blender discharge path (ASM-001)", {"usd": 21000, "src": "estimate"},
   [900, 900, 4600], "estimate", "480 V 3-ph, 3 HP", 0, "sanitary, full clean-out by removing the screw", contact=True)

# ---------------------------------------------------------------- 310 utilities serving the process
eq("DC-310", "Utilities", "Central cartridge dust collector, outdoor, explosion vented with isolation valve", "Camfil APC",
   "Gold Series X-Flo GSX 12 (12 cartridges, about 3,600 cfm at 1.5:1 to 2:1 air-to-media, confirm), explosion vent + inlet isolation flap valve",
   {"airflow": "3,625 cfm design = 2,900 cfm sum of pickups (dust_cfm x qty, checked by foodsafety.py) + 25 % margin", "design_cfm": 3625, "dust": "spice dust treated as combustible until tested (NFPA 61/652)"},
   "https://www.camfil.com/en-us/products/dust-fume-and-mist-collectors/dust-and-fume-collectors/gold-series-x-flo", "Camfil APC (direct, Jonesboro AR)", 1,
   "all local pickups duct to one collector outside the north wall", {"usd": 68000, "src": "estimate"}, [1830, 1520, 4570], "estimate",
   "480 V 3-ph, 10 HP fan", 3, "outdoor; dust hazard analysis (DHA) required before order", confirm="size after duct design")
eq("AC-311", "Utilities", "Rotary screw air compressor with integrated dryer", "Kaeser", "SK 15 T (15 hp, refrigerated dryer)",
   {"flow": "about 55 cfm at 125 psi (documented class)", "demand": "sum of air users (plant.py)"},
   "https://us.kaeser.com/products/rotary-screw-compressors/sk/", "Kaeser (direct) or distributor", 1, "plant air demand < 45 cfm",
   {"usd": 17500, "src": "estimate"}, [1100, 700, 1300], "estimate", "480 V 3-ph, 15 HP", 0,
   "food-contact air: coalescing + activated carbon + 0.01 um sterile filter at each point of contact (SQF)")
eq("AF-312", "Utilities", "Compressed air filter train for product-contact air", "Parker domnick hunter", "OIL-X grade AO + AA + ACS, BIO-X sterile filter",
   {"class": "ISO 8573-1 class 1.2.1 target (documented capability)"}, "https://www.parker.com/us/en/divisions/gas-separation-and-filtration-division/products/oil-x.html",
   "Parker distributor", 1, "one train after the dryer", {"usd": 3800, "src": "estimate"}, [600, 300, 900], "estimate")

# ---------------------------------------------------------------- 400 pack line A (shakers and jars)
eq("BU-401", "Pack line A", "Bulk bag discharger + flexible screw to filler hopper (QC-released bag)", "Flexicon",
   "BULK-OUT BFC bulk bag discharger, sanitary, with flexible screw conveyor and hopper level control",
   {"bag": "the blend bag from BF-306", "control": "high/low level probes at FL-403 hopper"}, "https://flexicon.com/products/bulk-bag-discharger/", FLX, 1,
   "one filler", {"usd": 52000, "src": "estimate"}, [2030, 2030, 4270], "estimate", "480 V 3-ph", 4, "sanitary SS", contact=True, dust_cfm=300)
eq("UN-402", "Pack line A", "Container unscrambling table", "Kaps-All", "FS-U unscrambling table (stainless)",
   {"speed": "1-400 bottles/min class (documented)"}, "https://www.kapsall.com/solutions/bottle-unscramblers/fs-u-unscrambling-table",
   "Kaps-All Packaging Systems (direct, Riverhead NY)", 1, "one line", {"usd": 14000, "src": "estimate"}, [1220, 1220, 1000], "estimate",
   "120 V", 0, "non-contact (outside of containers only)", rate={"upm": 120})
eq("FL-403", "Pack line A", "Rotary auger filler, twin servo augers, integrated weigh-check", "Spee-Dee Packaging Machinery",
   "X-Series rotary filler with two Revolution servo auger fillers (speed confirmed on quote)",
   {"fill_range": "5 g to 5 lb per auger (documented for Revolution)", "speed": "80 cpm on 2-4 oz, 45 cpm on 12 oz (assumed, confirm by run test)",
    "changeover": "tool-less change parts (documented for rotary fillers)"},
   "https://www.spee-dee.com/automatic-spice-packing-filling-machine", "Spee-Dee (direct, Sturtevant WI)", 1,
   "line balance: line A 88% loaded at 80 cpm on one shift (limit 85%); filler sets line speed, all others >= 1.25x", {"usd": 185000, "src": "estimate"}, [2400, 1600, 2800], "estimate",
   "480 V 3-ph", 3, "SS auger and funnel, magnetic funnel quick release (documented)", contact=True, dust_cfm=250,
   rate={"upm": {"SHAKER": 80, "JAR": 45}})
eq("CP-404", "Pack line A", "Inline 6-spindle capper with cap sorter", "Kaps-All", "A6 6-spindle auto capper",
   {"speed": "up to 200 bpm (documented)", "caps": "8-120 mm (documented)", "power": "220 V 3-ph (documented)"},
   "https://kapsall.com/solutions/cappers/a6-6-spindle-auto-capper", "Kaps-All Packaging Systems", 1, "one line",
   {"usd": 52000, "src": "estimate"}, [2286, 965, 1830], "documented", "220 V 3-ph", 3, "SS enclosure, interlocked doors (documented)",
   rate={"upm": 200})
eq("IS-405", "Pack line A", "Induction cap sealer (tamper evident liner seal)", "Enercon", "Super Seal 600 with all-in-one head (model by line speed, confirm)",
   {"supply": "240 V 1-ph (documented)", "heads": "flat, tunnel, all-in-one (documented)"},
   "https://www.enerconind.com/Sealing/Products/Super-Seal/", "Enercon Industries (direct, Menomonee Falls WI)", 1, "one line",
   {"usd": 19000, "src": "estimate"}, [900, 600, 1600], "estimate", "240 V 1-ph", 0, "", rate={"upm": 150})
eq("LB-406", "Pack line A", "Wrap-around pressure-sensitive labeler", "Pack Leader USA", "PL-501",
   {"label_speed": "131.2 ft/min (documented)", "conveyor": "72.2 ft/min (documented)", "container_max_width": "4 in (documented)",
    "label_max": "11.8 x 6 in (documented)", "dims_in": "79 x 40 x 41 (documented)"},
   "https://www.sigmaequipment.com/equipment/model/pack-leader-usa/pl-501/", "Pack Leader USA (direct, Pine Brook NJ)", 1,
   "one line; largest container jar-12 is 3.4 in, under the 4 in limit", {"usd": 28000, "src": "estimate"}, [2007, 1016, 1041], "documented",
   "120/220 V 1-ph", 0, "", rate={"upm": 150})
eq("TT-407", "Pack line A", "Thermal transfer overprinter on the labeler (lot + best-by on the label web)", "Videojet", "DataFlex 6330 TTO, 32 mm",
   {"code": "DHyyjjj-B## + BEST BY MMM DD YYYY (site lot rule)", "interface": "Ethernet, CLARiTY"},
   "https://www.videojet.com/us/homepage/products/thermal-transfer-overprinting.html", "Videojet (direct)", 1, "one labeler",
   {"usd": 11500, "src": "estimate"}, [250, 200, 200], "estimate", "120 V", 0.5)
eq("VS-408", "Pack line A", "Vision: label present, UPC grade, lot code OCR", "Cognex", "In-Sight 2800 with OCR",
   {"tools": "edge-learning classification + OCR (documented)"}, "https://www.cognex.com/products/machine-vision/vision-sensors/in-sight-2800-vision-system",
   "Cognex partner", 1, "one inspection point after the labeler", {"usd": 7800, "src": "estimate"}, [600, 400, 600], "estimate", "24 V DC")
eq("CW-409", "Pack line A", "Checkweigher with pusher reject to locking bin, OPC UA data", "Mettler-Toledo", "C33 PlusLine",
   {"speed": "up to 300-350 ppm (documented, page inconsistent)", "accuracy": "from +/-0.05 g (documented)", "max_weight": "7.5 kg (documented)",
    "data": "Ethernet TCP/IP, OPC UA (documented)"},
   "https://www.mt.com/us/en/home/products/Product-Inspection_1/checkweighing/C33.html", MT, 1,
   "site rule: reject any unit below declared net; lot average per NIST HB 133", {"usd": 32000, "src": "estimate"}, [1500, 800, 1500], "estimate",
   "120 V", 1, "", rate={"upm": 300})
eq("AT-410", "Pack line A", "Rotary accumulation table before pack-off", "Kaps-All", "Rotary table, 48 in (rotary tables line, confirm size)",
   {"buffer": "about 2 minutes at 80 upm (calculated)"}, "https://kapsall.com/solutions/rotary-tables", "Kaps-All Packaging Systems", 1,
   "decouples the cobot case packer from the filler", {"usd": 9500, "src": "estimate"}, [1220, 1220, 1000], "estimate", "120 V", 0)
eq("CE-411", "Pack line A", "Automatic case erector, tape bottom", "Wexxar (ProMach)", "WF20T",
   {"speed": "up to 20 cases/min (documented)", "case_range": "L 7.25-18, W 7.25-14, H 6-15 in (documented)", "air": "90 psi (documented)"},
   "https://www.sigmaequipment.com/equipment/used/wexxar-wf20-t-stainless-steel-fully-automatic-tape-bottom-case-erector-20-cases-per-minute-329528",
   "Wexxar / ProMach dealer", 1, "6.7 cases/min peak needed", {"usd": 46000, "src": "estimate"}, [2540, 1730, 2030], "estimate",
   "240 V 1-ph", 6, "", rate={"cpm": 20}, confirm="case sizes for 12 x shaker and 12 x jar fit the range")
eq("CK-412", "Pack line A", "Cobot case packing cell (UR10e), case-ready infeed", "Omega Design (cobot by Xyntek)", "Intelli-Pac with Case Packing Cobot (UR10e)",
   {"payload": "case layers up to 12 kg (documented)", "reach": "51 in (documented)", "case_range": "6x4x3 to 24x15x21 in (documented)",
    "speed": "about 8 cases/min for 12-count 2 x 6 layer picks (estimate, confirm)"},
   "https://www.profoodworld.com/home/product/22485950/omega-design-corporation-case-packing-cobot", "Omega Design Corp. (direct, Exton PA)", 1,
   "one line, 6.7 cases/min peak", {"usd": 135000, "src": "estimate"}, [2400, 2000, 2000], "estimate", "120 V", 8, "", rate={"cpm": 8})
eq("CS-413", "Pack line A", "Uniform case sealer, top and bottom tape", "Wexxar (BEL)", "BEL 505 (confirm)",
   {"speed": "up to 30 cases/min (estimate)"}, "https://www.wexxar.com/case-sealers/", "Wexxar / ProMach dealer", 1, "one line",
   {"usd": 14000, "src": "estimate"}, [1800, 900, 1700], "estimate", "120 V", 0, "", rate={"cpm": 25}, confirm="model")
eq("PA-414", "Pack line A", "Print and apply case labeler (GS1-128 SSCC + case GTIN-14)", "CTM Labeling Systems + Zebra",
   "CTM 360a with Zebra ZE511 print engine (ZE51142-R010000Z, confirm hand)",
   {"engine": "ZE511 4 in 203 dpi (documented)", "label": "4 x 6 in GS1 logistic label"},
   "https://www.zebra.com/us/en/products/spec-sheets/printers/print-engines/ze511-ze521.html", "CTM Labeling Systems (Salem OH) / Zebra partner", 1,
   "one case line", {"usd": 16500, "src": "estimate"}, [900, 700, 1700], "estimate", "120 V", 2, "", rate={"cpm": 25})
eq("PL-415", "Pack line A", "Cobot palletizer, dual pallet stations", "Robotiq", "PE20 Palletizing Solution, SOL-PAL-UR-VAC-PE20",
   {"payload": "18 kg [40 lb] (documented)", "speed": "13 cycles/min (documented)", "max_height": "2,150 mm [84 in] (documented)",
    "footprint": "2,900 x 1,766 mm (documented)"},
   "https://automationdistribution.com/robotiq-palletizing-solution-pe-series-for-ur20-with-vacuum-gripper", "Automation Distribution (online, in stock listing)", 1,
   "6.7 cases/min peak < 13 cycles/min", {"usd": 57712.50, "src": "documented"}, [2900, 1766, 2300], "documented", "120 V", 10, "", rate={"cpm": 13})
eq("SW-416", "Pack line A", "Semi-automatic turntable stretch wrapper", "Lantech", "Q300",
   {"rate": "25-35 loads/h (documented class)"}, "https://www.lantech.com/product/q300/", "Lantech dealer", 1,
   "about 2.5 pallets/h needed", {"usd": 14500, "src": "estimate"}, [2800, 1700, 2600], "estimate", "120 V", 0)
eq("CV-417", "Pack line A", "Stainless tabletop chain conveyor, 3.25 in Rexnord 880 TAB chain, side guide rails", "Nercon (custom conveyor)",
   "Sanitary tabletop conveyor, Rexnord 880 TAB-K325 chain, length per layout",
   {"length": "from layout (plant.py): about 22 m [72 ft] (calculated)", "chain": "Rexnord 880 TAB 3.25 in (documented catalog chain)"},
   "https://www.rexnord.com/products/880-series-tabletop-chains", "Nercon Engineering (Neenah WI)", 22,
   "metres: line A length 20.5 m on ASM-002 / LAY-001 + 1.5 m transfers", {"usd": 1350, "src": "estimate", "per": "m"}, [22000, 300, 900], "calculated", "480 V 3-ph, 4 x 0.5 HP", 0,
   "open-frame, no hollow tubes; guide rail brackets DH-104", rate={"fpm": 72})

# ---------------------------------------------------------------- 500 pack station B (pouches, tubs, cartons)
eq("NW-501", "Pack station B", "Net-weight auger filler for pouches, tubs and carton liners", "Spee-Dee Packaging Machinery",
   "Net Weight Auger: 4800 servo auger + load cell + conveyor",
   {"accuracy": "< 0.25% variance (documented)", "range": "up to 25 kg (documented)", "speed": "10-14 fills/min on 12 oz-5 lb (estimate)"},
   "https://www.spee-dee.com/automatic-spice-packing-filling-machine", "Spee-Dee (direct)", 1, "pouch + tub + carton volumes fit one station (line balance)",
   {"usd": 78000, "src": "estimate"}, [1800, 1200, 2700], "estimate", "480 V 3-ph", 2, "SS contact parts", contact=True, dust_cfm=250, rate={"upm": 12})
eq("BU-502", "Pack station B", "Bulk bag discharger feeding NW-501", "Flexicon", "BULK-OUT BFC with flexible screw conveyor",
   {"bag": "QC-released blend bag"}, "https://flexicon.com/products/bulk-bag-discharger/", FLX, 1, "one station",
   {"usd": 48000, "src": "estimate"}, [2030, 2030, 4270], "estimate", "480 V 3-ph", 4, "sanitary SS", contact=True, dust_cfm=300)
eq("BS-503", "Pack station B", "Continuous band sealer for stand-up zip pouches, stainless, with embossing coder", "Hualian", "FR-900S stainless (confirm)",
   {"speed": "0-12 m/min (documented class)", "seal_width": "10 mm (documented class)"}, "https://www.hualianmachinery.com/", "Hualian US distributor", 1,
   "12 oz pouches only", {"usd": 2600, "src": "estimate"}, [900, 450, 450], "estimate", "120 V", 0, "", confirm="US distributor stock")
eq("IM-504", "Pack station B", "Foot-operated impulse sealer for carton poly liners", "American International Electric", "AIE-305FD (12 in, 5 mm seal)",
   {"seal": "12 in x 5 mm (documented class)"}, "https://www.aiesealer.com/", "Uline / AIE distributor", 1, "boxed dry mixes",
   {"usd": 900, "src": "estimate"}, [600, 500, 1100], "estimate", "120 V", 0)
eq("TJ-505", "Pack station B", "Thermal inkjet coder for pouch, tub lid and carton (lot + best-by)", "Videojet", "8610 TIJ",
   {"speed": "up to 102 m/min (documented)"}, "https://www.videojet.com/us/homepage/industry-solutions/cosmetic-personal-home-care-hub/ss-8610-lp.html",
   "Videojet (direct)", 1, "one station", {"usd": 6500, "src": "estimate"}, [300, 200, 300], "estimate", "120 V")
eq("CW-506", "Pack station B", "Verification bench scale 60 kg (NIST HB 133 lot sampling)", "Mettler-Toledo", "ICS685 bench scale, 60 kg (confirm)",
   {"capacity": "60 kg"}, "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/bench-scales/checkweigher/ICS685/ICS685k-count-6SM-f.html",
   MT, 1, "station B units are weighed by NW-501; this scale audits lots", {"usd": 3200, "src": "estimate"}, [600, 500, 900], "estimate", "120 V",
   confirm="model")

# ---------------------------------------------------------------- 600 controls and IT (detail in ELE-001/ELE-002)
eq("PLC-601", "Controls", "Blending-area controller (bag dump, salt, blender, sifter, MD, bag filler interlocks)", "Allen-Bradley",
   "CompactLogix 5380, 5069-L320ER", {"memory": "2 MB, 16 local I/O modules, 40 EtherNet/IP nodes (documented)"},
   "https://www.rockwellautomation.com/en-us/products/details.5069-l320er.html", RA, 1, "one per process area (ELE-001)",
   {"usd": 5200, "src": "estimate"}, [0, 0, 0], "in panel", "24 V DC")
eq("PLC-602", "Controls", "Pack line coordinator (line A state machine, recipe download, rejects, counts)", "Allen-Bradley",
   "CompactLogix 5380, 5069-L320ER", {"memory": "2 MB (documented)"}, "https://www.rockwellautomation.com/en-us/products/details.5069-l320er.html", RA, 1,
   "one per process area (ELE-001)", {"usd": 5200, "src": "estimate"}, [0, 0, 0], "in panel", "24 V DC")
eq("IO-603", "Controls", "Digital input module 16 ch 24 V DC", "Allen-Bradley", "5069-IB16", {"channels": "16 sink (documented)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/io/chassis-based-io/5069-compact-5000-i-o-modules.html", RA, 4,
   "I/O list ELE-002: 52 DI + 25% spare -> 4 x 16", {"usd": 420, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("IO-604", "Controls", "Digital output module 16 ch 24 V DC", "Allen-Bradley", "5069-OB16", {"channels": "16 source (documented)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/io/chassis-based-io/5069-compact-5000-i-o-modules.html", RA, 3,
   "I/O list ELE-002: 30 DO + 25% spare -> 3 x 16", {"usd": 460, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("IO-605", "Controls", "Analog input module 8 ch", "Allen-Bradley", "5069-IF8", {"channels": "8 V/mA (documented)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/io/chassis-based-io/5069-compact-5000-i-o-modules.html", RA, 1,
   "I/O list ELE-002: 5 AI (motor amps, DC dP, air pressure)", {"usd": 780, "src": "estimate"}, [0, 0, 0], "in panel")
eq("HMI-606", "Controls", "Operator HMI 10.1 in", "Allen-Bradley", "PanelView 5510, 2715P-T10CD", {"display": "10.1 in touch (documented class)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/operator-interface/panelview-5510.html", RA, 2,
   "blending panel CP-300, line panel CP-400", {"usd": 4300, "src": "estimate", "per": "each"}, [0, 0, 0], "panel door", "24 V DC")
eq("SR-607", "Controls", "Dual-channel safety relay for e-stop and guard circuits", "Allen-Bradley Guardmaster", "440R-S12R2",
   {"category": "up to PLe / Cat 4 (documented class)"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/safety-products/safety-relays.html",
   RA, 2, "one safety zone per area (ELE-001)", {"usd": 330, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("PS-608", "Controls", "24 V DC power supply 10 A", "Allen-Bradley", "1606-XLE240E", {"output": "24 V DC 10 A (documented class)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/power-supplies.html", RA, 2, "one per control panel",
   {"usd": 260, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("SWI-609", "Controls", "Managed Ethernet switch 8 port", "Allen-Bradley", "Stratix 2500, 1783-LMS8", {"ports": "8 x 10/100 (documented class)"},
   "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/network-security-and-infrastructure/ethernet-networks/stratix-2500.html",
   RA, 3, "one per panel + one at MES rack", {"usd": 480, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("ENC-610", "Controls", "Stainless Type 4X control enclosure 36x30x12 in", "nVent HOFFMAN", "CSD363012SS (confirm)",
   {"rating": "Type 4X 304 SS (documented class)"}, "https://hoffman.nvent.com/en-us/products/enclosures/wall-mount-enclosures", "Graybar / Rexel", 2,
   "CP-300 blending, CP-400 line", {"usd": 2100, "src": "estimate", "per": "each"}, [762, 305, 914], "estimate", confirm="part number")
eq("SRV-611", "Controls", "MES / line manager server (runs software/mes) + UPS", "Dell + APC", "PowerEdge T160 + APC Smart-UPS SMT1500RM2UC",
   {"os": "Ubuntu 24.04 LTS or Windows Server", "role": "recipes, batches, traceability, labels, OEE"}, "https://www.dell.com/en-us/shop/servers-storage-and-networking/sf/poweredge-tower-servers",
   "Dell / CDW", 1, "one plant server; nightly backup off-site", {"usd": 3600, "src": "estimate"}, [0, 0, 0], "IT closet", "120 V")

# ---------------------------------------------------------------- 700 food safety and sanitation tools
eq("FS-701", "Food safety", "ATP hygiene monitoring system (pre-op swabs)", "Hygiena", "EnSURE Touch + UltraSnap swabs",
   {"use": "pre-op verification of dry clean on contact surfaces"}, "https://www.hygiena.com/food-safety-solutions/atp-cleaning-verification/", "Hygiena (direct)", 1,
   "one QC lab", {"usd": 2400, "src": "estimate"}, [0, 0, 0], "QC lab")
eq("FS-702", "Food safety", "Gluten (wheat) allergen surface test", "Neogen", "Reveal 3-D for Gluten",
   {"use": "verify wet clean after wheat campaign before gluten-free seasonings run"}, "https://www.neogen.com/categories/allergens/reveal-3-d-gluten/",
   "Neogen (direct)", 1, "kit of 25 per month (consumable)", {"usd": 260, "src": "estimate", "per": "kit"}, [0, 0, 0], "QC lab")
eq("FS-703", "Food safety", "Combustible-dust rated industrial vacuum (dry clean, no compressed-air blow-down)", "Nilfisk",
   "VHC 200 Class II Div 2 / combustible dust version (confirm)", {"rating": "Class II Div 2 (confirm on quote)"},
   "https://www.nilfisk.com/en-us/products/industrial-vacuum-cleaners/", "Nilfisk distributor", 2, "blending room + packing hall",
   {"usd": 7800, "src": "estimate", "per": "each"}, [1100, 700, 1500], "estimate", "480 V 3-ph", confirm="model and certification")
eq("FS-704", "Food safety", "Color-coded hygienic hand tools (green = general, yellow = wheat area)", "Vikan", "Hygienic brushes, scoops, scrapers, shadow boards",
   {"system": "color coded per allergen zone"}, "https://www.vikan.com/us/", "Vikan distributor", 1, "one set per zone (4 zones)",
   {"usd": 2600, "src": "estimate"}, [0, 0, 0], "wall boards")
eq("FS-705", "Food safety", "Hands-free stainless hand sink (knee valve) at each entry", "Eagle Group", "HSA-10-FOW-LRS hand sink (confirm)",
   {"type": "hands-free"}, "https://www.eaglegrp.com/", "Restaurant/food-plant supply", 3, "hygiene vestibule, weigh room, packing hall",
   {"usd": 1100, "src": "estimate", "per": "each"}, [500, 400, 1100], "estimate", confirm="model")

# ---------------------------------------------------------------- 620 field devices and drives, quantities from io.json
_io = json.loads((pathlib.Path(__file__).parent / "io.json").read_text()) if (pathlib.Path(__file__).parent / "io.json").exists() else None
_n_fork = sum(1 for p in (_io or {}).get("io", []) if "HOPPER_HIGH" in p["tag"] or "HOPPER_LOW" in p["tag"])
_n_pe = (_io or {}).get("photo_eyes", 14)
_n_start = sum(1 for m in (_io or {}).get("motors", []) if m["starter"] == "starter" and m["panel"].startswith("CP"))
eq("VFD-620", "Controls", "AC drive 15 HP 480 V for RB-303 ribbon blender (soft start, EtherNet/IP)", "Allen-Bradley", "PowerFlex 525, 25B-D024N114 (confirm rating)",
   {"rating": "15 HP normal duty 480 V (confirm)"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/motion-control/low-voltage-ac-drives/powerflex-525.html",
   RA, 1, "io.json motor M-304", {"usd": 2900, "src": "estimate"}, [0, 0, 0], "in panel")
eq("VFD-621", "Controls", "AC drive 5 HP 480 V for PM-210 V-cone blender", "Allen-Bradley", "PowerFlex 525, 25B-D010N114 (confirm rating)",
   {"rating": "5 HP 480 V (confirm)"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/motion-control/low-voltage-ac-drives/powerflex-525.html",
   RA, 1, "io.json motor M-307", {"usd": 1500, "src": "estimate"}, [0, 0, 0], "in panel")
eq("VFD-622", "Controls", "AC drive 0.5 HP 480 V for CV-417 conveyor zones", "Allen-Bradley", "PowerFlex 525, 25B-D1P4N114 (confirm rating)",
   {"rating": "0.5 HP 480 V (confirm)"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/motion-control/low-voltage-ac-drives/powerflex-525.html",
   RA, 4, "io.json motors M-402..M-405", {"usd": 900, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("MS-623", "Controls", "Motor protection breaker + contactor (across-the-line starters)", "Allen-Bradley", "140MT-C3E (range per FLA) + 100-C09D10, confirm ranges",
   {"use": "motors listed as 'starter' in io.json"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/circuit-and-load-protection/motor-circuit-protectors.html",
   RA, _n_start, "io.json: motors with across-the-line starters in CP-300/CP-400", {"usd": 260, "src": "estimate", "per": "each"}, [0, 0, 0], "in panel")
eq("LS-624", "Controls", "Vibrating-fork level switch for powders (hopper high/low)", "Endress+Hauser", "Soliphant FTM20",
   {"use": "bulk solids level detection (documented product family)"}, "https://www.endress.com/en/field-instruments-overview/level-measurement/point-level-vibronic-sensor-soliphant-ftm20",
   "Endress+Hauser (direct) or distributor", _n_fork, "io.json: one per HOPPER_HIGH / HOPPER_LOW point", {"usd": 650, "src": "estimate", "per": "each"}, [0, 0, 0], "on hoppers",
   sanitary="sanitary process connection on product-contact hoppers")
eq("PE-625", "Controls", "Polarized retroreflective photo-eye with reflector, 18 mm", "Banner Engineering", "QS18VP6LP + BRT-32X20AM reflector",
   {"range": "polarized retro, ignores shiny PET (documented family)"}, "https://www.bannerengineering.com/us/en/products/sensors/photoelectric-sensors/world-beam-qs18-series.html",
   "Banner distributor", _n_pe, "io.json: one per PExxx point; mounted on DH-105", {"usd": 110, "src": "estimate", "per": "each"}, [0, 0, 0], "on DH-105 brackets")
eq("ES-626", "Controls", "Emergency stop push button, 40 mm, 2 NC, with SS enclosure", "Allen-Bradley", "800FP-MT44PX02 + 800F-1YP3 enclosure (confirm)",
   {"contacts": "2 NC to SR-607 dual channel"}, "https://www.rockwellautomation.com/en-us/products/hardware/allen-bradley/push-buttons-and-signaling-devices/22mm-push-buttons/800f-push-buttons.html",
   RA, 12, "4 in blending (bag dump, BBD, blender platform, bag filler) + 8 along line A and station B, spaced <= 10 m", {"usd": 140, "src": "estimate", "per": "each"}, [0, 0, 0], "field")
eq("PT-627", "Controls", "Plant air pressure transmitter 0-200 psi 4-20 mA", "Endress+Hauser", "Cerabar PMP21",
   {"output": "4-20 mA"}, "https://www.endress.com/en/field-instruments-overview/pressure-measurement/absolute-gauge-pmp21", "Endress+Hauser distributor", 1,
   "io.json AC311_PRESS", {"usd": 420, "src": "estimate"}, [0, 0, 0], "air header")
eq("DP-628", "Controls", "Dust collector filter dP transmitter 0-10 in w.c.", "Dwyer", "Series 616KD differential pressure transmitter",
   {"output": "4-20 mA"}, "https://www.dwyer-inst.com/en/products/pressure-transmitters", "Dwyer distributor", 1, "io.json DC310_DP",
   {"usd": 260, "src": "estimate"}, [0, 0, 0], "DC-310")


def footprint_area_m2():
    return sum(e["footprint_mm"][0] * e["footprint_mm"][1] / 1e6 * (e["qty"] if e["footprint_mm"][0] else 0) for e in E)


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    st = here / "storage.json"
    if st.exists():                        # rack bay count is traced to the storage calculation
        n = json.loads(st.read_text())["total_bays"]
        for e in E:
            if e["tag"] == "WH-102":
                e["qty"] = n
                e["qty_basis"] = f"storage.json: raw 2 weeks + packaging 1 week + finished goods 3 days = {n} bays of 8 positions"
    if _io:                                # I/O module counts are traced to the I/O list (25% spare)
        m = _io["modules"]
        for tag, typ in (("IO-603", "DI"), ("IO-604", "DO"), ("IO-605", "AI")):
            q = m[f"601-{typ}"]["modules"] + m[f"602-{typ}"]["modules"]
            pts = m[f"601-{typ}"]["points"] + m[f"602-{typ}"]["points"]
            for e in E:
                if e["tag"] == tag:
                    e["qty"] = q; e["qty_basis"] = f"io.json: {pts} {typ} points + 25% spare -> {q} modules"
    (here / "equipment.json").write_text(json.dumps(E, indent=1))
    tot = sum(e["price"]["usd"] * (e["qty"] if "per" in e["price"] else 1) for e in E)
    print(len(E), "line items; budget (estimates, not quotes) ~ $", round(tot / 1000), "k")
