# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Named places of Weert: style overrides and extra geometry for buildings, plus the viewer's place list.

Sources: the Dutch Wikipedia, Wikidata and OpenStreetMap for the places, the Rijksmonumenten register, Wikimedia
Commons for the photos, and AHN for tower positions and heights.

Output: data/build/landmarks.json
"""

import json

import numpy as np

from config import BUILD, RAW
from geo import wgs_to_rd

RCE = "Rijksdienst voor het Cultureel Erfgoed, CC BY-SA 4.0"
WP = "https://nl.wikipedia.org/wiki/"  # every story is written from the Dutch Wikipedia article it links to

# Buildings found by an address or point; `pand` is resolved to the 3D BAG building under that point.
BUILDINGS = [
    {
        "name": "Sint-Martinuskerk",
        "note": "Laatgotische hallenkerk met de toren van 73 m",
        "kind": "Rijksmonument · 1456-1528",
        "address": "Markt",
        "stop": "Sint-Martinuskerk",
        "at": (177316.0, 362744.5),  # the middle of the tower in AHN, 73.6 m to the top
        "style": "church",
        "wall": (150, 100, 78),
        "roof": (70, 72, 80),
    },
    {
        "name": "Museum W",
        "note": "Het oude stadhuis aan de Markt",
        "addrs": ["Markt 7"],
        "kind": "Museum · voormalig stadhuis",
        "address": "Markt 7",
        "text": "Museum voor cultuurhistorie en hedendaagse kunst in het voormalige stadhuis, een rijksmonument. Tot 2020 heette het Gemeentemuseum Jacob van Horne, naar de graaf die Weert zijn kasteel en zijn klooster gaf. Na een verbouwing ging het in mei 2022 weer open.",
        "more": WP + "Museum_W",
        "photo": ("Gemeentemuseum Weert Jacob van Horne.jpg", "Het voormalige raadhuis in 2013, Smiley.toerist, CC BY-SA 3.0"),
        "web": "https://www.museumw.nl",
    },
    {
        "name": "Muntgebouw",
        "addrs": ["Muntpromenade 7"],
        "kind": "Rijksmonument · ca. 1580",
        "address": "Muntpromenade 7",
        "stop": "De Weertse munt",
    },
    {
        "name": "Munttheater",
        "latlon": (51.25399, 5.70469),
        "kind": "Theater · 1974",
        "text": "In 1974 opgericht als Cultureel Centrum De Munt, boven winkelcentrum de Muntpassage. De zaal en het balkon hebben samen 459 plaatsen; er komen zo'n 50.000 bezoekers per jaar.",
        "more": WP + "Munttheater",
        "web": "https://www.munttheater.nl",
    },
    {
        "name": "Ursulinenklooster",
        "addrs": ["Langstraat 20"],
        "kind": "Voormalig klooster · 1876",
        "address": "Langstraat 20",
        "text": "Gebouwd in 1876 in Duitse neogotiek voor de zusters ursulinen, die door de Kulturkampf uit het Duitse Dorsten waren verdreven. Ze begonnen in Weert een pensionaat (1883) en een school (1895). In 1989 vertrokken de zusters; alleen het hoofdgebouw en de Mariakapel bleven staan en werden winkels.",
        "more": WP + "Ursulinenklooster_(Weert)",
    },
    {
        "name": "Abdij Maria Hart",
        "addrs": ["Maasstraat 17"],
        "kind": "Klooster · rijksmonument",
        "address": "Maasstraat 17",
        "text": "Hier werd in 1442 het klooster Maria Wijngaard gesticht, voor kanunnikessen van Augustinus. De Fransen hieven het in 1797 op. In 1843 trokken birgittinessen uit Uden erin, en dat is het nog steeds: een birgittinessenklooster, met een kapel uit 1843 aan de straat en een beeldje van de heilige Birgitta boven de poort.",
        "more": WP + "Abdij_Maria_Hart",
        "photo": ("Klooster Maasstraat.jpg", "Het klooster aan de Maasstraat in 2008, Thommorris, CC BY-SA 3.0"),
    },
    {
        "name": "Kasteel Nijenborgh",
        "note": "Ruïne van het kasteel van de graven van Horne",
        "latlon": (51.25638, 5.70883),
        "kind": "Rijksmonument · 1455-1461",
        "stop": "De Nijenborgh",
    },
    {
        "name": "Minderbroedersklooster en Paterskerk",
        "note": "Klooster uit 1461 met de laatgotische Paterskerk",
        "at": (177699.2, 363378.8),  # the ridge of the church in AHN
        "kind": "Rijksmonument · 1461",
        "address": "Biest 43",
        "stop": "Minderbroeders op de Biest",
        "style": "church",
        "wall": (156, 96, 74),
        "roof": (72, 74, 82),
    },
    {
        "name": "Station Weert",
        "latlon": (51.24894, 5.70410),
        "kind": "Rijksmonument · 1914",
        "address": "Stationsplein",
        "stop": "De IJzeren Rijn",
    },
    {
        "name": "Bethelkerk",
        "addrs": ["Maaspoort 30"],
        "kind": "Protestantse kerk · 1912",
        "address": "Maaspoort 30",
        "text": "De protestanten van Weert moesten lang naar Budel lopen om te kerken. In 1852 kregen ze een eigen gemeente, die samenkwam in een pand aan de Oelemarkt. Deze achtkante zaalkerk is gebouwd van 1910 tot 1912, naar ontwerp van George van Heukelom, de architect van het station. Boven de ingang staat: Gewisselijk is de Heer aan deze plaats.",
        "more": WP + "Bethelkerk_(Weert)",
    },
    {
        "name": "Fatimahuis",
        "addrs": ["Coenraad Abelsstraat 31A"],
        "kind": "Voormalige kerk · 1955",
        "address": "Coenraad Abelsstraat 31a",
        "text": "De waaiervormige kerk van baksteen en beton gaf de wijk Fatima haar naam; daarvoor heette de arbeiderswijk Molenveld. De Weertse architect Pierre Weegels ontwierp haar en in 1955 was ze klaar. Sinds 2011 is het geen parochiekerk meer: als Fatimahuis heeft het gebouw een sociaal en cultureel doel, en op zondag viert de Eritrees-orthodoxe kerk er de dienst.",
        "more": WP + "Onbevlekt_Hart_van_Mariakerk_(Weert)",
    },
    {
        "name": "Kapel van de paters van de Heilige Geest",
        "addrs": ["Coenraad Abelsstraat 36"],
        "kind": "Moskee · kapel uit 1911",
        "address": "Coenraad Abelsstraat 36",
        "text": "De paters van de Heilige Geest kwamen in 1904 uit Lier naar Weert om missionarissen op te leiden; hun internaat groeide van dertig naar zo'n tweehonderd leerlingen. De kapel, ontworpen door Pierre Cuypers jr., was klaar in 1911. Het internaat sloot in 1970 en het missiehuis is gesloopt, maar de kapel bleef: het is nu de Turkse moskee.",
        "more": WP + "Klooster_van_de_Paters_van_de_Heilige_Geest",
        "photo": ("'Turkse moskee' Coenraad Abelstraat Weert.jpg", "De kapel als moskee in 2012, FaceMePLS, CC BY 2.0"),
    },
    {
        "name": "Molen Sint Oda",
        "at": (176497.2, 362938.2),  # the cap of the mill in AHN
        "style": "house",
        "wall": (128, 76, 58),
        "roof": (58, 60, 66),
        "kind": "Rijksmonument · 1883",
        "address": "Suffolkweg",
        "text": "Ronde bakstenen beltmolen uit 1883, genoemd naar de heilige Oda. Tot 2002 maalde de molenaar hier voor zijn beroep rogge en boekweit. Daarna stond de molen stil, tot hij in 2008 weer draaide.",
        "more": WP + "Sint_Oda_(molen)",
        "photo": ("Weert StOda.jpg", "Molen Sint Oda in 2008, Groucho M, CC BY-SA 3.0"),
    },
    {
        "name": "Molen Wilhelmus-Hubertus",
        "at": (176974.2, 363402.2),  # the cap of the mill in AHN
        "style": "house",
        "wall": (128, 76, 58),
        "roof": (58, 60, 66),
        "kind": "Rijksmonument · 1904",
        "address": "Oude Hushoverweg 30",
        "text": "Beltmolen uit 1904, gebouwd nadat de standerdmolen op deze plek door de bliksem was getroffen en afbrandde. Hij maalde tot vlak voor de Tweede Wereldoorlog. Bij de restauratie van 1961 kreeg hij zijn naam, naar de opa van de molenbouwer. Nu is het een restaurant; de molen kan nog draaien.",
        "more": WP + "Wilhelmus-Hubertus",
        "photo": ("Weert, Wilhelmus-Hubertus, beltmolen 02a.JPG", "De Wilhelmus-Hubertus in 2008, Noorse, CC BY-SA 3.0"),
    },
    {
        "name": "Boonesmolen",
        "addrs": ["Julianalaan 24"],
        "kind": "Molenromp · 1855",
        "address": "Julianalaan 24",
        "text": "Van deze koren-, pel- en oliemolen uit 1855 staat alleen de romp nog. Hij heet naar de familie Boonen, eigenaar van 1863 tot 1927. Toen de buurt achter het station volgebouwd raakte, ving de molen steeds minder wind; in de zware storm van 9 februari 1949 brak de as. Daarna stond er een grote reclame voor Blue Band op de romp. De kap ging er in 1968 af.",
        "more": WP + "Boonesmolen",
    },
    {
        "name": "Sint-Rumolduskapel",
        "latlon": (51.25435, 5.70101),
        "kind": "Rijksmonument · ca. 1775",
        "address": "Molenpoort",
        "text": "Al rond 1400 stond hier, buiten de Molenpoort, een kapel waar Sint-Rumoldus werd aangeroepen tegen kwade ogen, keelpijn en veeziekten. Het kapelletje van nu is uit de 18e eeuw; de linden eromheen zijn in 1838 geplant. Sinds de restauratie van 1975 is het de gedachteniskapel voor de Weertenaren die in de Tweede Wereldoorlog omkwamen, met een kunstwerk van Felix van Kalmthout: Opdat wij niet vergeten.",
        "more": WP + "Sint-Rumolduskapel_(Weert)",
        "photo": ("Aanzicht - Weert - 20251897 - RCE.jpg", f"De kapel in 1964, G.Th. Delemarre, {RCE}"),
    },
    {
        "name": "Sint-Jozefkerk",
        "at": (176911.8, 361369.2),  # the tower in AHN, 45 m to the top
        "kind": "Rijksmonument · 1939",
        "address": "Sint Jozefskerkplein 1",
        "text": "Neoromaanse bakstenen kerk van Alphons Boosten uit 1939, met een toren van 45 meter. Ze is gebouwd voor de wijk Keent, waar de militairen van de nieuwe Van Hornekazerne kwamen te wonen.",
        "more": WP + "Sint-Jozefkerk_(Weert)",
        "photo": ("Kerk Keent.jpg", "De Sint-Jozefkerk in 2009, Thommorris, CC BY-SA 3.0"),
        "style": "church",
        "wall": (164, 110, 84),
        "roof": (74, 76, 84),
    },
    {
        "name": "Van Hornekazerne",
        "addrs": ["Kazernelaan 101"],
        "kind": "Kazerne · 1938",
        "address": "Kazernelaan 101",
        "stop": "Kazerne en kazematten",
    },
    {
        "name": "Verrezen Christuskerk",
        "latlon": (51.24362, 5.70912),
        "kind": "Kerk · 1972",
        "address": "Oranjeplein",
        "text": "De kerk van de nieuwbouwwijk Moesel, die in 1963 een eigen rectoraat kreeg. Eerst diende de Moeselkapel als noodkerk, daarna een houten noodkerk aan de Christinelaan. Het lage bakstenen gebouw met plat dak en zonder toren, van architect P.W.J. Coenders, was klaar in 1972. Gène Eggen maakte de wand van glas in lood.",
        "more": WP + "Verrezen_Christuskerk_(Weert)",
    },
    {
        "name": "Moeselkapel",
        "latlon": (51.24169, 5.71635),
        "kind": "Kapel · 1912",
        "address": "Irenelaan",
        "text": "Kapel uit 1912 aan het Moeselplein, gewijd aan Onze-Lieve-Vrouw van Lourdes. Toen de wijk Moesel in de jaren zestig werd gebouwd, was dit even de noodkerk.",
        "more": WP + "Moeselkapel",
    },
    {
        "name": "Meelfabriek",
        "at": (176224.0, 362671.0),  # the 35 m tall factory of 1928 in 3D BAG
        "kind": "Rijksmonument · 1928",
        "address": "Industriekade 38",
        "text": "Meelfabriek pal aan de Zuid-Willemsvaart, met een havenkraan aan de kade om de schepen te lossen. Het complex is een rijksmonument.",
        "photo": ("Overzicht vanuit het oosten met havenkraan, rechts de Zuid-Willemsvaart - Weert - 20347947 - RCE.jpg", f"De meelfabriek met de havenkraan in 2003, IJsbrand Heins, {RCE}"),
    },
]

# Points without a building of their own.
POINTS = [
    {"name": "Markt", "latlon": (51.25340, 5.70655), "kind": "Plein", "stop": "Marktrechten"},
    {"name": "Stadsbrug", "latlon": (51.25785, 5.70363), "kind": "Hefbrug · 1968", "stop": "De Zuid-Willemsvaart"},
    {
        "name": "Biesterbrug",
        "latlon": (51.26137, 5.71400),
        "kind": "Ophaalbrug · 1997",
        "text": "De Beesterbrök verbindt de Biest met Molenakker. Voor die wijk er lag, liep hier de weg van de stad naar het kerkdorp Laar. De ophaalbrug van nu is in 1997 gebouwd op de plek van een oude gietijzeren brug van hetzelfde type.",
        "more": WP + "Biesterbrug",
        "photo": ("Biesterbrug.jpg", "De Biesterbrug in 2009, Weertenaar, CC BY-SA 3.0"),
    },
    {"name": "Kleipijpenoven", "latlon": (51.26181, 5.71409), "kind": "Rijksmonument · 1856", "address": "Noordkade", "stop": "Kleipijpen van Trumm-Bergmans"},
    {"name": "Scheepswerf", "latlon": (51.26305, 5.72001), "kind": "Scheepswerf · 1907", "stop": "De Weerter kempenaar"},
    {"name": "Keltische Schans", "latlon": (51.26427, 5.71452), "kind": "Archeologische vindplaats", "stop": "De Keltische Schans"},
    {"name": "Aldenborgh", "latlon": (51.25927, 5.71247), "kind": "Verdwenen kasteel · ca. 1290", "stop": "De Aldenborgh"},
    {"name": "Standbeeld Philips de Montmorency", "latlon": (51.25719, 5.70936), "kind": "Standbeeld", "stop": "De graaf van Horne onthoofd"},
    {"name": "Suffolk-monument", "latlon": (51.25781, 5.70321), "kind": "Oorlogsmonument · 2002", "stop": "Bevrijd door de Suffolks"},
    {"name": "Verzetsmonument", "latlon": (51.25410, 5.70330), "kind": "Oorlogsmonument · 2022"},
    {
        "name": "Kazematten aan de Noordkade",
        "latlon": (51.25926, 5.70610),
        "kind": "Rijksmonumenten · 1939",
        "address": "Noordkade",
        "text": "De Peel-Raamstelling, in 1939 aangelegd, liep van de Maas bij Grave door de Peel en langs de Zuid-Willemsvaart tot de Belgische grens bij Weert. Langs het kanaal stonden de betonnen kazematten om de tweehonderd meter, vooral bij de bruggen. Aan de Noordkade staan er nog drie. In de ochtend van 11 mei 1940 is bij Weert kort gevochten; toen was de stelling al gevallen.",
        "more": WP + "Peel-Raamstelling",
    },
    {
        "name": "Sint-Martinuskerkhof",
        "latlon": (51.25458, 5.70131),
        "kind": "Begraafplaats",
        "address": "Molenpoort",
        "text": "Het kerkhof van de Sint-Martinuskerk ligt een paar honderd meter van de kerk, buiten de oude Molenpoort, naast de Sint-Rumolduskapel. Er is ook een urnenmuur.",
        "more": WP + "Sint-Martinuskerkhof_(Weert)",
        "photo": ("A Winters Day (3176450077).jpg", "Het kerkhof aan de Molenpoort in de winter van 2009, FaceMePLS, CC BY 2.0"),
    },
    {
        "name": "Muurschildering: Ik, Philips van Horne, mag graag op reis gaan",
        "latlon": (51.25268, 5.70759),
        "kind": "Muurschildering · 2018",
        "text": "Een van de muurschilderingen die in 2018 in de binnenstad zijn gemaakt, 450 jaar na de dood van Philips de Montmorency, graaf van Horne.",
        "photo": ("Muurschildering Philips van Horne Weert 05.jpg", "De muurschildering in 2020, FrDr, CC BY-SA 4.0"),
    },
    {
        "name": "Muurschildering: Ik, Philips van Horne, smeek om vergeving",
        "latlon": (51.25162, 5.70455),
        "kind": "Muurschildering · 2018",
        "text": "De onthoofding van Philips van Horne in Brussel, op 5 juni 1568. Een van de muurschilderingen die in 2018 in de binnenstad zijn gemaakt, 450 jaar na zijn dood.",
        "photo": ("Muurschildering 'de onthoofding van Philips van Horne' Weert 01.jpg", "De muurschildering in 2020, FrDr, CC BY-SA 4.0"),
    },
    {
        "name": "Muurschildering: Wij, liga der groten, nodigen U uit",
        "latlon": (51.25404, 5.70505),
        "kind": "Muurschildering · 2018",
        "text": "Bourgondische heren aan tafel, met Walburgis van Nieuwenaer, de vrouw van Philips van Horne. Een van de muurschilderingen die in 2018 in de binnenstad zijn gemaakt.",
        "photo": ("Muurschildering 'Bourgondische heren' Weert 04.jpg", "De muurschildering in 2020, FrDr, CC BY-SA 4.0"),
    },
    {"name": "Kunstwerk: On the Shoulder of Giants", "latlon": (51.25659, 5.70112), "kind": "Kunstwerk", "text": "Beeld van Studio Job."},
    {
        "name": "Vastelaovundj-monumênt",
        "latlon": (51.24998, 5.71790),
        "kind": "Kunstwerk · 2015",
        "text": "Monument voor de vastelaovendj van Jan van Riet. Met carnaval heten de Weertenaren Rogstaekers, naar een sage uit 1653: een voerman verloor in Laar een rog, en de Weertenaren, die zo'n beest nooit hadden gezien, hielden hem met zijn valse ogen en pijlstaart voor de duivel. De klokken luidden, de schutterij rukte uit en er kwam een kanon bij. Jan, de zoon van de waard van 't Bruyne Paerd, stak het beest ten slotte aan zijn riek. Toen kwam de voerman terug en lachte hen hartelijk uit.",
        "more": WP + "Rogstaekers",
    },
    {"name": "Heilig Hartbeeld", "latlon": (51.25099, 5.70640), "kind": "Beeld", "text": "Heilig Hartbeeld van de beeldhouwer August Falise."},
]

# Series in the viewer's panel: a walk past these places, starting with the one nearest the middle of the map.
CATEGORIES = [
    ("horne", "De graven van Horne", [
        "Kasteel Nijenborgh", "Aldenborgh", "Minderbroedersklooster en Paterskerk", "Sint-Martinuskerk", "Muntgebouw", "Museum W",
        "Standbeeld Philips de Montmorency", "Muurschildering: Ik, Philips van Horne, mag graag op reis gaan",
        "Muurschildering: Ik, Philips van Horne, smeek om vergeving", "Muurschildering: Wij, liga der groten, nodigen U uit",
    ]),
    ("kerken", "Kerken en kloosters", [
        "Sint-Martinuskerk", "Abdij Maria Hart", "Ursulinenklooster", "Minderbroedersklooster en Paterskerk", "Bethelkerk",
        "Sint-Rumolduskapel", "Fatimahuis", "Kapel van de paters van de Heilige Geest", "Sint-Jozefkerk", "Verrezen Christuskerk", "Moeselkapel",
    ]),
    ("kanaal", "Langs het kanaal", ["Stadsbrug", "Suffolk-monument", "Kazematten aan de Noordkade", "Biesterbrug", "Kleipijpenoven", "Scheepswerf", "Meelfabriek"]),
    ("molens", "Molens", ["Molen Sint Oda", "Molen Wilhelmus-Hubertus", "Boonesmolen"]),
    ("oorlog", "Oorlog en herdenking", ["Sint-Rumolduskapel", "Verzetsmonument", "Suffolk-monument", "Kazematten aan de Noordkade", "Van Hornekazerne"]),
    ("kunst", "Kunst", [
        "Muurschildering: Wij, liga der groten, nodigen U uit", "Muurschildering: Ik, Philips van Horne, mag graag op reis gaan",
        "Muurschildering: Ik, Philips van Horne, smeek om vergeving", "Standbeeld Philips de Montmorency", "Kunstwerk: On the Shoulder of Giants",
        "Heilig Hartbeeld", "Vastelaovundj-monumênt",
    ]),
]

# What the viewer shows when a place is clicked; the rest of an entry is for the render.
INFO = ("note", "kind", "text", "address", "web", "more", "photo", "stop")

# Steel lattice telecom masts: {"latlon": (lat, lon), "height": m, "base": m, "tip": m}.
MASTS = []


def point_in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


ADDRESSES = None


def address_xy(name):
    """RD position of a BAG address such as "Geldersestraat 3" (data/raw/addresses.json, from scripts/fetch.py)."""
    global ADDRESSES
    if ADDRESSES is None:
        ADDRESSES = {label.split(", ")[0]: (x, y) for x, y, label in json.loads((RAW / "addresses.json").read_text())}
    return ADDRESSES[name]


def building_at(rings, x, y):
    for rid, ring, a in rings:
        if point_in_ring(x, y, ring):
            return rid, a
    return None, None


def main():
    feats = [json.loads(line) for line in open(RAW / "3dbag.jsonl")]
    rings = []
    for f in feats:
        t = f["transform"]
        V = np.array(f["vertices"], dtype=np.float64) * t["scale"] + t["translate"]
        co = f["CityObjects"][f["id"]]
        rings.append((f["id"], V[co["geometry"][0]["boundaries"][0][0]][:, :2], co["attributes"]))

    out = {"buildings": {}, "places": [], "masts": [], "hotspots": [], "categories": []}
    for b in BUILDINGS:
        if "addrs" in b:
            pts = [address_xy(a) for a in b["addrs"]]
            pids = [building_at(rings, *pt)[0] for pt in pts]
            assert all(pids), f"{b['name']}: no building at {b['addrs']}"
            x, y = np.mean(pts, axis=0)
            out["places"].append({"name": b["name"], "note": b.get("note"), "x": x, "y": y, "h": 4.0})
            out["hotspots"].append({"name": b["name"], "pids": pids, "x": x, "y": y, **{k: b[k] for k in INFO if k in b}})
            print(f"{b['name']}: {', '.join(pids)}")
            continue
        x, y = b["at"] if "at" in b else wgs_to_rd(*b["latlon"])
        pid, attrs = None, None
        for rid, ring, a in rings:
            if point_in_ring(x, y, ring):
                pid, attrs = rid, a
                break
        if pid is None:
            d = [(np.hypot(*(ring.mean(0) - (x, y))), rid, a) for rid, ring, a in rings]
            dist, pid, attrs = min(d, key=lambda t: t[0])
            if dist > 20:
                pid = None
        height = ((attrs or {}).get("b3_h_dak_max") or 0) - ((attrs or {}).get("b3_h_maaiveld") or 0)
        if "tower" in b:
            height = b["tower"]["top"]
        elif "turret" in b:
            height = b["turret"]["top"]
        out["places"].append({"name": b["name"], "note": b.get("note"), "x": x, "y": y, "h": round(height, 1)})
        if pid and "style" in b:
            out["buildings"][pid] = {k: v for k, v in b.items() if k not in ("at", "latlon", *INFO)}
        if pid:
            out["hotspots"].append({"name": b["name"], "pid": pid, "x": x, "y": y, **{k: b[k] for k in INFO if k in b}})
        print(f"{b['name']}: {pid or 'no building'}")
    for p in POINTS:
        x, y = p["at"] if "at" in p else address_xy(p["addr"]) if "addr" in p else wgs_to_rd(*p["latlon"])
        out["places"].append({"name": p["name"], "note": p.get("note"), "x": x, "y": y, "h": 2.0})
        out["hotspots"].append({"name": p["name"], "x": x, "y": y, **{k: p[k] for k in INFO if k in p}})
    for m in MASTS:
        x, y = wgs_to_rd(*m["latlon"])
        out["masts"].append({**{k: v for k, v in m.items() if k != "latlon"}, "x": x, "y": y})
    names = {h["name"] for h in out["hotspots"]}
    for key, label, members in CATEGORIES:
        missing = [n for n in members if n not in names]
        assert not missing, f"{label}: no hotspot for {missing}"
        out["categories"].append({"key": key, "label": label, "names": members})
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "landmarks.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
