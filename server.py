import json
import html
import gzip
import struct
import psycopg
from flask import Flask, Response, request
from time import perf_counter
from database import Database
from collections import OrderedDict

cache = OrderedDict()
MAX_CACHE = 100


app = Flask(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}


@app.route("/")
def index():
    with open("templates/index.html") as f:
        template = f.read()
    return Response(template)


@app.route("/sets")
def sets():
    encoding = request.args.get("encoding", "utf-8").lower()
    if encoding not in ("utf-8", "utf-16"):
        encoding = "utf-8"

    with open("templates/sets.html") as f:      # "With open" ensures that the file is properly closed after usage
        template = f.read()

    rows_list = []

    start_time = perf_counter()

    db = Database(DB_CONFIG)
    rows_data = db.execute_and_fetch_all(
        "SELECT id, name FROM lego_set ORDER BY id"
    )

    for row in rows_data:
        html_safe_id = html.escape(row[0])
        html_safe_name = html.escape(row[1])

        rows_list.append(
            f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td>'
            f'<td>{html_safe_name}</td></tr>\n'
        )

    rows = "".join(rows_list)
    print(f"Time to render all sets: {perf_counter() - start_time}")
    

    if encoding == "utf-8":
        meta = '<meta charset="UTF-8">'
    else:
        meta = ""

    page_html = template.replace("{META}", meta).replace("{ROWS}", rows)

    body = page_html.encode(encoding)

    compressed_body = gzip.compress(body)

    response = Response(
        compressed_body,
        content_type=f"text/html; charset={encoding}",
        headers={"Cache-Control": "max-age=60"} # Cache page for 1 minute (browser cache)
    )
    response.headers["Content-Encoding"] = "gzip"

    return response


@app.route("/set")
def legoSet():  # We don't want to call the function `set`, since that would hide the `set` data type.
    with open("templates/set.html") as f:
        template = f.read()
    return Response(template)


@app.route("/api/set")
def apiSet():
    set_id = request.args.get("id")

    # --- Cache ---
    if set_id in cache:
        cache.move_to_end(set_id)
        return Response(
            json.dumps(cache[set_id]),
            content_type="application/json"
        )


    db = Database(DB_CONFIG)

    # --- Get set ---
    set_rows = db.execute_and_fetch_all("""
        SELECT id, name, year, category, preview_image_url
        FROM lego_set
        WHERE id = %s
    """, (set_id,))

    if not set_rows:
        return Response("Set not found", status=404)

    set_row = set_rows[0]

    # --- Get inventory ---
    inventory_rows = db.execute_and_fetch_all("""
        SELECT
            b.brick_type_id,
            b.color_id,
            b.name,
            b.preview_image_url,
            i.count
        FROM lego_inventory i
        JOIN lego_brick b
        ON i.brick_type_id = b.brick_type_id
        AND i.color_id = b.color_id
        WHERE i.set_id = %s
        ORDER BY b.brick_type_id, b.color_id
    """, (set_id,))

    inventory = []
    for brick_type_id, color_id, name, image_url, count in inventory_rows:
        inventory.append({
            "brick_type_id": brick_type_id,
            "color_id": color_id,
            "name": name,
            "image": image_url,
            "count": count
        })

    result = {
        "id": set_row[0],
        "name": set_row[1],
        "year": set_row[2],
        "category": set_row[3],
        "image": set_row[4],
        "inventory": inventory
    }

    # --- Store in cache ---
    cache[set_id] = result
    if len(cache) > MAX_CACHE:  # Drop Least Recently Used (LRU) if cache is full
        cache.popitem(last=False)

    return Response(
        json.dumps(result, indent=4),
        content_type="application/json"
    )


def pack_string(s: str) -> bytes:
    """Helper: packs string as [length][bytes]"""
    encoded = s.encode("utf-8")
    return struct.pack("I", len(encoded)) + encoded


@app.route("/api/set/bin")
def apiSetBinary():
    set_id = request.args.get("id")

    db = Database(DB_CONFIG)

    set_rows = db.execute_and_fetch_all("""
        SELECT id, name, year, category, preview_image_url
        FROM lego_set
        WHERE id = %s
    """, (set_id,))

    if not set_rows:
        return Response("Set not found", status=404)

    set_row = set_rows[0]

    inventory_rows = db.execute_and_fetch_all("""
        SELECT
            b.brick_type_id,
            b.color_id,
            b.name,
            b.preview_image_url,
            i.count
        FROM lego_inventory i
        JOIN lego_brick b
        ON i.brick_type_id = b.brick_type_id
        AND i.color_id = b.color_id
        WHERE i.set_id = %s
        ORDER BY b.brick_type_id, b.color_id
    """, (set_id,))


    data = b""

    data += pack_string(set_row[0])
    data += pack_string(set_row[1])
    data += struct.pack("I", int(set_row[2]))
    data += pack_string(set_row[3] or "")
    data += pack_string(set_row[4] or "")

    data += struct.pack("I", len(inventory_rows))

    for brick_type_id, color_id, name, image_url, count in inventory_rows:
        data += pack_string(brick_type_id) 
        data += struct.pack("I", int(color_id))
        data += pack_string(name or "")
        data += pack_string(image_url or "")
        data += struct.pack("I", int(count))

    return Response(
        data,
        content_type="application/octet-stream"
    )
                

if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
