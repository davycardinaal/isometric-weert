"""Weert van toen: a guided tour along the town's history, as an overlay for the viewer.

Texts are written for this map from the Dutch Wikipedia; every stop names and links the article it was written from.
Photos are Wikimedia Commons files with an open license, many from the Rijksdienst voor het Cultureel Erfgoed
(CC BY-SA 4.0); they are downloaded once and published with the site, with credits.

Output: data/build/history.json and data/build/history/*.jpg
"""

import hashlib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request

from config import BUILD, CX, CY
from geo import wgs_to_rd

WP = "https://nl.wikipedia.org/wiki/"
RCE = "Rijksdienst voor het Cultureel Erfgoed, CC BY-SA 4.0"


def wiki(title, label=None):
    """A stop's source: the Dutch Wikipedia article its text was written from."""
    return (f"Wikipedia: {label or title.replace('_', ' ')}", WP + title)


STOPS = [
    {
        "year": "1062",
        "title": "Het eiland van Weert",
        "latlon": (51.25340, 5.70655),
        "zoom": 0.25,
        "text": "Weert is een waard: een hoog en droog stuk land tussen de Peelmoerassen, waar de wegen over de hei en het veen samenkwamen. De plaats wordt voor het eerst genoemd in een oorkonde uit 1062. Al veel eerder woonden hier mensen: op de Boshoverheide ligt een groot urnenveld uit de late bronstijd.",
        "source": wiki("Weert_(stad)", "Weert"),
        "more": WP + "Weert_(stad)",
    },
    {
        "year": "1e eeuw v.Chr.",
        "title": "De Keltische Schans",
        "latlon": (51.26427, 5.71452),
        "text": "Bij de bouw van de wijk Molenakker vonden amateurarcheologen Romeins bronzen vaatwerk. De opgraving van 1994 bracht een versterking van anderhalve hectare aan het licht, uit de eerste eeuw voor Christus: een vluchtburcht met een gracht van drie meter breed, in de tijd van de Eburonen. Ernaast lag tot ongeveer 250 na Christus een nederzetting van ten minste tien hectare, met 45 grotere gebouwen en zes waterputten.",
        "source": wiki("Keltische_Schans"),
        "more": WP + "Keltische_Schans",
    },
    {
        "year": "ca. 1290",
        "title": "De Aldenborgh",
        "latlon": (51.25927, 5.71247),
        "text": "De heren van Horne kregen in de 12e eeuw steeds meer te zeggen in Weert. Een oorkonde uit 1295 noemt het huis van graaf Willem II van Horne; een jaar later mocht hij water aftappen om er de gracht mee te vullen. Of het een kasteel was of alleen een hof, weet niemand zeker. In 2020 is hier een grafkelder gevonden waarin Philips van Horne misschien is begraven.",
        "source": wiki("Aldenborgh"),
        "more": WP + "Aldenborgh",
    },
    {
        "year": "1306",
        "title": "De Weertse munt",
        "latlon": (51.25401, 5.70522),
        "h": 8,
        "text": "In 1306 droeg het kapittel van Sint-Servaas in Maastricht zijn rechten in Weert over aan de heren van Horne. Van dat jaar tot 1568 werden in Weert munten geslagen. De sierlijke gezwenkte voorgevel van het Muntgebouw is jonger, van 1580 of kort daarna. De buurt eromheen is gesloopt voor winkelcentrum de Muntpassage (1970); alleen dit huis bleef staan. In 2003 stond het model voor het 84ste Delfts blauwe huisje van de KLM.",
        "photos": [
            ("Overzicht voorgevel en gedeelte linker zijgevel - Weert - 20354343 - RCE.jpg", f"Het Muntgebouw in 2001, J.P. de Koning, {RCE}"),
            ("Muntgebouw Weert 01.jpg", "Het Muntgebouw in 2020, FrDr, CC BY-SA 4.0"),
        ],
        "source": wiki("Muntgebouw_(Weert)", "Muntgebouw"),
        "more": WP + "Muntgebouw_(Weert)",
    },
    {
        "year": "1414",
        "title": "Marktrechten",
        "latlon": (51.25340, 5.70655),
        "text": "In 1414 kreeg Weert marktrechten. Onder de bescherming van de graven van Horne bloeide de stad tussen 1450 en 1550, vooral door het laken dat hier werd geweven. Uit die tijd is de kerk aan de Markt.",
        "source": wiki("Weert_(stad)", "Weert"),
        "more": WP + "Weert_(stad)",
    },
    {
        "year": "1455",
        "title": "De Nijenborgh",
        "latlon": (51.25638, 5.70883),
        "h": 6,
        "text": "Jacob I van Horne liet tussen 1455 en 1461 een nieuwe waterburcht bouwen tegen de stadswal: de Nijenborgh, de nieuwe burcht. Het kasteel van 75 bij 60 meter had vier hoektorens en een hoge woonvleugel met trapgevels. In de Tachtigjarige Oorlog is het keer op keer belegerd, en in 1702, in de Spaanse Successieoorlog, verwoest. Op de fundamenten van de zuidelijke toren staat sinds 1841 het herenhuis Op de Biest.",
        "photos": [
            ("Nijenborgh prent.jpg", "De ruïne van de toegangspoort op een oude prent (publiek domein)"),
            ("Kasteel Biest.jpg", "Het kasteel in 2008, Thommorris, CC BY-SA 3.0"),
        ],
        "source": wiki("Kasteel_Nijenborgh"),
        "more": WP + "Kasteel_Nijenborgh",
    },
    {
        "year": "1461",
        "title": "Minderbroeders op de Biest",
        "at": (177699.2, 363378.8),
        "h": 10,
        "text": "Toen zijn nieuwe kasteel klaar was, schonk Jacob I van Horne zijn oude hof, de Aldenborgh, aan de minderbroeders. Na de dood van zijn vrouw trad hij zelf in. De laatgotische Paterskerk is van 1512 tot 1526 gebouwd. De Fransen hieven het klooster in 1797 op; in 1836 kwamen de broeders terug. Ze bleven tot 2023: na 561 jaar waren er te weinig broeders over.",
        "photos": [
            ("Aldenborgh.JPG", "De Paterskerk in 2012, Peter van der Wielen, CC BY-SA 3.0 NL"),
            ("Weert Minderbroederklooster-3.jpg", "De achterkant van het klooster met de begraafplaats in 2004, Jan van den Eijnden, CC BY-SA 3.0 NL"),
        ],
        "source": wiki("Minderbroedersklooster_(Weert)", "Minderbroedersklooster"),
        "more": WP + "Minderbroedersklooster_(Weert)",
    },
    {
        "year": "1456-1528",
        "title": "Sint-Martinuskerk",
        "at": (177316.0, 362744.5),
        "h": 30,
        "text": "Een laatgotische hallenkerk: drie beuken van gelijke hoogte onder één dak. Nederland heeft er nog twee, deze en de Grote Kerk in Zwolle. Het koor was klaar in 1456, het schip in 1512, en in 1528 begon de bouw van de toren. De gewelven zijn van voor tot achter beschilderd. In 1887 kreeg de toren een spits tot 104,80 meter, toen de op twee na hoogste van Nederland. In een najaarsstorm van 1940 stortte die naar beneden. De bekroning van nu, van Theo Verlaan, is uit 1960.",
        "photos": [
            ("MartinuskerkWeertLimburgNederland.jpg", "De Sint-Martinuskerk in 2010, Massimo Catarinella, CC BY 3.0"),
            ("Toren Martinuskerk - Weert (29022792687).jpg", "De toren in 2018, FaceMePLS, CC BY 2.0"),
        ],
        "source": wiki("Sint-Martinuskerk_(Weert)", "Sint-Martinuskerk"),
        "more": WP + "Sint-Martinuskerk_(Weert)",
    },
    {
        "year": "1568",
        "title": "De graaf van Horne onthoofd",
        "latlon": (51.25719, 5.70936),
        "text": "Philips de Montmorency, graaf van Horne en heer van Weert, was admiraal en ridder van het Gulden Vlies. Toen Alva kwam, vluchtte Willem van Oranje; Egmont en Horne bleven. Op 5 juni 1568 zijn ze op de Grote Markt van Brussel onthoofd. Zijn grafsteen ligt in de Martinuskerk, maar of hij daar ook begraven is, staat niet vast. Sinds 2022 staat hij te paard in de voorhof van zijn kasteel.",
        "photos": [
            ("Muurschildering 'de onthoofding van Philips van Horne' Weert 01.jpg", "Muurschildering van de onthoofding, FrDr, CC BY-SA 4.0"),
        ],
        "source": wiki("Filips_van_Montmorency", "Filips van Montmorency"),
        "more": WP + "Filips_van_Montmorency",
    },
    {
        "year": "1825",
        "title": "De Zuid-Willemsvaart",
        "latlon": (51.25785, 5.70363),
        "text": "Na de dood van de laatste graaf raakte Weert in verval. Het kanaal van Maastricht naar 's-Hertogenbosch bracht de handel terug. Bij Weert loopt het naar het westen, door het bed van Napoleons nooit voltooide Grand Canal du Nord. De Stadsbrug, de Statterbrök, is zo oud als het kanaal: eerst een ophaalbrug, vanaf 1913 een draaibrug, en sinds 1968 de hefbrug van nu.",
        "photos": [("Stadsbrug.jpg", "De Stadsbrug, Thommorris, CC BY-SA 3.0")],
        "source": wiki("Stadsbrug_Weert", "Stadsbrug Weert"),
        "more": WP + "Stadsbrug_Weert",
    },
    {
        "year": "1856",
        "title": "Kleipijpen van Trumm-Bergmans",
        "latlon": (51.26181, 5.71409),
        "text": "De pijpenfabriek Trumm-Bergmans kwam in 1855 naar Weert en bouwde een jaar later deze oven van baksteen en chamotte om kleipijpen in te bakken. In 1933 stapte de fabriek over op pijpen van bruyèrehout; in de oven ging voortaan het houtafval. In 1989 is hij vijftig meter verplaatst, naar de Biesterbrug.",
        "photos": [("Overzicht zijde van bakstenen oven met trap - Weert - 20346649 - RCE.jpg", f"De oven in 2003, IJsbrand Heins, {RCE}")],
        "source": wiki("Kleipijpenoven"),
        "more": WP + "Kleipijpenoven",
    },
    {
        "year": "1879",
        "title": "De IJzeren Rijn",
        "latlon": (51.24894, 5.70410),
        "h": 8,
        "text": "Op 20 juli 1879 ging het station open, aan de spoorlijn die de IJzeren Rijn heet. Het bakstenen gebouw van nu, met de achtkantige toren en het stadswapen op de spits, is uit 1914 en ontworpen door George van Heukelom. Tot eind jaren zestig was Weert een goederenstation met een eigen rangeerlocje, de Sik.",
        "photos": [
            ("Station Weert (2024).jpg", "Het station in 2024, Sneeuwvlakte, CC BY-SA 4.0"),
            ("Weert stationsgebouw.jpg", "Het stationsgebouw, M.Minderhoud, CC BY-SA 3.0"),
        ],
        "source": wiki("Station_Weert", "Station Weert"),
        "more": WP + "Station_Weert",
    },
    {
        "year": "1907",
        "title": "De Weerter kempenaar",
        "latlon": (51.26305, 5.72001),
        "text": "Al sinds 1836 werden hier houten schepen gerepareerd. In 1907 begon de Weerter Scheepsbouw Maatschappij met stalen schepen; tot 1947 liepen er 145 van stapel. In de jaren twintig tekende Driessens de Weerter kempenaar: 50 meter lang, 6,60 breed en met 525 ton net iets meer laadvermogen dan een gewone kempenaar. In het beste jaar leverde de werf er dertien af en werkten er tweehonderd man.",
        "source": wiki("Weerter_Scheepsbouw_Maatschappij", "Weerter Scheepsbouw Maatschappij"),
        "more": WP + "Weerter_Scheepsbouw_Maatschappij",
    },
    {
        "year": "1938",
        "title": "Kazerne en kazematten",
        "latlon": (51.24478, 5.68630),
        "text": "De Van Hornekazerne is in 1938 gebouwd als een van zestien standaardkazernes voor de infanterie. In mei 1940 trokken de soldaten naar de Peel-Raamstelling langs het kanaal; de kazerne bleef leeg achter en de bezetter trok erin. Na de bevrijding kwamen de Engelsen, en in november 1944 was Eisenhower op bezoek. Vanaf 1951 zijn hier alle onderofficieren van de landmacht opgeleid, aan de Onderofficiersschool, die sinds 1961 Koninklijk heet.",
        "photos": [("Van Horne Kazerne (20).JPG", "De Van Hornekazerne in 2011, ArmTheInsane, CC BY-SA 3.0")],
        "source": wiki("Van_Hornekazerne"),
        "more": WP + "Van_Hornekazerne",
    },
    {
        "year": "1944",
        "title": "Bevrijd door de Suffolks",
        "latlon": (51.25781, 5.70321),
        "text": "Op 22 september 1944 is Weert bevrijd, door Britse soldaten van het Suffolk Regiment. De Suffolkweg aan de overkant van het kanaal heet naar hen, en bij de Stadsbrug staat sinds 2002 hun monument.",
        "source": ("Wikipedia: Kenneth Mayhew", WP + "Kenneth_Mayhew"),
    },
]

def commons_thumb(name, width=960):  # Wikimedia only serves a fixed set of thumbnail widths
    name = name.replace(" ", "_")  # Commons stores a file under its name with underscores
    h = hashlib.md5(name.encode()).hexdigest()
    q = urllib.parse.quote(name)
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"


def download(url, tries=6):
    """Wikimedia rate-limits bursts of thumbnail requests; wait politely and retry."""
    req = urllib.request.Request(url, headers={"User-Agent": "isometric-map/0.1 (personal map)"})
    for attempt in range(tries):
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
            time.sleep(3)
            return data
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(15 * (attempt + 1))


def route_order(stops):
    """Visit the stops as a route over the map instead of by date: the first and last stay put, the rest is a
    nearest-neighbour path tidied with 2-opt, so dots that lie together come one after another. Stops on the same
    spot (the old and the new church) keep their chronological order."""
    if len(stops) < 3:
        return stops
    first, last, middle = stops[0], stops[-1], stops[1:-1]
    dist = lambda a, b: ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
    path, todo = [first], middle[:]
    while todo:
        nxt = min(todo, key=lambda s: (dist(path[-1], s), stops.index(s)))
        path.append(nxt)
        todo.remove(nxt)
    path.append(last)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                before = dist(path[i - 1], path[i]) + dist(path[j], path[j + 1])
                after = dist(path[i - 1], path[j]) + dist(path[i], path[j + 1])
                if after < before - 0.01:
                    path[i : j + 1] = path[i : j + 1][::-1]
                    improved = True
    # Places within 40 m of each other (church, parsonage, Sunday school) in chronological order.
    i = 0
    while i < len(path):
        j = i
        while j + 1 < len(path) - 1 and i > 0 and dist(path[j + 1], path[i]) < 40:
            j += 1
        year = lambda st: int(m.group()) if (m := re.search(r"\d{4}", st["year"])) else 9999
        path[i : j + 1] = sorted(path[i : j + 1], key=lambda st: (year(st), stops.index(st)))
        i = j + 1
    return path


def main():
    out_dir = BUILD / "history"
    out_dir.mkdir(parents=True, exist_ok=True)
    stops = []
    for i, s in enumerate(STOPS, start=1):
        x, y = s["at"] if "at" in s else wgs_to_rd(*s["latlon"])
        stop = {"n": i, "year": s["year"], "title": s["title"], "text": s["text"], "x": round(x, 1), "y": round(y, 1),
                "h": s.get("h", 0), "zoom": s.get("zoom", 1.2),
                "source": {"label": s["source"][0], "url": s["source"][1]}, "more": s.get("more")}
        stop["photos"] = []
        for k, (name, credit) in enumerate(s.get("photos", [])):
            dst = out_dir / f"{i:02d}_{k}.jpg"
            if not dst.exists():
                dst.write_bytes(download(commons_thumb(name)))
                subprocess.run(["magick", str(dst), "-resize", "640x640>", "-quality", "82", str(dst)], check=True)
            stop["photos"].append({"src": f"history/{dst.name}", "credit": credit,
                                   "url": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(name)}"})
        stops.append(stop)
    stops = route_order(stops)
    for n, stop in enumerate(stops, start=1):
        stop["n"] = n
    # A version in every photo URL, so browsers never show a cached photo that has since been replaced.
    version = hashlib.md5(b"".join(f.read_bytes() for f in sorted(out_dir.glob("*.jpg")))).hexdigest()[:8]
    for stop in stops:
        for ph in stop["photos"]:
            ph["src"] += f"?v={version}"
    (BUILD / "history.json").write_text(json.dumps({"stops": stops}, ensure_ascii=False, indent=1))
    print(f"{len(stops)} stops, {sum(len(s['photos']) for s in stops)} photos on {sum(bool(s['photos']) for s in stops)} stops")


if __name__ == "__main__":
    main()
