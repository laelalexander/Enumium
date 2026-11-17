"""Phase 1 prototype equipment: 1,000 lb a week, semi-automatic, fabricate wherever it is safe.

Rule for buy vs fabricate (written into the package so it can be argued with):
  BUY   anything that is a CCP or a legal measurement (metal detector, scales), anything whose
        accuracy comes from precision machining or electronics (auger tooling, induction sealer,
        labeler, printers), and the blender agitator (a ribbon is costly to make and to validate).
  BUILD stainless frames, tables, hoods, chutes, the sieve deck, carts and turntables (a local
        stainless fabricator or in-house TIG), plus 3D-printed jigs, nests and grips that never
        touch product. No 3D-printed part touches product: printed plastic is porous and cannot
        be validated clean.
Prices: estimate unless src says documented/listing. Used-market prices are from live listings
on 2026-11-17 and change daily. Running this file writes equipment.json.
"""
import json, pathlib

HERE = pathlib.Path(__file__).parent
E = []
MT = "Mettler-Toledo (direct, mt.com) or authorized dealer"


def eq(tag, area, name, maker, model, specs, source, supplier, qty, qty_basis, price, footprint, fp_src,
       power=None, sanitary="", kind="buy", contact=False, dust_cfm=0, confirm="", growth_equiv="", build=None, reuse_in_growth=False):
    E.append(dict(tag=tag, area=area, name=name, maker=maker, model=model, specs=specs, source=source, supplier=supplier, qty=qty,
                  qty_basis=qty_basis, price=price, footprint_mm=footprint, footprint_src=fp_src, power=power, air_cfm=0,
                  sanitary=sanitary, alternates=[], rate=None, kind=kind, product_contact=contact, dust_cfm=dust_cfm, confirm=confirm,
                  growth_equiv=growth_equiv, build=build, reuse_in_growth=reuse_in_growth))


def fab(drawing, material, mat_usd, labor_h, process, files):
    return dict(drawing=drawing, material=material, material_usd=mat_usd, labor_h=labor_h, process=process, files=files)


# ---------------------------------------------------------------- 100 receiving and storage
eq("P1-101", "Receiving", "Low-profile pallet floor scale 1,000 lb with indicator (verify inbound weights)", "Rice Lake Weighing Systems",
   "RoughDeck QC 4x4 ft, 1,000 lb x 0.2 lb + 482 Legend indicator (confirm)", {"capacity": "1,000 lb (estimate of size chosen)"},
   "https://www.ricelake.com/products/floor-scales/", "Rice Lake dealer", 1, "one receiving point", {"usd": 2600, "src": "estimate"},
   [1219, 1219, 90], "estimate", "120 V", "painted platform, Z1 only", growth_equiv="RCV-101", reuse_in_growth=True)
eq("P1-102", "Storage", "NSF wire shelving unit 24x60x74 in, 4 shelves", "InterMetro", "Super Erecta 2460NC + 74P posts (confirm)",
   {"load": "800 lb per shelf, NSF (documented class)"}, "https://www.emerson.com/en-us/catalog/metro-super-erecta", "WebstaurantStore / Metro dealer",
   6, "storage.json: raw 2 weeks + packaging 1 week + finished 3 days in shelves and floor pallets", {"usd": 420, "src": "estimate", "per": "each"},
   [1524, 610, 1880], "documented", None, "NSF, 6 in off the floor, 18 in from walls for pest inspection")
eq("P1-103", "Storage", "Manual pallet truck 5,500 lb", "Crown", "PTH 50 hand pallet truck", {"capacity": "5,500 lb (documented class)"},
   "https://www.crown.com/en-us/forklifts/hand-pallet-truck.html", "Crown dealer", 1, "one dock", {"usd": 650, "src": "estimate"}, [1550, 690, 1220], "estimate")

# ---------------------------------------------------------------- 200 weigh and dispense
eq("P1-201", "Weigh & dispense", "Bench scale 60 kg for majors (legal for trade, SICS)", "Mettler-Toledo", "ICS685 bench scale, 60 kg (ICS685k-60LA/f, confirm)",
   {"readability": "10 g class (documented family)", "interface": "MT-SICS over Ethernet option (documented family)"},
   "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/Terminals-and-Controllers/bench-scales/ICS685.html", MT, 1,
   "one weigh station", {"usd": 3600, "src": "estimate"}, [500, 400, 120], "estimate", "120 V", "SS platform", growth_equiv="WS-202", reuse_in_growth=True)
eq("P1-202", "Weigh & dispense", "Precision scale 6 kg x 0.1 g for minors (< 2 %)", "Mettler-Toledo", "ICS685s-6 precision (confirm)",
   {"readability": "0.1 g (site scale_resolution_g)"}, "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/Terminals-and-Controllers/bench-scales/ICS685.html",
   MT, 1, "site rule: minors to 0.1 g", {"usd": 3900, "src": "estimate"}, [350, 300, 120], "estimate", "120 V", "SS pan", growth_equiv="WS-203", reuse_in_growth=True)
eq("P1-203", "Weigh & dispense", "Cordless barcode scanner (lot scan of every bag)", "Zebra", "DS3678-SR rugged cordless",
   {"rating": "IP65/IP67 (documented)"}, "https://www.zebra.com/us/en/products/scanners/ultra-rugged-scanners/ds36x8.html", "CDW / Zebra partner",
   2, "weigh station + pack bench", {"usd": 520, "src": "estimate", "per": "each"}, [0, 0, 0], "estimate", growth_equiv="WS-205", reuse_in_growth=True)
eq("P1-204", "Weigh & dispense", "Desktop thermal transfer printer: bag, batch and case labels (ZPL)", "Zebra", "ZD421t 203 dpi (ZD4A042-301M00EZ, confirm)",
   {"width": "4 in (documented)", "language": "ZPL (documented)"}, "https://www.zebra.com/us/en/products/printers/desktop/zd400-series.html", "CDW / Zebra partner",
   1, "one printer serves weigh, blend and pack-off", {"usd": 650, "src": "estimate"}, [230, 200, 180], "documented")
eq("P1-205", "Controls", "MES computer + 24 in touch monitor + UPS (runs software/mes, Phase 1 config)", "Dell + APC", "OptiPlex Micro + P2424HT + APC BX1500M",
   {"os": "Linux or Windows, Python 3.11+"}, "https://www.dell.com/en-us/shop/desktop-computers/sc/optiplex-desktops", "Dell", 1, "one plant",
   {"usd": 1600, "src": "estimate"}, [0, 0, 0], "estimate", "120 V", "monitor in a wipe-clean cover in Z3")
eq("P1-206", "Weigh & dispense", "Weigh bench with backdraft dust hood (stainless)", "fabricated", "drawing P1-206 (table) + P1-207 (hood)",
   {"top": "1524 x 762 mm [60 x 30 in], 900 mm [35.4 in] high", "hood": "slot hood 300 cfm"}, "cad/p1_parts.py", "local stainless fabricator or in-house TIG",
   1, "one weigh station", {"usd": 0, "src": "see build"}, [1524, 762, 1600], "calculated", None, "304 #4 top, sealed welds, no hollow legs open at the top",
   kind="build", contact=True, dust_cfm=300, build=fab("P1-206, P1-207", "304 SS 14 ga sheet, 1.5 in sq tube", 780, 14, "laser cut, brake, TIG", ["dxf/P1-206_top", "dxf/P1-207_front"]))
eq("P1-208", "Weigh & dispense", "Premix pail tumbler (minors + carrier salt in a sealed SS pail on driven rollers)", "fabricated", "drawing P1-208; bought pail and gearmotor",
   {"pail": "Vollrath 5 qt SS (bought)", "speed": "30 rpm rollers"}, "cad/p1_parts.py", "in-house", 1, "replaces the PM-210 V-cone at this scale",
   {"usd": 0, "src": "see build"}, [600, 400, 300], "calculated", "120 V, 1/8 HP", "pail is the only product-contact part (bought SS)", kind="build",
   build=fab("P1-208", "304 SS 11 ga plate, 2 x UHMW rollers, 1/8 HP gearmotor", 520, 8, "laser cut, brake, TIG; lathe the rollers", []))

# ---------------------------------------------------------------- 210 ingredient bins and metered dosing (client 2026-11-17: "silo these spices")
eq("P1-210", "Dosing", "Ingredient bin ring frame, 12 positions around the weigh hopper", "fabricated", "drawing P1-210",
   {"positions": "12 (9 used at launch, 3 for growth: dosing-plan.md)"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one dosing station",
   {"usd": 0, "src": "see build"}, [3330, 3330, 2235], "calculated", None, "no product contact; closed tube ends", kind="build",
   build=fab("P1-210", "304 SS 2 in sq tube 11 ga ~70 m, 12 foot plates, 3 load-cell mount plates", 2800, 48, "saw, TIG, passivate", ["cad/step/P1-210"]))
eq("P1-211", "Dosing", "Ingredient bin 5 cu ft with hinged lid and bag-rest grate", "fabricated", "drawing P1-211",
   {"volume": "141 L working", "outlet": "120 sq to feeder"}, "cad/p1_parts.py", "local stainless fabricator", 9,
   "dosing-plan.md: 9 bins used at launch (salt, garlic, paprika, onion, black pepper, coarse pepper, cayenne, lemon peel, red pepper)",
   {"usd": 0, "src": "see build"}, [680, 680, 686], "calculated", None, "304 #4, welds ground, lid gasket FDA silicone", kind="build", contact=True,
   build=fab("P1-211", "304 SS 14 ga ~2.2 m2 + 6 mm flanges + hinge + FDA gasket", 380, 9, "laser cut, brake, TIG, passivate", ["dxf/P1-211_flange"]))
eq("P1-212", "Dosing", "Volumetric screw feeder, 2 in, stainless, with agitator option for low-density herbs", "Tecweigh",
   "Volumetric feeder, 2 in screw, SS contact (model per hopper flange, confirm on quote)",
   {"rate": "~700 L/h at max rpm (estimate, maker class)", "drive": "0.5 HP gearmotor"}, "https://www.tecweigh.com/products/volumetric-feeders",
   "Tecweigh (White Bear Lake MN)", 9, "one per used bin; 3 more positions bought at growth", {"usd": 4800, "src": "estimate", "per": "each"},
   [900, 300, 350], "estimate", "230 V 3-ph via VFD", "tool-free screw removal; agitator on lemon peel and herb bins", contact=True,
   confirm="test-feed salt, garlic and lemon peel samples at Tecweigh; ask for a used-unit price (listings exist)")
eq("P1-213", "Dosing", "Vibrating fork low-level switch for powders", "Endress+Hauser", "Soliphant FTM20", {"use": "bin low level = refill and run-empty marker"},
   "https://www.endress.com/en/field-instruments-overview/level-measurement/point-level-vibronic-ftm20", "Endress+Hauser", 9, "one per used bin",
   {"usd": 520, "src": "estimate", "per": "each"}, [0, 0, 0], "estimate", "24 V DC", "316L fork, 1.5 in Tri-Clamp process connection (sanitary option)",
   contact=True, growth_equiv="LS-624")
eq("P1-214", "Dosing", "Flexible snap-fit connector feeder spout to hopper inlet (scale isolation)", "BFM Global", "BFM fitting, 100 mm, Seeflex 040E (confirm size)",
   {"material": "FDA polyether urethane (documented class)"}, "https://www.bfmfitting.com/", "BFM Global distributor", 9, "one per feeder",
   {"usd": 140, "src": "estimate", "per": "each"}, [0, 0, 0], "estimate", None, "tool-free, see-through", contact=True)
eq("P1-220", "Dosing", "Weigh hopper 141 L on 3 load cells (gain-in-weight dosing)", "fabricated", "drawing P1-220",
   {"capacity": "100 kg", "accuracy": "+/-20 g with fast/slow feed"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one dosing station",
   {"usd": 0, "src": "see build"}, [840, 840, 580], "calculated", None, "316L #4, ground welds", kind="build", contact=True, dust_cfm=150,
   build=fab("P1-220", "316L 14 ga ~2 m2 + 4 in BPE ferrule + 304 lugs", 620, 12, "laser cut, roll, TIG, polish, passivate", ["dxf/P1-220_lid"]))
eq("P1-221", "Dosing", "Weigh module (load cell + mount) 50 kg, stainless", "Mettler-Toledo", "SWB505 MultiMount + SLB615D cell, 50 kg (confirm)",
   {"capacity": "50 kg each, 3 per hopper", "class": "OIML C3 class (documented family)"}, "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/automation-and-oem/weigh-modules.html",
   MT, 3, "3-point hopper support", {"usd": 650, "src": "estimate", "per": "each"}, [0, 0, 0], "estimate", None, "IP68 SS")
eq("P1-222", "Dosing", "Weight indicator/controller with EtherNet/IP or Modbus TCP", "Rice Lake Weighing Systems", "880 Performance Series, panel mount",
   {"function": "setpoints, fast/slow cutoffs (documented class)"}, "https://ricelake.com/products/880-performance-series-digital-weight-indicator-and-controller",
   "Rice Lake dealer", 1, "one hopper", {"usd": 1500, "src": "estimate"}, [0, 0, 0], "estimate", "120 V")
eq("P1-223", "Dosing", "Sanitary butterfly valve 4 in Tri-Clamp with 24 V DC electric actuator and open/closed limit switches (PLC-operated)", "Valworx",
   "4 in sanitary butterfly valve 316L, EPDM seat, 24 V DC electric actuator with position switches (confirm model)",
   {"size": "4 in Tri-Clamp", "actuator": "24 V DC on/off, about 10 s stroke, 2 limit switches"}, "https://www.valworx.com/", "Valworx", 1, "weigh hopper outlet",
   {"usd": 1400, "src": "estimate"}, [300, 200, 350], "estimate", "24 V DC from P1-225", "FDA seat, Tri-Clamp both sides", contact=True)
eq("P1-224", "Dosing", "Flexible screw conveyor, weigh hopper to blender inlet, sanitary, with intake grate for hand adds", "Flexicon", "Flexible screw conveyor, 2.5 in, low-profile floor hopper with bag grate and dust collar, SS (confirm)",
   {"rate": "~1,000 L/h class (estimate)", "length": "~4.5 m, rising about 2.6 m to the blender inlet on P1-311", "intake": "bin charge from the weigh hopper valve, then hand adds and premix tipped at about 600 mm [24 in]"}, "https://flexicon.com/?p=14", "Flexicon (Bethlehem PA)", 1,
   "one dosing station", {"usd": 11000, "src": "estimate"}, [4000, 600, 1600], "estimate", "230/460 V 3-ph, 1 HP", "runs clear between formulas; tool-free screw pull",
   contact=True, growth_equiv="BD-301 flexible screw")
eq("P1-225", "Dosing", "Dosing controller: WAGO PFC200 (CODESYS) + I/O, SS enclosure, 24 V supply", "WAGO", "750-8212 + 2 x 750-1504 DO + 2 x 750-1405 DI + 750-600 end (confirm)",
   {"runtime": "CODESYS 3.5 (documented)", "program": "software/plc/DosingStation.st"}, "https://www.wago.com/pfc200", "WAGO distributor", 1,
   "one dosing station", {"usd": 2900, "src": "estimate incl. enclosure and 24 V supply"}, [600, 500, 250], "estimate", "120 V")
eq("P1-226", "Dosing", "Feeder drives: AC drive 0.5 HP for each feeder (fast/slow dosing)", "AutomationDirect", "DURApulse GS20, 0.5 HP (GS21-20P5, confirm)",
   {"control": "Modbus TCP/RTU or digital speed select"}, "https://www.automationdirect.com/adc/overview/catalog/drives_-a-_soft_starters/ac_variable_frequency_drives_(vfd)",
   "AutomationDirect", 9, "one per feeder", {"usd": 190, "src": "estimate", "per": "each"}, [0, 0, 0], "estimate", "230 V")
eq("P1-227", "Dosing", "Rolling 4-step platform for loading bins (40 in top step, handrails both sides)", "Cotterman",
   "4-step rolling ladder, 40 in top step, 24 in wide, handrails, OSHA/ANSI A14.7 (confirm)", {"reach": "bin rim 2,392 mm is about 1.38 m above the top step"},
   "https://www.cotterman.com/", "Grainger", 1, "bin loading", {"usd": 1100, "src": "estimate"}, [1300, 800, 1900], "estimate",
   confirm="bags over 1.4 m: use the bag-rest grate on each bin lid, or add a vacuum bag lifter if lifting assessment requires")

# ---------------------------------------------------------------- 300 blending
eq("P1-301", "Blending", "Ribbon blender, 6 cu ft working, 304 SS (used, inspected)", "Sprout-Waldron / Paul O. Abbe class (used market)",
   "6 cu ft double ribbon blender, 304 SS, 2 HP (example listing: Sprout-Waldron B-6, 21 x 48 in trough)",
   {"capacity": "6 cu ft (listing)", "trough": "21 in W x 48 in L (listing)", "motor": "2 HP, 27 rpm (listing)"},
   "https://surplusrecord.com/es/listing/6-cu-ft-sprout-waldron-b-6-stainless-steel-jacketed-double-ribbon-blender-21-width-x-48-l-flange-14-9-psi-5-discharge-2-hp-27-rpm-431930/",
   "Surplus Record dealers / Genemco / Federal Equipment (used)", 1, "line balance: 6 cu ft, 7 batches/week, 18 % loaded; 13-blend growth fits",
   {"usd": 9000, "src": "estimate: used 304 SS 5-6 cu ft listings $5-9k + inspection, seals, repolish"}, [1600, 760, 1500], "estimate",
   "230/460 V 3-ph, 2 HP (single-phase input VFD if no 3-ph)", "inspect welds and shaft seals; repolish contact to #4 if pitted; new FDA packing",
   contact=True, confirm="see it run first: no pitting, seals replaceable, discharge valve works; measure cover opening and valve flange for P1-302/P1-303",
   growth_equiv="RB-303")
eq("P1-311", "Blending", "Blender riser stand: lifts the blender so its valve clears chute + sieve + 55 gal drum", "fabricated", "drawing P1-311",
   {"height": "1,150 mm [45.3 in] to the blender's leg feet (VERIFY on the used unit)", "load": "blender ~450 kg + 70 kg batch, x3 design factor"},
   "cad/p1_parts.py", "local stainless fabricator", 1, "one blender", {"usd": 0, "src": "see build"}, [1700, 860, 1150], "calculated", None,
   "304, all tube ends capped and seal-welded; not product contact", kind="build",
   build=fab("P1-311", "304 SS 3 in sq tube 11 ga ~14 m, 4 x 12 mm foot plates, 4 leg pads", 650, 16, "saw, TIG, ground, passivate", ["dxf/P1-311_foot"]))
eq("P1-302", "Blending", "Blender cover grate and dust hood (vent pickup on the blender inlet)", "fabricated", "drawing P1-302",
   {"grate": "50 mm [2 in] bar spacing, bag rest", "pickup": "250 cfm, 4 in collar"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one blender",
   {"usd": 0, "src": "see build"}, [700, 500, 450], "calculated", None, "304 #4, removable without tools for cleaning", kind="build", contact=True, dust_cfm=250,
   build=fab("P1-302", "304 SS 14 ga + 10 mm bar", 340, 10, "laser cut, brake, TIG", ["dxf/P1-302_grate"]))
eq("P1-303", "Blending", "Blender discharge chute to sieve (scaled DH-101)", "fabricated", "drawing P1-303",
   {"outlet": "4 in Tri-Clamp ferrule (bought)"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one blender", {"usd": 0, "src": "see build"},
   [200, 200, 220], "calculated", None, "316L contact, ground welds", kind="build", contact=True,
   build=fab("P1-303", "316L 14 ga + 4 in BPE ferrule", 210, 6, "laser cut, roll, TIG, polish", ["dxf/P1-303_flange"]),
   confirm="match the used blender's valve flange before cutting")
eq("P1-304", "Blending", "Vibratory sieve deck on leg frame (12 mesh screen, grate magnet under the screen)", "fabricated", "drawing P1-304; bought screen, vibrator and magnet",
   {"rate": "8 lb/min design (line balance)", "screen": "18 in round 12 mesh SS"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one blending train",
   {"usd": 0, "src": "see build"}, [700, 700, 1100], "calculated", "120 V vibrator", "screen and hopper tool-free removal", kind="build", contact=True, dust_cfm=200,
   build=fab("P1-304", "304 SS 14 ga sheet, 1.5 in tube legs, rubber isolators", 460, 12, "laser cut, roll, TIG", ["cad/step/P1-304"]), growth_equiv="SC-304")
eq("P1-305", "Blending", "Sieve screen 18 in, 12 mesh stainless, with frame", "Gilson", "18 in sieve 12 mesh, SS frame (V18SS12 class, confirm)",
   {"mesh": "12 (site sifter spec)"}, "https://www.globalgilson.com/18in-sieves", "Gilson Company", 2, "one in use + one spare (screen check each shift)",
   {"usd": 290, "src": "estimate", "per": "each"}, [457, 457, 100], "documented", None, "inspect for tears each shift", contact=True)
eq("P1-306", "Blending", "Rotary electric vibrator motor for sieve deck", "Martin Engineering", "CDX/MGR small electric vibrator (confirm size for 30 kg deck)",
   {"force": "~150 lbf class (estimate)"}, "https://www.martin-eng.com/content/product/690/electric-vibrators", "Martin Engineering", 1, "one sieve deck",
   {"usd": 750, "src": "estimate"}, [200, 120, 120], "estimate", "120 V 1-ph")
eq("P1-307", "Blending", "Grate magnet 12 x 12 in, rare earth, on brackets under the sieve screen", "Industrial Magnetics, Inc.", "Grate magnet 12 x 12 in, 1 in tubes, no housing, 10,000 gauss class (confirm)",
   {"strength": "10,000 G class (estimate)"}, "https://www.magnetics.com/product.asp?ProductID=24", "IMI", 1, "one train (prerequisite, not the CCP)",
   {"usd": 650, "src": "estimate"}, [305, 305, 50], "estimate", None, "pull and wipe each batch; record finds", contact=True)
eq("P1-308", "Blending", "Lidded food-grade blend drum 55 gal, open top, with liner (one batch per drum, QC hold container)", "Uline",
   "55 gallon plastic drum, open top, with lever-lock lid, 23 x 36 in (confirm SKU)",
   {"volume": "55 gal (208 L); a 147 lb [66.7 kg] batch at 0.51 g/mL is 131 L, 63 % full"}, "https://www.uline.com/BL_1525/Plastic-Drums", "Uline", 6,
   "7 batches/week, one drum per batch, held up to 1 day for QC: 1 filling, 2 in hold, 1 at the filler, 2 spare", {"usd": 120, "src": "estimate", "per": "each"},
   [584, 584, 914], "estimate", None, "FDA-grade HDPE + poly liner per batch", contact=True)
eq("P1-309", "Blending", "Drum dolly with lift handle (stainless)", "fabricated", "drawing P1-309",
   {"load": "250 lb", "fits": "55 gal drum Ø584 [23 in]"}, "cad/p1_parts.py", "in-house", 3, "one under the sieve, one in hold, one at the filler", {"usd": 0, "src": "see build"}, [640, 640, 130], "calculated",
   kind="build", build=fab("P1-309", "304 SS 11 ga + 4 x 3 in SS casters (bought, Colson 2 series)", 140, 3, "laser cut, brake, TIG", ["dxf/P1-309_base"]))
eq("P1-320", "Grinding", "Small sanitary hammer mill on stand: grinds whole peppercorns, chiles and leaf herbs to size in house", "Schutte-Buffalo Hammermill",
   "Mini Mill class lab/pilot hammer mill, 2 HP, stainless contact parts, interchangeable screens (confirm model and screen set)",
   {"rate": "50-150 lb/h on pepper at 1/8 in screen (maker class, estimate)", "need": "coarse black pepper about 50 lb/week at launch, 1 h/week",
    "screens": "1/16, 1/8 and 3/16 in perforated, SS", "temperature": "batch under 20 min so the spice stays below 40 °C (volatile oils)"},
   "https://www.hammermills.com/", "Schutte-Buffalo (Buffalo NY)", 1, "one mill; whole spices are optional at launch (buy ground if deferred)",
   {"usd": 9500, "src": "estimate: new pilot-scale mill with stand"}, [900, 700, 1500], "estimate", "230 V 1-ph or 208 V 3-ph, 2 HP",
   "SS contact, tool-free screen and hammer access, dry clean between spices", kind="buy", contact=True, dust_cfm=150,
   confirm="grind trial with our peppercorns before ordering: particle size, heat rise, rate")
eq("P1-321", "Grinding", "Grate magnet in the mill feed throat (tramp metal ahead of the mill, NFPA 61 ignition control)", "Industrial Magnetics, Inc.",
   "Grate-in-housing 6 x 6 in, rare earth, 1 in tubes (confirm to mill inlet)", {"strength": "10,000 gauss class"}, "https://www.magnetics.com/",
   "IMI", 1, "one mill", {"usd": 450, "src": "estimate"}, [200, 200, 120], "estimate", None, "pull-out tubes, wipe clean each run", contact=True)
eq("P1-322", "Grinding", "Mill feed hopper and discharge chute to a lined drum (stainless, fabricated)", "fabricated", "drawing P1-322",
   {"feed": "10 L hopper with magnet slot", "discharge": "4 in Tri-Clamp to a cotton sock into a lined 5 gal pail (about 10 kg), tipped into bin B06"}, "cad/p1_parts.py", "local stainless fabricator", 1, "one mill",
   {"usd": 0, "src": "see build"}, [400, 400, 700], "calculated", None, "304 #4, welds ground, opens without tools", kind="build", contact=True,
   build=fab("P1-322", "304 SS 14 ga + 4 in BPE ferrule", 230, 8, "laser cut, brake, TIG, polish", ["dxf/P1-322_flange"]))
eq("P1-310", "Utilities", "Portable cartridge dust collector (weigh hood, blender hood, sieve, mill)", "Camfil APC", "Gold Series small cartridge collector (confirm >= 1,400 cfm model)",
   {"airflow": "1,050 cfm pickups (weigh hood 300, blender grate 250, sieve 200, weigh hopper vent 150, mill 150) + 25 % = 1,313 cfm, checked by foodsafety.py", "design_cfm": 1400}, "https://camfilapc.com/?p=3400", "Camfil APC", 1,
   "all five pickups", {"usd": 14000, "src": "estimate"}, [1200, 900, 2400], "estimate", "120/240 V 1-ph",
   "small dust quantity, but a DHA (NFPA 652) is still required; collector outside the room or vented per DHA", confirm="DHA first")

# ---------------------------------------------------------------- 400 packing (one semi-automatic bench)
eq("P1-401", "Pack bench", "Semi-automatic servo auger filler with weighing, foot pedal", "VTOPS", "Semi-automatic auger filler, 10-5,000 g, servo (model per tooling, confirm)",
   {"range": "10-5,000 g (maker class)", "rate": "15 upm operator-paced (estimate)"}, "https://vtops.com/filling-machines/auger-fillers/semi-automatic-auger-fillers",
   "VTOPS (US office)", 1, "line balance: 80 % at peak, 42 % of the week", {"usd": 11500, "src": "estimate"}, [700, 600, 1800], "estimate", "120/240 V 1-ph",
   "304 SS contact, tool-free hopper and auger", contact=True, dust_cfm=0, confirm="auger tooling for 53 mm shaker, 89 mm jar, pouch and tub on the quote",
   growth_equiv="NW-501 (moves to station B in Growth)", reuse_in_growth=True)
eq("P1-402", "Pack bench", "Cap torque tester (verify hand-capped torque each hour)", "Mark-10", "TT01 cap torque tester, 10 lbf-in (confirm range)",
   {"range": "to 10 lbF-in class (confirm)"}, "https://mark-10.com/products/torque-testers/", "Mark-10", 1, "QC check of hand capping",
   {"usd": 1400, "src": "estimate"}, [300, 300, 200], "estimate", "battery")
eq("P1-403", "Pack bench", "Handheld induction cap sealer, specialty head to 120 mm for the 89 mm jar", "Enercon", "Super Seal Jr + optional 120 mm head",
   {"caps": "to 83 mm standard head, to 120 mm optional head (documented)", "power": "120 VAC 60 Hz (documented)"},
   "https://www.enerconind.com/sealing/cap-sealers/super-seal-jr.aspx", "Enercon", 1, "one bench", {"usd": 4800, "src": "estimate"},
   [76, 210, 267], "documented", "120 V", growth_equiv="IS-405")
eq("P1-404", "Pack bench", "Semi-automatic wrap labeler for round containers", "Primera Technology", "AP360e label applicator",
   {"containers": "round, cylindrical (documented)"}, "https://www.onlinelabels.com/articles/reviewing-the-primera-ap360-label-applicator?src=1", "Primera dealer",
   1, "one bench", {"usd": 1500, "src": "estimate"}, [500, 400, 300], "estimate", "120 V")
eq("P1-405", "Pack bench", "Color label printer: full labels with lot and best-by printed per run (no separate coder)", "Primera Technology",
   "LX910 color label printer (pigment ink, confirm water resistance on chosen stock)", {"width": "to 8.25 in (documented class)"},
   "https://www.primera.com/lx910-color-label-printer.html", "Primera dealer", 1, "one bench", {"usd": 2500, "src": "estimate"}, [500, 450, 270], "estimate", "120 V")
eq("P1-406", "Pack bench", "Conveyor metal detector with reject (CCP-1, on finished packs)", "Fortress Technology", "Stealth with conveyor, ~10 x 6 in aperture (used, Sigma Equipment)",
   {"aperture": "about 10 in W x 6 in H (listing class)"}, "https://www.sigmaequipment.com/equipment/model/fortress-technology/stealth/", "Sigma Equipment (used) or Fortress (new)",
   1, "CCP-1 on every pack", {"usd": 14000, "src": "estimate (used); new ~$30k"}, [1500, 600, 1100], "estimate", "120 V",
   "locked reject bin; validate with test wands per pack size", confirm="sensitivity test with the 12 oz jar (metallized liner) before buying",
   growth_equiv="MD-305 (Growth checks the blend; Phase 1 checks the pack)")
eq("P1-407", "Pack bench", "Checkweigh scale 15 kg with over/under lights (100 % weigh, NIST HB 133)", "Mettler-Toledo", "ICS425s-15 (confirm)",
   {"function": "checkweighing with tolerance lights (documented family)"}, "https://www.mt.com/us/en/home/products/Industrial_Weighing_Solutions/Terminals-and-Controllers/bench-scales.html",
   MT, 1, "every unit weighed; MES records", {"usd": 2200, "src": "estimate"}, [350, 300, 150], "estimate", "120 V", growth_equiv="CW-409 (manual here)")
eq("P1-408", "Pack bench", "Accumulation turntable 30 in (stainless disc on lazy-susan bearing)", "fabricated", "drawing P1-408",
   {"disc": "762 mm [30 in] 304 SS with 25 mm rim"}, "cad/p1_parts.py", "in-house", 1, "buffer between labeler and checkweigh",
   {"usd": 0, "src": "see build"}, [762, 762, 900], "calculated", None, kind="build",
   build=fab("P1-408", "304 SS 14 ga disc + 12 in steel lazy-susan bearing (bought) on a P1-206 table", 190, 4, "laser cut, roll rim, TIG", ["dxf/P1-408_disc"]))
eq("P1-409", "Pack bench", "Stainless work table 60 x 30 in (fill, cap, seal, label, pack)", "fabricated", "drawing P1-206 (same table)",
   {"top": "1524 x 762 mm"}, "cad/p1_parts.py", "local stainless fabricator", 4, "fill, cap/seal, label, case-pack stations", {"usd": 0, "src": "see build"},
   [1524, 762, 900], "calculated", None, "304 #4", kind="build",
   build=fab("P1-206", "304 SS 14 ga + 1.5 in sq tube + 4 adjustable bullet feet", 520, 6, "laser cut, brake, TIG", ["dxf/P1-206_top"]))
eq("P1-410", "Pack bench", "3D-printed fixtures: filler container nests, labeler guides, cap grips (no product contact)", "printed", "STL in cad/print/",
   {"material": "PETG, white (cleanable, food-area color code)"}, "cad/p1_parts.py", "Bambu printer (in-house)", 1, "one set per container size",
   {"usd": 0, "src": "see build"}, [0, 0, 0], "calculated", kind="build",
   build=fab("P1-410a..e", "PETG ~600 g", 15, 1, "3D print (slice in Bambu Studio)", ["cad/print"]))
eq("P1-411", "Pack bench", "Tape dispenser and hand stretch-wrap dispenser", "Uline", "H-150 tape gun + H-50 hand stretch wrap dispenser (confirm)",
   {}, "https://www.uline.com/", "Uline", 1, "one pack-off", {"usd": 90, "src": "estimate"}, [0, 0, 0], "estimate")

# ---------------------------------------------------------------- 700 food safety
eq("P1-701", "Food safety", "ATP hygiene monitoring (pre-op swabs)", "Hygiena", "EnSURE Touch + UltraSnap swabs", {}, "https://www.hygiena.com/", "Hygiena",
   1, "one plant", {"usd": 2200, "src": "estimate"}, [0, 0, 0], "estimate", growth_equiv="FS-701", reuse_in_growth=True)
eq("P1-702", "Food safety", "Combustible-dust rated vacuum (no compressed air cleaning)", "Nilfisk", "VHC120 Z22 (Class II Div 2 class, confirm)", {},
   "https://www.nilfisk.com/en-us/", "Nilfisk", 1, "one plant", {"usd": 6800, "src": "estimate"}, [700, 600, 1100], "estimate", "120 V", growth_equiv="FS-703", reuse_in_growth=True)
eq("P1-703", "Food safety", "Color-coded hygienic hand tools and shadow board", "Vikan", "brushes, scoops, scrapers (green set)", {}, "https://www.vikan.com/us/",
   "Vikan dealer", 1, "one set", {"usd": 450, "src": "estimate"}, [0, 0, 0], "estimate", growth_equiv="FS-704", reuse_in_growth=True)
eq("P1-704", "Food safety", "Hands-free hand sink at the room entry", "Eagle Group", "HSA-10-FOW-LRS (confirm)", {}, "https://www.eaglegrp.com/", "WebstaurantStore",
   1, "one entry", {"usd": 650, "src": "estimate"}, [400, 400, 600], "estimate", None, growth_equiv="FS-705", reuse_in_growth=True)


def cost(e):
    if e["kind"] == "build":
        b = e["build"]; return (b["material_usd"] + b["labor_h"] * LABOR) * e["qty"]
    p = e["price"]; return p["usd"] * (e["qty"] if p.get("per") else 1)


LABOR = 65.0   # $/h fabrication labor (assumed, local stainless shop rate)

if __name__ == "__main__":
    for e in E:
        e["ext_usd"] = round(cost(e), 2)
        if e["kind"] == "build":
            e["price"] = {"usd": round(cost(e) / e["qty"], 2), "src": f"build: material ${e['build']['material_usd']} + {e['build']['labor_h']} h x ${LABOR:.0f}", "per": "each"}
    (HERE / "equipment.json").write_text(json.dumps(E, indent=1))
    buy = sum(e["ext_usd"] for e in E if e["kind"] == "buy"); build = sum(e["ext_usd"] for e in E if e["kind"] == "build")
    print(len(E), "lines; buy $", round(buy), "build $", round(build), "total $", round(buy + build))
