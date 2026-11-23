from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def cube_stl(tmp_path: Path) -> Path:
    """A 20 mm cube: a 3D part that should be printed."""
    import trimesh

    path = tmp_path / "cube.stl"
    trimesh.creation.box(extents=(20, 20, 20)).export(path)
    return path


@pytest.fixture
def plate_stl(tmp_path: Path) -> Path:
    """A 60 x 40 x 3 mm plate with a round hole: a flat part for the laser."""
    import trimesh
    from shapely.geometry import Point, Polygon

    outline = Polygon([(0, 0), (60, 0), (60, 40), (0, 40)]).difference(Point(30, 20).buffer(5))
    mesh = trimesh.creation.extrude_polygon(outline, height=3.0)
    path = tmp_path / "plate.stl"
    mesh.export(path)
    return path


@pytest.fixture
def big_stl(tmp_path: Path) -> Path:
    import trimesh

    path = tmp_path / "big.stl"
    trimesh.creation.box(extents=(300, 50, 50)).export(path)
    return path


@pytest.fixture
def square_dxf(tmp_path: Path) -> Path:
    """A 100 mm square with a 20 mm circle cut out, in millimetres."""
    import ezdxf

    doc = ezdxf.new(units=4)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (100, 0), (100, 100), (0, 100)], close=True)
    msp.add_circle((50, 50), radius=10)
    path = tmp_path / "square.dxf"
    doc.saveas(path)
    return path
