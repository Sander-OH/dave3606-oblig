import json
import html
import gzip
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

    with open("templates/sets.html") as f:      # "With open" ensures that the file is properly closed after usage
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
    result = {"set_id": set_id}
    json_result = json.dumps(result, indent=4)
    return Response(json_result, content_type="application/json")


if __name__ == "__main__":
    app.run(port=5000, debug=True)

# Note: If you define new routes, they have to go above the call to `app.run`.
