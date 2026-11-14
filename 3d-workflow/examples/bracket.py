length, width, thickness = 60.0, 30.0, 4.0
flange_h = 25.0
hole_d, hole_inset = 5.5, 10.0
fillet_r = 3.0

base = cq.Workplane("XY").box(length, width, thickness, centered=(True, True, False))
flange = (cq.Workplane("XY").box(length, thickness, flange_h, centered=(True, False, False))
          .translate((0, -width / 2, 0)))
result = (base.union(flange).edges("|X and >Z and <Y").fillet(fillet_r)
          .faces(">Z").workplane()
          .pushPoints([(-length / 2 + hole_inset, 3), (length / 2 - hole_inset, 3)])
          .hole(hole_d))
