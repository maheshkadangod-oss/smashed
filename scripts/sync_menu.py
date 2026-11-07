"""Refresh the menu baked into the site from their live SmashPOS menu (menu.smashed.in).

Rewrites, only when something changed:
  - the menu markup in index.html (between MENU:START and MENU:END)
  - the menu and the FAQ price answer in the JSON-LD
  - the visible FAQ price answer
  - the menu in llms.txt and the date in sitemap.xml

The page also loads the live menu in the browser, so visitors see changes straight away.
This script keeps what search engines and AI crawlers read in step with it.

Stdlib only. Run from the repo root:  python3 scripts/sync_menu.py
Exit code 0 = up to date or updated, 1 = could not fetch (nothing is touched).
"""
import datetime, html, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTES = json.loads((ROOT / "menu-notes.json").read_text())


def query(path, args):
    req = urllib.request.Request(
        NOTES["api"] + "/api/query",
        data=json.dumps({"path": path, "args": args, "format": "json"}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "smashed-site-menu-sync"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        body = json.load(r)
    if body.get("status") != "success":
        raise RuntimeError(f"{path}: {body}")
    return body["value"]


def norm(name):
    return re.sub(r"\s+", " ", name.replace("’", "'").replace("*", "")).strip().lower()


def clean(name):
    return re.sub(r"\s*\*+\s*$", "", name).strip()


def rupees(paise):
    v = paise / 100
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def build_model(categories):
    """Same rules as renderMenu() in index.html. Change both together."""
    model, extras = [], {}
    for cat in categories:
        full = cat["name"] in NOTES["fullCategories"]
        items = []
        for p in cat["products"]:
            if not full and not p["isAvailable"]:
                continue
            price, variants = p["basePrice"], None
            for g in p.get("addonGroups", []):
                if g["name"].lower().startswith("patty"):
                    opts = g["addons"]
                    price += next((a["price"] for a in opts if a.get("isDefault")), 0)
                    if len(opts) > 1:
                        variants = " / ".join(f'{a["name"]} ₹{rupees(p["basePrice"] + a["price"])}' for a in opts)
                elif g["name"].lower() == "extras" and cat["name"] == "Classic Burgers":
                    for a in g["addons"]:
                        extras.setdefault(a["name"], a["price"])
            items.append({
                "name": clean(p["name"]), "price": rupees(price), "variants": variants,
                "best": bool(p.get("isBestseller")), "out": not p["isAvailable"],
                "desc": NOTES["descriptions"].get(norm(p["name"])),
            })
        if items:
            model.append({"key": cat["name"], "title": NOTES["categoryNames"].get(cat["name"], cat["name"]),
                          "note": NOTES["categoryNotes"].get(cat["name"]), "full": full, "items": items})
    if extras:
        model.append({"key": "extras", "title": NOTES["extrasTitle"], "note": None, "full": False,
                      "items": [{"name": n, "price": rupees(v), "variants": None, "best": False, "out": False, "desc": None}
                                for n, v in extras.items()]})
    return model


def render(model):
    e = html.escape
    out = []
    for c in model:
        rows = []
        for it in c["items"]:
            star = ' <span class="star" aria-label="Bestseller">★</span>' if it["best"] else ""
            tag = '<span class="soldout mono">Sold out tonight</span>' if it["out"] else ""
            r = (f'<div class="mi{" small" if not c["full"] else ""}{" out" if it["out"] else ""}">'
                 f'<div class="mi-top"><h4>{e(it["name"])}{star}</h4><span class="dots" aria-hidden="true"></span>'
                 f'<span class="price">₹{it["price"]}</span></div>{tag}')
            if c["full"] and it["desc"]:
                r += f'<p>{e(it["desc"])}</p>'
            if c["full"] and it["variants"]:
                r += f'<p class="var mono">{e(it["variants"])}</p>'
            rows.append(r + "</div>")
        note = f'<span class="mono">{e(c["note"])}</span>' if c["note"] else ""
        out.append(f'<div class="mcat"><div class="mcat-head"><h3>{e(c["title"])}</h3>{note}</div>'
                   f'<div class="{"mrows" if c["full"] else "mgrid"}">{"".join(rows)}</div></div>')
    return "".join(out)


def price_answer(model):
    burgers = next((c for c in model if c["key"] == "Classic Burgers"), None)
    if not burgers:
        return None
    lo = min(burgers["items"], key=lambda i: int(float(i["price"])))
    hi = max(burgers["items"], key=lambda i: int(float(i["price"])))
    text = f"Burgers run from ₹{lo['price']} for the {lo['name']} to ₹{hi['price']} for the {hi['name']}, priced as doubles."
    single = re.search(r"Single ₹(\d+)", lo["variants"] or "")
    if single:
        text += f" A single-patty {lo['name']} is ₹{single.group(1)}."
    fries = next((i for c in model for i in c["items"] if norm(i["name"]) == "tallow fries"), None)
    if fries:
        text += f" Tallow Fries are ₹{fries['price']}."
    return text + " Delivery prices on Zomato can differ."


def jsonld_menu(model, site):
    secs = []
    for c in model:
        items = []
        for it in c["items"]:
            d = {"@type": "MenuItem", "name": it["name"]}
            if it["desc"]:
                d["description"] = it["desc"]
            d["offers"] = {"@type": "Offer", "price": it["price"], "priceCurrency": "INR"}
            items.append(d)
        secs.append({"@type": "MenuSection", "name": c["title"], "hasMenuItem": items})
    return {"@type": "Menu", "name": "Smashed Burgers & Co. menu", "url": site + "#menu", "hasMenuSection": secs}


def llms_menu(model):
    lines = ["## Menu", "",
             "Prices in Indian rupees from the restaurant's live menu at https://menu.smashed.in/. Burgers are priced as doubles.",
             "Stock changes through the night. Delivery prices on Zomato can differ. Bestsellers are marked ★.", ""]
    for c in model:
        lines.append(f"### {c['title']}")
        for it in c["items"]:
            star = " ★" if it["best"] else ""
            bits = [f"- {it['name']}{star} (₹{it['price']})"]
            if it["variants"]:
                bits.append(f" [{it['variants']}]")
            if it["desc"] and c["full"]:
                bits.append(f": {it['desc']}")
            lines.append("".join(bits))
        lines.append("")
    return "\n".join(lines)


def main():
    try:
        rest = query("restaurants:getByPublicPagePath", {"path": NOTES["pagePath"]})
        cats = query("products:listPublic", {"restaurantId": rest["_id"]})
    except Exception as e:  # network or API change: leave the site as it is
        print(f"could not fetch the live menu, nothing changed: {e}")
        return 1
    model = build_model(cats)
    food = sum(len(c["items"]) for c in model if c["full"])
    if food < 5:
        print(f"only {food} food items came back, refusing to overwrite the menu")
        return 1

    idx = ROOT / "index.html"
    s = idx.read_text()
    start, end = "<!-- MENU:START -->", "<!-- MENU:END -->"
    a, b = s.index(start) + len(start), s.index(end)
    s = s[:a] + render(model) + s[b:]

    m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', s, re.S)
    data = json.loads(m.group(2))
    rest_node = next(g for g in data["@graph"] if g["@type"] == "Restaurant")
    rest_node["hasMenu"] = jsonld_menu(model, rest_node["url"])
    answer = price_answer(model)
    if answer:
        for q in next(g for g in data["@graph"] if g["@type"] == "FAQPage")["mainEntity"]:
            if q["name"] == "How much does a meal cost?":
                q["acceptedAnswer"]["text"] = answer
        s = re.sub(r'(<p class="a">)Burgers run from ₹[^<]*?Zomato can differ\.(</p>)',
                   lambda mm: mm.group(1) + html.escape(answer, quote=False) + mm.group(2), s)
    s = s[:m.start(2)] + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n" + s[m.end(2):]

    llms = ROOT / "llms.txt"
    t = llms.read_text()
    t = t[:t.index("## Menu")] + llms_menu(model) + "\n" + t[t.index("## Links"):]

    changed = []
    if s != idx.read_text():
        idx.write_text(s); changed.append("index.html")
    if t != llms.read_text():
        llms.write_text(t); changed.append("llms.txt")
    if changed:
        sm = ROOT / "sitemap.xml"
        today = datetime.date.today().isoformat()
        sm.write_text(re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{today}</lastmod>", sm.read_text()))
        changed.append("sitemap.xml")
    print(f"{food} food items, {len(model)} sections. " + (f"updated: {', '.join(changed)}" if changed else "already up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
