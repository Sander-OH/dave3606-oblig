import json
import html
import gzip
import struct
import psycopg
from flask import Flask, Response, request
from time import perf_counter

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

    with open("templates/sets.html") as f:
        template = f.read()

    rows_list = []

    start_time = perf_counter()
    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("select id, name from lego_set order by id")
            for row in cur.fetchall():
                html_safe_id = html.escape(row[0])
                html_safe_name = html.escape(row[1])

                rows_list.append(
                    f'<tr><td><a href="/set?id={html_safe_id}">{html_safe_id}</a></td>'
                    f'<td>{html_safe_name}</td></tr>\n'
                )

        rows = "".join(rows_list)

        print(f"Time to render all sets: {perf_counter() - start_time}")
    finally:
        conn.close()

    if encoding == "utf-8":
        meta = '<meta charset="UTF-8">'
    else:
        meta = ""

    page_html = template.replace("{META}", meta).replace("{ROWS}", rows)

    body = page_html.encode(encoding)

    compressed_body = gzip.compress(body)

    response = Response(
        compressed_body,
        content_type=f"text/html; charset={encoding}"
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

    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, year, category, preview_image_url
                FROM lego_set
                WHERE id = %s
            """, (set_id,))
            set_row = cur.fetchone()

            if not set_row:
                return Response("Set not found", status=404)

            cur.execute("""
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
            for brick_type_id, color_id, name, image_url, count in cur.fetchall():
                inventory.append({
                    "brick_type_id": brick_type_id,
                    "color_id": color_id,
                    "name": name,
                    "image": image_url,
                    "count": count
                })

    finally:
        conn.close()

    result = {
        "id": set_row[0],
        "name": set_row[1],
        "year": set_row[2],
        "category": set_row[3],
        "image": set_row[4],
        "inventory": inventory
    }

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

    conn = psycopg.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, year, category, preview_image_url
                FROM lego_set
                WHERE id = %s
            """, (set_id,))
            set_row = cur.fetchone()

            if not set_row:
                return Response("Set not found", status=404)

            cur.execute("""
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

            inventory_rows = cur.fetchall()

    finally:
        conn.close()


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
