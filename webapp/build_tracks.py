"""Bake real circuit outlines into webapp/static/tracks.json.

Source: bacinger/f1-circuits (MIT, notice in static/tracks.LICENSE.md) --
GPS-traced centrelines of every F1 circuit as GeoJSON. The result is a
static file for the same reason the photos are: nothing at request time
depends on a third party being up.

    python -m webapp.build_tracks                 # download and rebuild
    python -m webapp.build_tracks circuits.geojson  # from a local copy

Coordinates are projected equirectangularly around each circuit's own
centre (longitude scaled by cos(latitude)), which is distortion-free at
the scale of a few kilometres, then flipped so north is up and fitted
into a 100-unit box with the aspect ratio kept.
"""

import json
import math
import os
import sys
import urllib.request

SOURCE_URL = "https://raw.githubusercontent.com/bacinger/f1-circuits/master/f1-circuits.geojson"
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "tracks.json")

# App circuit id (reference.CIRCUITS) -> dataset id. Only modern slugs:
# pre-2023 races use numeric ids, and many of those layouts have since
# changed, so a current outline would be the wrong shape for them.
DATASET_IDS = {
    "albert_park": "au-1953",
    "americas": "us-2012",
    "bahrain": "bh-2002",
    "baku": "az-2016",
    "catalunya": "es-1991",
    "hungaroring": "hu-1986",
    "imola": "it-1953",
    "interlagos": "br-1940",
    "jeddah": "sa-2021",
    "losail": "qa-2004",
    "madring": "es-2026",
    "marina_bay": "sg-2008",
    "miami": "us-2022",
    "monaco": "mc-1929",
    "monza": "it-1922",
    "red_bull_ring": "at-1969",
    "rodriguez": "mx-1962",
    "sepang": "my-1999",
    "shanghai": "cn-2004",
    "silverstone": "gb-1948",
    "spa": "be-1925",
    "suzuka": "jp-1962",
    "vegas": "us-2023",
    "villeneuve": "ca-1978",
    "yas_marina": "ae-2009",
    "zandvoort": "nl-1948",
}

BOX = 100


def outline(coordinates) -> dict:
    lons = [lon for lon, _ in coordinates]
    lats = [lat for _, lat in coordinates]
    lat0 = (min(lats) + max(lats)) / 2
    scale_x = math.cos(math.radians(lat0))
    xs = [lon * scale_x for lon in lons]
    ys = [-lat for lat in lats]

    min_x, min_y = min(xs), min(ys)
    span = max(max(xs) - min_x, max(ys) - min_y)
    points = [((x - min_x) / span * BOX, (y - min_y) / span * BOX) for x, y in zip(xs, ys)]
    if points[0] == points[-1]:
        points.pop()

    width = max(x for x, _ in points)
    height = max(y for _, y in points)
    d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points) + " Z"
    return {"viewBox": f"0 0 {width:.2f} {height:.2f}", "d": d}


def main(source: str = None) -> None:
    if source:
        with open(source, encoding="utf-8") as handle:
            collection = json.load(handle)
    else:
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
            collection = json.load(response)

    by_id = {feature["properties"]["id"]: feature for feature in collection["features"]}
    tracks = {}
    for app_id, dataset_id in sorted(DATASET_IDS.items()):
        feature = by_id.get(dataset_id)
        if feature is None or feature["geometry"]["type"] != "LineString":
            print(f"skipped {app_id}: {dataset_id} not in source", file=sys.stderr)
            continue
        tracks[app_id] = outline(feature["geometry"]["coordinates"])

    payload = {
        "source": "https://github.com/bacinger/f1-circuits (MIT, see tracks.LICENSE.md)",
        "tracks": tracks,
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, separators=(",", ":"))
    print(f"wrote {len(tracks)} outlines to {OUTPUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
