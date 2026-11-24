"""The bundled design sources: Pyslate originals, game-icons.net art and NASA 3D print models."""

from __future__ import annotations

import gzip
import json
import re
from functools import lru_cache
from pathlib import Path

from . import originals
from . import shapes as S
from .catalog import LASER, PRINT, Design

DATA = Path(__file__).parent / "data"


def machine_for(w: float, h: float) -> str | None:
    """The smallest laser bed the layout fits on, as drawn (M2 426 x 320, X1 615 x 320)."""
    if w <= 416 and h <= 310:
        return "m2"
    if w <= 605 and h <= 310:
        return "x1"
    return None


class Originals:
    source = "pyslate"

    def __init__(self):
        self._fns = {}

    def designs(self):
        for slug, title, category, tags, summary, fn in originals.ENTRIES:
            self._fns[slug] = fn
            yield Design(slug=slug, title=title, summary=summary, category=category, process=LASER, source="pyslate",
                         license="pyslate", tags=list(tags), author="Pyslate", rank=0)

    @lru_cache(maxsize=256)
    def _shapes(self, slug: str) -> tuple:
        return tuple(self._fns[slug]())

    def shapes(self, design, variant=None):
        return [dict(s) for s in self._shapes(design.slug)]


# ---------------------------------------------------------------- game-icons.net

ICON_CATEGORIES = {
    "Animals": "bat bear beast bee beetle bird boar bull butterfly camel cat chicken cow crab crow deer dog dolphin dove "
               "dragonfly duck eagle elephant fish fox frog goat gorilla hedgehog horse hound jellyfish kangaroo koala lion "
               "lizard llama monkey moose mouse octopus owl ox panda parrot paw penguin pig rabbit raccoon ram rat raven "
               "rhinoceros scorpion seal shark sheep shrimp snail snake spider squid squirrel swan tiger toad turtle "
               "unicorn whale wolf worm feather horns hoof claw fang tentacle bunny kitten puppy insect ant mosquito",
    "Nature": "acorn tree leaf leaves flower rose tulip lotus sunflower mushroom cactus palm pine oak branch plant seed "
              "sprout grass vine forest mountain sun moon star cloud rain snow snowflake lightning wind wave fire flame "
              "water drop rock stone crystal volcano island rainbow tornado ice clover herb berry",
    "Fantasy and magic": "dragon wizard witch magic spell potion rune wand ghost skull zombie vampire demon devil angel "
                         "fairy elf orc goblin troll monster beholder crystal-ball pentacle portal curse totem mage "
                         "necromancer specter haunting tentacle cthulhu kraken griffin phoenix hydra minotaur medusa",
    "Food and drink": "apple banana bread cake candy carrot cheese cherry chocolate coffee cookie corn cupcake donut "
                      "egg fruit grapes hamburger honey ice-cream lemon meat milk orange pear pepper pie pizza pumpkin "
                      "sandwich sausage strawberry sushi tea tomato watermelon wine beer bottle cup mug glass teapot",
    "Weapons and armour": "sword axe dagger bow arrow spear shield helmet armor armour mace hammer-war gun pistol rifle "
                          "bullet cannon grenade bomb crossbow knife blade katana saber trident flail halberd scythe "
                          "musket revolver missile catapult whip lance club",
    "Tools and objects": "hammer wrench saw screwdriver drill anvil pliers tool key lock chain gear cog compass scale "
                         "candle lamp lantern book scroll quill pen pencil brush hourglass clock watch bell trophy crown "
                         "ring necklace gem diamond coin money bag chest box barrel bucket rope ladder umbrella glasses "
                         "camera phone computer robot battery magnet microscope telescope flask",
    "Vehicles": "car truck bus train tram bicycle motorcycle boat ship sailboat submarine plane airplane helicopter "
                "rocket spaceship tank tractor cart wagon carriage scooter skateboard ufo jet",
    "Sports and games": "ball soccer football basketball baseball tennis golf hockey bowling dice card chess pawn "
                        "rook knight-chess bishop queen king joker poker trophy medal whistle racket skate ski surf "
                        "boxing dumbbell weight target dart billiard",
    "Buildings": "castle tower house home church temple pyramid bridge lighthouse windmill tent igloo cabin barn "
                 "fortress gate door wall well fountain factory skyscraper",
    "People": "person man woman child baby face head hand fist foot eye ear mouth lips brain heart body muscle "
              "beard mustache hair silhouette dancer runner king queen knight soldier ninja pirate cowboy",
    "Clothing": "hat boot boots shoe shoes shirt dress cap hood cloak jacket gloves glove belt suit mask helm crown "
                "scarf sock socks trousers apron tie bowtie heel",
    "Music": "drum flute piano guitar violin harp lute note clef musical trumpet tuba saxophone microphone speaker "
             "headphones bell gong maracas",
    "Abstract and patterns": "abstract swirl spiral knot celtic triskelion trefoil zigzag waves pattern mandala "
                             "triple nested rings orb aura burst rays spark",
    "Space": "planet galaxy comet meteor asteroid astronaut satellite orbit saturn earth mars nebula star-sattelites",
    "Symbols and signs": "heart star cross arrow circle triangle hexagon peace yin-yang infinity check sign symbol "
                         "flag banner emblem badge icon alien radioactive biohazard recycle question exclamation "
                         "omega alpha sigma ankh triskelion knot celtic spiral",
}
_ICON_WORDS = {cat: set(words.split()) for cat, words in ICON_CATEGORIES.items()}


def icon_category(name: str) -> str:
    parts = name.lower().split("-")
    words = set(parts) | {p[:-1] for p in parts if p.endswith("s")} | {name.lower()}
    for cat, vocab in _ICON_WORDS.items():
        if words & vocab:
            return cat
    return "Other art"


ICON_VARIANTS = {
    "coaster": "Round coaster, 95 mm",
    "keychain": "Keychain, 40 mm",
    "ornament": "Hanging ornament, 80 mm",
    "plaque": "Square plaque, 150 mm",
    "cutout": "Cut-out silhouette, 100 mm",
}


class GameIcons:
    source = "game-icons"

    def __init__(self, path: Path = DATA / "game-icons.json.gz"):
        self.path = path
        self._rings: dict[str, str] = {}

    def designs(self):
        if not self.path.exists():
            return
        with gzip.open(self.path, "rt") as fh:
            data = json.load(fh)
        for icon in sorted(data["icons"], key=lambda i: i["name"]):
            self._rings[icon["slug"]] = icon["rings"]
            name = icon["name"].title()
            yield Design(
                slug=f"art-{icon['slug']}", title=name, category=icon_category(icon["slug"]), process=LASER,
                summary=f"{name} artwork by {icon['author']}. Engrave it on a coaster, keychain, ornament or plaque, "
                        "or cut it out as a silhouette.",
                source="game-icons", license=icon["license"], tags=icon["name"].split() + ["engraving", "art"],
                author=icon["author"], author_url=icon["author_url"],
                source_url=f"https://game-icons.net/1x1/{icon['folder']}/{icon['slug'].removesuffix('-' + icon['folder'])}.html",
                variants=list(ICON_VARIANTS), rank=2,
            )

    def rings(self, design: Design) -> list[list[tuple[float, float]]]:
        raw = self._rings[design.slug.removeprefix("art-")]
        out = []
        for ring in raw.split("|"):
            nums = [float(v) for v in ring.split()]
            out.append(list(zip(nums[0::2], nums[1::2])))
        return out

    def icon_svg(self, design: Design) -> str:
        d = " ".join("M" + " L".join(f"{x:g} {y:g}" for x, y in r) + "Z" for r in self.rings(design))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img"><title>{design.title}</title>'
                f'<path d="{d}" fill="#2b2118" fill-rule="evenodd"/></svg>')

    def _fit(self, rings, size: float, cx: float, cy: float, engrave: bool = True) -> list[dict]:
        xs = [x for r in rings for x, _ in r]
        ys = [y for r in rings for _, y in r]
        x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
        k = size / max(x1 - x0, y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        out = []
        for r in rings:
            shape = S.path([(cx + (x - mx) * k, cy + (y - my) * k) for x, y in r], closed=True, engrave=engrave)
            if engrave:
                shape["fill"] = True
            out.append(shape)
        return out

    def shapes(self, design, variant=None):
        variant = variant if variant in ICON_VARIANTS else "coaster"
        rings = self.rings(design)
        if variant == "cutout":
            return S.centre(self._cutout(rings))
        if variant == "coaster":
            base = [S.circle(0, 0, 95)]
            art = self._fit(rings, 62, 0, 0)
        elif variant == "keychain":
            base = [S.rect(0, 0, 40, 40, 5), S.circle(0, -14.5, 5)]
            art = self._fit(rings, 24, 0, 3)
        elif variant == "ornament":
            base = originals.ornament("circle", 80)[:2]
            base = [s for s in base if not s.get("engrave")]
            x0, y0, x1, y1 = S.bounds(base)
            art = self._fit(rings, 50, (x0 + x1) / 2, y1 - 40)
        else:  # plaque
            base = [S.rect(0, 0, 150, 150, 10), S.circle(-63, -63, 5), S.circle(63, -63, 5)]
            art = self._fit(rings, 110, 0, 5)
        return S.centre(base + art)

    def _cutout(self, rings) -> list[dict]:
        """The icon as one cut-out piece: a sticker-style outline around the art, with the art engraved."""
        from shapely import affinity
        from shapely.geometry import Polygon

        ink = None
        for p in sorted((Polygon(r).buffer(0) for r in rings if len(r) >= 3), key=lambda p: -p.area):
            if not p.is_empty:
                ink = p if ink is None else ink.symmetric_difference(p)
        if ink is None or ink.is_empty:
            return self._fit(rings, 100, 0, 0, engrave=False)
        for grow in (10, 16, 24, 34, 48, 64):
            solid = ink.buffer(grow, 8)
            if solid.geom_type == "Polygon":
                break
        else:
            solid = solid.convex_hull
        outer = Polygon(solid.exterior)
        x0, y0, x1, y1 = outer.bounds
        k = 100 / max(x1 - x0, y1 - y0)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        cut = affinity.affine_transform(outer, [k, 0, 0, k, -mx * k, -my * k]).simplify(0.05)
        art = []
        for r in rings:
            shape = S.path([((x - mx) * k, (y - my) * k) for x, y in r], closed=True, engrave=True)
            shape["fill"] = True
            art.append(shape)
        return S.polygon_paths(cut) + art


# ---------------------------------------------------------------- NASA 3D Resources

class Nasa3D:
    source = "nasa-3d"
    MAX_QUOTE_BYTES = 45 * 1024 * 1024

    def __init__(self, path: Path = DATA / "nasa-3d.json"):
        self.path = path

    def designs(self):
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text())
        for m in data["models"]:
            n = len(m["files"])
            parts = f"{n} printable parts" if n > 1 else "one printable part"
            yield Design(
                slug=m["slug"], title=m["title"], category="Space", process=PRINT, source="nasa-3d", license="nasa",
                summary=f"A 3D print model from NASA's 3D Resources, with {parts}. We can scale it to suit.",
                tags=re.split(r"[\s()-]+", m["title"].lower()) + ["nasa", "space", "3d print", "model"],
                author="NASA", source_url="https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Printing/"
                + "%20".join(m["title"].split(" ")),
                size_mm=tuple(m["extents_mm"]), files=m["files"],
                preview_url=f"/static/library/nasa/{m['slug']}.webp", rank=1,
            )

    def shapes(self, design, variant=None):
        return []


def default_providers():
    return [Originals(), Nasa3D(), GameIcons()]

