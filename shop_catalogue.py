#!/usr/bin/env python3
"""
Read the 2026 waterproofing price list and turn it into the catalogue the shop
pages are built from.

The spreadsheet is the single source of truth: nothing about a product is typed
out by hand anywhere in the site. Replace data/waterproofing-price-list-2026.xlsx
with a newer list, re-run build_shop.py, and the whole shop follows.

    from shop_catalogue import load_catalogue
    cat = load_catalogue()
"""
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, 'data', 'waterproofing-price-list-2026.xlsx')

VAT_RATE = 0.20

# Column order in Sheet1. Sheet2 is the same list shouted in capitals, so Sheet1
# is the one worth reading.
COL_CODE, COL_DESC, COL_PRICE, COL_UOM = 0, 1, 2, 3
COL_CATEGORY, COL_LINE, COL_LINE_DESC, COL_GROUP = 4, 5, 6, 7
COL_PRICE_2025, COL_SALES_UNIT, COL_STATUS = 8, 9, 10


def slugify(text):
    text = unicodedata.normalize('NFKD', str(text)).encode('ascii', 'ignore').decode()
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return re.sub(r'-{2,}', '-', text)


# ---- names ----------------------------------------------------------------
# The list writes everything in sentence case with the units run together
# ("Mapelastic Aquadefense bucket 15kg"). Product names read better with the
# trade abbreviations and brand names cased the way the manufacturers write them.
CASE_FIXES = {
    'dpc': 'DPC', 'dpm': 'DPM', 'sds': 'SDS', 'pvc': 'PVC', 'hd': 'HD',
    'uv': 'UV', 'wp': 'WP', 'ibc': 'IBC', 'led': 'LED', 'ble': 'BLE',
    'cm8': 'CM8', 'cm20': 'CM20', 'cm3': 'CM3', 'k20': 'K20', 'utt': 'UTT',
    'tt': 'TT', 'lv': 'LV', 'aks': 'AKS', 'crt': 'CRT', 'mms3': 'MMS3',
    'f/i': 'F/I', 'm/b': 'M/B', 'c2f': 'C2F', 'pu': 'PU', 'ph': 'pH',
    'usb': 'USB', 'sm': 'm²', 'mt': 'm',
}
def prettify(desc):
    """Turn a price-list description into a product name fit for a shop page."""
    text = re.sub(r'\s+', ' ', str(desc)).strip()
    words = []
    for word in text.split(' '):
        bare = word.strip('()').lower()
        if bare in CASE_FIXES:
            words.append(word.lower().replace(bare, CASE_FIXES[bare]))
        elif re.match(r'^[a-z]{2,}\d', bare):
            # product codes written inline: mcs1, cm8, k11 -> MCS1, CM8, K11
            words.append(word.upper())
        elif any(ch.isdigit() for ch in bare):
            words.append(word.lower())
        else:
            words.append(word)
    out = ' '.join(words)
    out = re.sub(r'\s+1\s*pc$', '', out)                  # "…alarm 1pc" -> "…alarm"
    out = re.sub(r'(\d)\s*sm\b', '\\1 m²', out)          # 20sm -> 20 m²
    out = re.sub(r'(\d)\s*mt\b', r'\1m', out)             # 20mt -> 20m
    return out[0].upper() + out[1:] if out else out


def title_case_group(text):
    """CAVITY DRAIN SYSTEMS -> Cavity Drain Systems, with the trade spellings kept."""
    fixed = {
        'HELYCAL': 'Helical', 'INIJECTION': 'Injection', 'APPLYED': 'Applied',
        'SPUR': 'Spur', 'C2F': 'C2F', 'PVC': 'PVC', 'TU': 'TU', 'AND': 'and',
        'FOR': 'for', 'OF': 'of', '&': '&', 'TT': 'TT', 'EQUIPMENTS': 'Equipment',
        'POST-APPLYED': 'Post-applied', 'SELF-ADHESIVES': 'Self-adhesive',
        'ANTI-CONDENSATION': 'Anti-condensation', 'HYDRO-SWELLING': 'Hydro-swelling',
        'RE-INJECTABLE': 'Re-injectable',
        'BITUMINOUS': 'Bituminous', 'BENTONITIC': 'Bentonite',
    }
    words = []
    for word in str(text).split():
        if word in fixed:
            words.append(fixed[word])
        elif word in ('PURTOP', 'MAPELASTIC'):
            words.append(word.capitalize())
        else:
            words.append(word.capitalize())
    out = ' '.join(words)
    return out[0].upper() + out[1:] if out else out


# ---- brands ---------------------------------------------------------------
# Every product name starts with, or contains, the range it belongs to. The
# first match wins, so the more specific ranges are listed before the umbrella
# brand they sit under.
BRAND_RULES = [
    ('Protimeter', r'\bprotimeter\b'),
    ('Triton', r'\btriton\b'),
    ('Sika', r'\bsika\b'),
    ('Thor Helical', r'\bthor\b|\bheliforce\b|\bhelical\b|\bhelibar\b'),
    ('Wykamol', r'\bwykamol\b|\bwyk\b|\bcm8\b|\bcm20\b|\bcm3\b|\bwaterguard\b|'
                r'\bdrytech\b|\bdampsolve\b|\bmicrotech\b|\bultracure\b|\bquadproof\b|'
                r'\bdampstore\b|\bnomould\b|\bdryseal\b|\bdryshield\b|\btechnicseal\b'),
    ('Mapei', r'\bmape\w*|\bidrostop\b|\bpurtop\b|\bfoamjet\b|\bresfoam\b|'
              r'\blamposilex\b|\bplaniseal\b|\bpolyglass\b|\bdynamon\b|\bantipluviol\b|'
              r'\belastocolor\b|\bprimer\b\s+\bsn\b|\bquarzolite\b|\bsilexcolor\b|'
              r'\bkerabond\b|\bkeraflex\b|\baquaflex\b|\bmonofinish\b|\bnivoplan\b|\butt\b'),
    ('Lignum', r'\blignum\b'),
]


def detect_brand(name, code):
    haystack = (name + ' ' + code).lower()
    for brand, pattern in BRAND_RULES:
        if re.search(pattern, haystack):
            return brand
    if code.upper().startswith('WYK-'):
        return 'Wykamol'
    return 'Other Manufacturers'


# ---- product kind, which decides the illustration -------------------------
# Ordered: the first rule that matches a product wins, so a "membrane roll" is
# drawn as a membrane and not as a plain roll.
KIND_RULES = [
    ('meter',     r'protimeter|moisture meter|hygro|thermo|logger|survey master|mms\b|\bble\b'),
    ('pump',      r'\bpump\b|\bpumponly\b|macerator'),
    ('float',     r'float switch|sump alarm|\balarm\b|control panel|battery back'),
    ('sump',      r'\bsump\b|chamber|\bliner\b'),
    ('fan',       r'\bfan\b|ventilat|extract|\bpiv\b|air brick|airbrick|\bvent\b'),
    ('channel',   r'waterguard|\bchannel\b|drainage channel|\bdrain\b.*\bchannel\b'),
    ('drill',     r'drill bit|sds\+|\bsds\b'),
    ('tie',       r'helical|crack stitching|\btie\b|drive pin|wall tie|restraint|\bbar\b'),
    ('nozzle',    r'\bnozzle\b|\bsleeving\b|earth wire|earth rod|\bpacker\b'),
    ('valve',     r'valve|non return|jetting eye|\bconnector\b|\belbow\b|\bcoupling\b'),
    ('plug',      r'\bplug\b|\bplugs\b|surefix|\bcob\b|\bseal\b.*\bbag\b|sealing plug'),
    ('tool',      r'applicator|\bgun\b|paddle|mixing|setting tool|adaptor|trowel|roller|'
                  r'\bbrush\b|\bspray\b|\bkit\b|\btool\b'),
    ('mesh',      r'\bnet\b|mesh|poliestere|mapetex|fibre|reinforc|scrim|geotex'),
    ('tape',      r'\btape\b|mapeband|idrostop|waterstop|\bband\b|\bhose\b|\brope\b|'
                  r'joint\b|\bstrip\b'),
    ('membrane',  r'membrane|mapeplan|mapeproof|mapethene|\bcm8\b|\bcm20\b|\bk20\b|'
                  r'\bmesh membrane\b|dimple|\bfoil\b|\bsheet\b'),
    ('board',     r'\bboard\b|\bslab\b|insulat'),
    ('cartridge', r'cartridge|\bcrt\b|sausage|\bcaulk\b'),
    ('ibc',       r'\bibc\b'),
    ('drum',      r'\bdrum\b'),
    ('jerrycan',  r'jerrycan|jerry can'),
    ('bottle',    r'\bbottle\b'),
    ('bucket',    r'\bbucket\b|\bpail\b|\btub\b'),
    ('bag',       r'\bbag\b|\bsack\b'),
    ('roll',      r'\broll\b'),
    ('box',       r'\bbox\b|\bcarton\b|\bunit\b|\bcrate\b'),
]

UOM_KIND = {
    'Roll': 'roll', 'Bag': 'bag', 'bucket': 'bucket', 'Jerrycan': 'jerrycan',
    'bottle': 'bottle', 'drum': 'drum', 'IBC': 'ibc', 'crt': 'cartridge',
    'box': 'box', 'sausage': 'cartridge', 'board': 'board', 'm2': 'membrane',
    'm': 'roll', 'unit': 'box', 'pc': 'part',
}


# A product sold by the bucket is drawn as a bucket whatever it is made of, so
# these units short-circuit the keyword rules below. Instruments and machines
# are the exception: a moisture meter boxed in a carton is still a meter.
CONTAINER_UOMS = ('Bag', 'bucket', 'Jerrycan', 'bottle', 'drum', 'IBC', 'crt',
                  'sausage', 'Roll', 'board', 'm2')
CONTAINER_OVERRIDE = r'protimeter|moisture meter|\bpump\b|\bfan\b|logger|\bmeter\b'


def detect_kind(name, group, uom):
    haystack = (name + ' ' + group).lower()
    if uom in CONTAINER_UOMS and not re.search(CONTAINER_OVERRIDE, haystack):
        if uom == 'Roll':
            # a roll of membrane and a roll of jointing tape look nothing alike,
            # and only the product's own name says which one this is
            sheet = re.search(r'membrane|mapeproof|mapethene|geotex|dimple|\bfoil\b|'
                              r'\bnet\b|mapetex|poliestere|\bsheet\b|\bdpm\b',
                              name.lower())
            return 'membrane' if sheet else 'tape'
        return UOM_KIND[uom]
    for kind, pattern in KIND_RULES:
        if re.search(pattern, haystack):
            return kind
    return UOM_KIND.get(uom, 'part')


# ---- pack size ------------------------------------------------------------
PACK_PATTERNS = [
    r'\d+(?:\.\d+)?\s*(?:kg|ltr|lt|ml|g)\b',
    r'\d+(?:\.\d+)?\s*(?:sm|m2|m\u00b2)\b',
    r'\d+(?:\.\d+)?\s*(?:mt|m)\b',
    r'\d+\s*pcs?\b',
]


def detect_pack(desc, uom):
    """The size a customer actually buys: "20kg · per bucket · box of 4"."""
    text = str(desc).lower()
    box = re.search(r'box of (\d+)', text)
    text = re.sub(r'\([^)]*\)', ' ', text)          # drop the bracketed notes
    text = re.sub(r'/[\d.]+\s*(?:lb|ft|oz|in)\b', ' ', text)   # drop imperial conversions
    text = re.sub(r'\b\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?\s*m?\b', ' ', text)  # 2x20m roll widths

    size = ''
    for pattern in PACK_PATTERNS:
        found = re.findall(pattern, text)
        if found:
            size = found[-1].replace(' ', '')
            break
    size = re.sub(r'(sm|m2)$', ' m\u00b2', size)
    size = re.sub(r'^(\d+(?:\.\d+)?)mt$', r'\g<1>m', size)

    label = {'pc': 'each', 'unit': 'per unit'}.get(uom, 'per ' + uom.lower())
    if size and size != '1pc':
        label = '%s \u00b7 %s' % (size.strip(), label)
    if box:
        label += ' \u00b7 box of %s' % box.group(1)
    return label


# ---- the catalogue --------------------------------------------------------
def load_catalogue(path=XLSX):
    import openpyxl

    workbook = openpyxl.load_workbook(path, data_only=True)
    sheet = workbook['Sheet1']

    products = []
    seen = set()
    for row in sheet.iter_rows(min_row=2, values_only=True):
        code = str(row[COL_CODE] or '').strip()
        desc = str(row[COL_DESC] or '').strip()
        if not code or not desc:
            continue
        if str(row[COL_STATUS] or '').strip().lower() != 'active':
            continue

        try:
            price = float(row[COL_PRICE])
        except (TypeError, ValueError):
            price = 0.0
        try:
            price_2025 = float(row[COL_PRICE_2025])
        except (TypeError, ValueError):
            price_2025 = 0.0

        name = prettify(desc)
        uom = str(row[COL_UOM] or 'pc').strip()
        group = title_case_group(row[COL_GROUP] or 'Other')
        if group == 'Other':
            # "OTHER" as a category name tells a customer nothing; it is always
            # the loose fixings and sundries that sit under its range.
            group = 'Other %s Accessories' % title_case_group(row[COL_LINE_DESC] or '').split(' and ')[0]
        line = title_case_group(row[COL_LINE_DESC] or 'Other')

        slug = slugify(name + '-' + code)
        if slug in seen:                      # two codes share a description
            slug = slugify(name + '-' + code + '-2')
        seen.add(slug)

        products.append({
            'code': code,
            'slug': slug,
            'name': name,
            'price': round(price, 2),
            'price_2025': round(price_2025, 2),
            'poa': price <= 0,
            'uom': uom,
            'pack': detect_pack(desc, uom),
            'line': line,
            'line_slug': slugify(line),
            'group': group,
            'group_slug': slugify(group),
            'brand': detect_brand(name, code),
            'kind': detect_kind(name, group, uom),
        })

    products.sort(key=lambda p: (p['line'], p['group'], p['name']))

    lines = {}
    for product in products:
        line = lines.setdefault(product['line_slug'], {
            'name': product['line'], 'slug': product['line_slug'],
            'groups': {}, 'count': 0,
        })
        line['count'] += 1
        group = line['groups'].setdefault(product['group_slug'], {
            'name': product['group'], 'slug': product['group_slug'],
            'line': product['line'], 'line_slug': product['line_slug'], 'count': 0,
        })
        group['count'] += 1

    ordered_lines = sorted(lines.values(), key=lambda l: -l['count'])
    for line in ordered_lines:
        line['groups'] = sorted(line['groups'].values(), key=lambda g: -g['count'])

    brands = {}
    for product in products:
        brands[product['brand']] = brands.get(product['brand'], 0) + 1

    return {
        'products': products,
        'lines': ordered_lines,
        'brands': sorted(brands.items(), key=lambda b: (-b[1], b[0])),
        'vat': VAT_RATE,
    }


if __name__ == '__main__':
    catalogue = load_catalogue()
    print('%d products, %d lines, %d brands'
          % (len(catalogue['products']), len(catalogue['lines']), len(catalogue['brands'])))
    for line in catalogue['lines']:
        print('  %-42s %3d  (%d groups)' % (line['name'], line['count'], len(line['groups'])))
    print()
    for brand, count in catalogue['brands']:
        print('  %-22s %3d' % (brand, count))
