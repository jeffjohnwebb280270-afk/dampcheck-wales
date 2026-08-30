#!/usr/bin/env python3
"""
Build the trade store from the price list.

    python3 build_shop.py

Reads  data/waterproofing-price-list-2026.xlsx
Writes shop/  — home, 13 range pages, 52 category pages, one page per product,
       search, basket, products.json, sitemap.xml and the illustration set.

Everything under shop/ except assets/ is generated: edit the spreadsheet or the
SHOP block below and re-run, never the output. Real photographs are the one
exception — see PHOTO_DIR.
"""
import html
import json
import os
import shutil

from shop_catalogue import load_catalogue, slugify
from shop_images import write_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'shop')
IMG_DIR = os.path.join(OUT, 'img')
PHOTO_DIR = os.path.join(IMG_DIR, 'photos')      # drop <product-code>.jpg here
PHOTO_EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.avif')

# ---------------------------------------------------------------------------
# The only hand-written facts on the site. Change them here, nowhere else.
# ---------------------------------------------------------------------------
SHOP = {
    'name': 'DampCheck Wales',
    'store': 'Trade Store',
    'tagline': 'Waterproofing, damp-proofing and structural repair products',
    'base': 'https://www.dampcheckwales.co.uk/shop',
    'email': 'sales@dampcheckwales.co.uk',
    'phone': '',                       # leave empty to hide the phone line
    'vat_rate': 0.20,
    'price_year': '2026',
    'price_note': 'Trade list prices for 2026, shown excluding VAT.',
    'parent': 'https://www.dampcheckwales.co.uk/',
}

VAT = SHOP['vat_rate']


def esc(text):
    return html.escape(str(text), quote=True)


def money(value):
    return '£' + format(value, ',.2f')


# ---------------------------------------------------------------------------
# chrome
# ---------------------------------------------------------------------------
LOGO = ('<svg viewBox="0 0 26 33" aria-hidden="true"><path fill="#CE1B22" d="M13 0C13 0 0 14.4 0 22.1'
        'A13 13 0 0 0 26 22.1C26 14.4 13 0 13 0Zm0 27.5a5.4 5.4 0 0 1-5.4-5.4h2.6a2.8 2.8 0 0 0 5.6 0'
        'h2.6a5.4 5.4 0 0 1-5.4 5.4Z"/></svg>')


def head(title, description, root, canonical, extra=''):
    return (
        '<!DOCTYPE html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n<meta name="description" content="%s">\n'
        '<link rel="canonical" href="%s">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="%s %s">\n'
        '<meta property="og:title" content="%s">\n'
        '<meta property="og:description" content="%s">\n'
        '<link rel="icon" href="%s/img/favicon.svg" type="image/svg+xml">\n'
        '<link rel="stylesheet" href="%s/assets/shop.css">\n%s</head>\n'
        % (esc(title), esc(description), esc(canonical), esc(SHOP['name']), esc(SHOP['store']),
           esc(title), esc(description), root, root, extra)
    )


def header(root, current_line=None, lines=()):
    nav = ''.join(
        '<a href="%s/category/%s.html"%s>%s</a>'
        % (root, line['slug'], ' aria-current="page"' if line['slug'] == current_line else '',
           esc(line['name']))
        for line in lines[:8])
    phone = ('<a href="tel:%s">%s</a>' % (SHOP['phone'].replace(' ', ''), esc(SHOP['phone']))
             if SHOP['phone'] else '')
    return (
        '<body data-root="%s">\n'
        '<div class="topbar"><div class="wrap">'
        '<span>%s</span>'
        '<span class="sep"></span>%s'
        '<a href="mailto:%s">%s</a>'
        '<a href="%s">DampCheck Wales damp guide</a>'
        '</div></div>\n'
        '<div class="masthead"><div class="wrap">'
        '<a class="brand" href="%s/">%s<span><b>%s</b><span>%s</span></span></a>'
        '<form class="searchbox" role="search" action="%s/search.html" method="get">'
        '<input id="q" name="q" type="search" placeholder="Search 593 products by name or code…" '
        'autocomplete="off" aria-label="Search products">'
        '<button type="submit">Search</button>'
        '<div class="suggest" id="suggest" hidden></div></form>'
        '<a class="cartbtn" href="%s/cart.html">Basket <span class="n" data-cart-count hidden>0</span></a>'
        '</div></div>\n'
        '<nav class="mainnav"><div class="wrap">%s<a href="%s/catalogue.html">All products</a></div></nav>\n'
        % (root, esc(SHOP['price_note']), phone, esc(SHOP['email']), esc(SHOP['email']),
           SHOP['parent'], root, LOGO, esc(SHOP['name']), esc(SHOP['store']), root, root, nav, root)
    )


def footer(root, lines):
    top = ''.join('<li><a href="%s/category/%s.html">%s</a></li>' % (root, line['slug'], esc(line['name']))
                  for line in lines[:6])
    return (
        '<footer class="site"><div class="wrap"><div class="fcols">'
        '<div><h4>%s %s</h4><p>%s. Prices are %s trade list, excluding VAT.</p>'
        '<p><a href="mailto:%s">%s</a></p></div>'
        '<div><h4>Ranges</h4><ul>%s</ul></div>'
        '<div><h4>Shop</h4><ul>'
        '<li><a href="%s/catalogue.html">Full catalogue</a></li>'
        '<li><a href="%s/search.html">Search</a></li>'
        '<li><a href="%s/cart.html">Your basket</a></li>'
        '<li><a href="%s/ordering.html">How ordering works</a></li></ul></div>'
        '<div><h4>Advice</h4><ul>'
        '<li><a href="%s">Damp and mould guide</a></li>'
        '<li><a href="%scy/">Fersiwn Gymraeg</a></li></ul></div>'
        '</div><div class="fbase">Product names, codes and prices are taken from the manufacturers\' '
        '%s price list. Trade marks belong to their owners.</div></div></footer>\n'
        '<script src="%s/assets/shop.js"></script>\n</body>\n</html>\n'
        % (esc(SHOP['name']), esc(SHOP['store']), esc(SHOP['tagline']), SHOP['price_year'],
           esc(SHOP['email']), esc(SHOP['email']), top, root, root, root, root,
           SHOP['parent'], SHOP['parent'], SHOP['price_year'], root)
    )


def crumbs(root, trail):
    parts = ['<a href="%s/">Home</a>' % root]
    for label, href in trail[:-1]:
        parts.append('<a href="%s">%s</a>' % (href, esc(label)))
    parts.append('<span aria-current="page">%s</span>' % esc(trail[-1][0]))
    return '<div class="wrap"><nav class="crumbs">%s</nav></div>' % '<span>›</span>'.join(parts)


# ---------------------------------------------------------------------------
# product card — the same markup shop.js builds for search results
# ---------------------------------------------------------------------------
def card(product, root):
    href = '%s/product/%s.html' % (root, product['slug'])
    if product['poa']:
        price = '<div class="poa">Price on application</div>'
    else:
        price = ('<div class="price">%s <small>excl VAT</small></div>'
                 '<div class="incl">%s incl VAT</div>'
                 % (money(product['price']), money(product['price'] * (1 + VAT))))
    return (
        '<article class="card" data-code="%s" data-name="%s" data-price="%s" data-poa="%s" '
        'data-brand="%s" data-uom="%s" data-img="%s" data-href="%s">'
        '<a class="shot" href="%s"><img src="%s/%s" alt="%s" loading="lazy" width="480" height="480">'
        '%s</a>'
        '<div class="body"><a class="name" href="%s">%s</a>'
        '<div class="meta">%s · %s</div>%s'
        '<div class="buyrow"><div class="qty">'
        '<button type="button" data-step="-" aria-label="Fewer">−</button>'
        '<input type="number" min="1" value="1" aria-label="Quantity">'
        '<button type="button" data-step="+" aria-label="More">+</button></div>'
        '<button type="button" class="add">Add to cart</button></div></div></article>'
        % (esc(product['code']), esc(product['name']), product['price'],
           1 if product['poa'] else 0, esc(product['brand']), esc(product['uom']),
           product['img'], href, href, root, product['img'], esc(product['name']),
           '<span class="flag">%s</span>' % esc(product['brand'])
           if product['brand'] != 'Other Manufacturers' else '',
           href, esc(product['name']), esc(product['code']), esc(product['pack']), price)
    )


def sidebar(root, products, lines, current_line=None, current_group=None):
    priced = [p['price'] for p in products if not p['poa']]
    low = int(min(priced)) if priced else 0
    high = int(max(priced)) + 1 if priced else 100

    brands = {}
    for product in products:
        brands[product['brand']] = brands.get(product['brand'], 0) + 1

    tree = []
    for line in lines:
        open_line = line['slug'] == current_line
        subs = ''.join(
            '<li><a href="%s/category/%s.html"%s>%s <span class="n">(%d)</span></a></li>'
            % (root, group['page'], ' aria-current="page"' if group['slug'] == current_group else '',
               esc(group['name']), group['count'])
            for group in line['groups']) if open_line else ''
        tree.append(
            '<li><a href="%s/category/%s.html"%s>%s <span class="n">(%d)</span></a>%s</li>'
            % (root, line['slug'], ' aria-current="page"' if open_line else '',
               esc(line['name']), line['count'],
               '<ul class="sub">%s</ul>' % subs if subs else ''))

    brand_rows = ''.join(
        '<label class="check"><input type="checkbox" data-brand="%s">%s<span class="n">%d</span></label>'
        % (esc(brand), esc(brand), count)
        for brand, count in sorted(brands.items(), key=lambda b: (-b[1], b[0])))

    return (
        '<aside class="side">'
        '<details class="panel" open><summary>Price range</summary><div class="body">'
        '<div class="range"><span>Min<b id="price-min-out">%s</b></span>'
        '<span style="text-align:right">Max<b id="price-max-out">%s</b></span></div>'
        '<div class="sliders"><div class="track"></div><div class="fill"></div>'
        '<input id="price-min" type="range" min="%d" max="%d" value="%d" aria-label="Minimum price">'
        '<input id="price-max" type="range" min="%d" max="%d" value="%d" aria-label="Maximum price">'
        '</div></div></details>'
        '<details class="panel" open><summary>Manufacturers</summary>'
        '<div class="body">%s</div></details>'
        '<details class="panel" open><summary>Categories</summary>'
        '<ul class="cats">%s</ul></details>'
        '</aside>'
        % (money(low), money(high), low, high, low, low, high, high, brand_rows, ''.join(tree))
    )


TOOLBAR = (
    '<div class="toolbar">'
    '<label for="per-page">Display</label>'
    '<select id="per-page"><option>25</option><option>50</option><option>100</option></select>'
    '<span>per page</span>'
    '<span class="grow"></span>'
    '<span data-count></span>'
    '<label for="sort-by">Sort by</label>'
    '<select id="sort-by">'
    '<option value="position">Position</option>'
    '<option value="name">Name A–Z</option>'
    '<option value="name-desc">Name Z–A</option>'
    '<option value="price">Price low to high</option>'
    '<option value="price-desc">Price high to low</option></select>'
    '<div class="view" data-view>'
    '<button type="button" data-set="grid" aria-pressed="true" aria-label="Grid view">'
    '<svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">'
    '<rect width="6" height="6"/><rect x="9" width="6" height="6"/>'
    '<rect y="9" width="6" height="6"/><rect x="9" y="9" width="6" height="6"/></svg></button>'
    '<button type="button" data-set="list" aria-pressed="false" aria-label="List view">'
    '<svg width="15" height="15" viewBox="0 0 15 15" fill="currentColor">'
    '<rect width="15" height="3"/><rect y="6" width="15" height="3"/>'
    '<rect y="12" width="15" height="3"/></svg></button></div></div>'
)


def listing(root, products):
    return ('%s<div class="grid" data-listing>%s</div>'
            '<div class="empty" data-empty hidden>No products match those filters. '
            'Widen the price range or clear a manufacturer.</div>'
            '<div class="pager" data-pager></div>'
            % (TOOLBAR, ''.join(card(p, root) for p in products)))


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def write(path, markup):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as handle:
        handle.write(markup)


def page_home(catalogue):
    lines, products = catalogue['lines'], catalogue['products']
    root = '.'
    tiles = ''.join(
        '<a class="tile" href="./category/%s.html"><img src="./%s" alt="" loading="lazy">'
        '<span><b>%s</b><span>%d product%s</span></span></a>'
        % (line['slug'], line['thumb'], esc(line['name']), line['count'],
           '' if line['count'] == 1 else 's')
        for line in lines)

    groups = sorted((g for line in lines for g in line['groups']), key=lambda g: -g['count'])[:12]
    popular = ''.join(
        '<a class="chip" href="./category/%s.html">%s <span class="muted">%d</span></a>'
        % (group['page'], esc(group['name']), group['count']) for group in groups)

    brands = ''.join('<a class="chip" href="./catalogue.html?brand=%s">%s <span class="muted">%d</span></a>'
                     % (slugify(brand), esc(brand), count) for brand, count in catalogue['brands'])

    featured = ''.join(card(p, root) for p in pick_featured(products))

    return (
        head('%s %s | %s' % (SHOP['name'], SHOP['store'], SHOP['tagline']),
             '%d waterproofing, damp-proofing and structural repair products at %s trade list prices. '
             'Cavity drain membranes, DPC injection, pumps, helical ties and tanking.'
             % (len(products), SHOP['price_year']),
             root, SHOP['base'] + '/')
        + header(root, None, lines)
        + '<main>'
        '<section class="hero"><div class="wrap">'
        '<h1>%s</h1>'
        '<p>%d lines from Wykamol, Mapei, Triton, Sika, Thor Helical and Protimeter — '
        'cavity drain systems, tanking slurries, DPC injection creams, sump pumps, crack '
        'stitching and survey kit. %s</p>'
        '<div class="btnrow"><a class="btn" href="./catalogue.html">Browse the catalogue</a>'
        '<a class="btn ghost" href="./ordering.html">How ordering works</a></div>'
        '</div></section>'
        '<section class="section"><div class="wrap"><div class="head"><h2>Shop by range</h2></div>'
        '<div class="tiles">%s</div></div></section>'
        '<section class="section" style="padding-top:0"><div class="wrap">'
        '<div class="head"><h2>Popular categories</h2>'
        '<a href="./catalogue.html">All %d products →</a></div>'
        '<div class="strip">%s</div></div></section>'
        '<section class="section" style="padding-top:0"><div class="wrap">'
        '<div class="head"><h2>Trade favourites</h2></div>'
        '<div class="grid">%s</div></div></section>'
        '<section class="section" style="padding-top:0"><div class="wrap">'
        '<div class="head"><h2>Manufacturers</h2></div><div class="strip">%s</div></div></section>'
        '</main>'
        % (esc(SHOP['tagline']), len(products), esc(SHOP['price_note']), tiles,
           len(products), popular, featured, brands)
        + footer(root, lines)
    )


def pick_featured(products):
    """One recognisable line from each of the biggest categories, priced, in stock order."""
    wanted = ['cavity-drain-systems', 'chemical-barrier-injection', 'cavity-drain-pumps',
              'cement-based-coatings', 'helical-steel-wall-tie-and-restraints',
              'liquid-elastic-membranes', 'anti-condensation-coatings', 'cleaning-mould-cleaner',
              'technical-items-and-equipment', 'water-repellents']
    out = []
    for slug in wanted:
        for product in products:
            if product['group_slug'] == slug and not product['poa'] and product['price'] > 20:
                out.append(product)
                break
    return out[:10]


def page_line(catalogue, line):
    root = '..'
    products = [p for p in catalogue['products'] if p['line_slug'] == line['slug']]
    groups = ''.join(
        '<a class="chip" href="./%s.html">%s <span class="muted">%d</span></a>'
        % (group['page'], esc(group['name']), group['count']) for group in line['groups'])
    return (
        head('%s | %s %s' % (line['name'], SHOP['name'], SHOP['store']),
             '%d %s products at %s trade list prices, excluding VAT.'
             % (line['count'], line['name'].lower(), SHOP['price_year']),
             root, '%s/category/%s.html' % (SHOP['base'], line['slug']))
        + header(root, line['slug'], catalogue['lines'])
        + '<main>' + crumbs(root, [(line['name'], '')])
        + '<div class="wrap"><div class="cols">'
        + sidebar(root, products, catalogue['lines'], line['slug'])
        + '<div><h1>%s</h1><p class="muted">%d products across %d categories.</p>'
          '%s<div style="height:14px"></div>%s</div>'
          % (esc(line['name']), line['count'], len(line['groups']),
             '<div class="strip">%s</div>' % groups if len(line['groups']) > 1 else '',
             listing(root, products))
        + '</div></div></main>' + footer(root, catalogue['lines'])
    )


def page_group(catalogue, line, group):
    root = '..'
    products = [p for p in catalogue['products'] if p['group_slug'] == group['slug']
                and p['line_slug'] == line['slug']]
    return (
        head('%s | %s %s' % (group['name'], SHOP['name'], SHOP['store']),
             '%d %s products — %s trade list prices, excluding VAT. %s.'
             % (len(products), group['name'].lower(), SHOP['price_year'],
                ', '.join(sorted({p['brand'] for p in products}))),
             root, '%s/category/%s.html' % (SHOP['base'], group['page']))
        + header(root, line['slug'], catalogue['lines'])
        + '<main>' + crumbs(root, [(line['name'], './%s.html' % line['slug']), (group['name'], '')])
        + '<div class="wrap"><div class="cols">'
        + sidebar(root, products, catalogue['lines'], line['slug'], group['slug'])
        + '<div><h1>%s</h1><p class="muted">%d products in %s.</p>%s</div>'
          % (esc(group['name']), len(products),
             '<a href="./%s.html">%s</a>' % (line['slug'], esc(line['name'])),
             listing(root, products))
        + '</div></div></main>' + footer(root, catalogue['lines'])
    )


def page_catalogue(catalogue):
    root = '.'
    products = catalogue['products']
    return (
        head('Full catalogue | %s %s' % (SHOP['name'], SHOP['store']),
             'Every one of the %d products in the %s waterproofing and damp-proofing price list.'
             % (len(products), SHOP['price_year']),
             root, SHOP['base'] + '/catalogue.html')
        + header(root, None, catalogue['lines'])
        + '<main>' + crumbs(root, [('Full catalogue', '')])
        + '<div class="wrap"><div class="cols">'
        + sidebar(root, products, catalogue['lines'])
        + '<div><h1>Full catalogue</h1><p class="muted">All %d products, %s.</p>%s</div>'
          % (len(products), SHOP['price_note'].lower().rstrip('.'), listing(root, products))
        + '</div></div></main>' + footer(root, catalogue['lines'])
    )


def page_product(catalogue, product, related):
    root = '..'
    price_block = (
        '<div class="poa" style="font-size:24px;font-weight:800;color:#A15C00">Price on application</div>'
        '<p class="small muted">This line is quoted per order. Add it to your basket and we will '
        'price it with the rest of your enquiry.</p>'
        if product['poa'] else
        '<div class="big">%s <small>excl VAT</small></div>'
        '<div class="muted small">%s incl VAT at %d%%</div>'
        % (money(product['price']), money(product['price'] * (1 + VAT)), VAT * 100))

    changed = ''
    if product['price_2025'] and not product['poa']:
        delta = product['price'] - product['price_2025']
        if abs(delta) >= 0.01:
            direction = 'up' if delta > 0 else 'down'
            changed = ('<tr><th>2025 list price</th><td>%s <span class="muted">(%s %s in %s)</span></td></tr>'
                       % (money(product['price_2025']), direction, money(abs(delta)), SHOP['price_year']))

    schema = {
        '@context': 'https://schema.org', '@type': 'Product',
        'name': product['name'], 'sku': product['code'], 'brand': {'@type': 'Brand', 'name': product['brand']},
        'category': '%s > %s' % (product['line'], product['group']),
        'image': '%s/%s' % (SHOP['base'], product['img']),
        'url': '%s/product/%s.html' % (SHOP['base'], product['slug']),
    }
    if not product['poa']:
        schema['offers'] = {
            '@type': 'Offer', 'price': '%.2f' % product['price'], 'priceCurrency': 'GBP',
            'availability': 'https://schema.org/InStock',
            'url': '%s/product/%s.html' % (SHOP['base'], product['slug']),
        }

    return (
        head('%s — %s | %s %s' % (product['name'], product['code'], SHOP['name'], SHOP['store']),
             '%s (%s). %s. %s trade list price, excluding VAT.'
             % (product['name'], product['code'], product['pack'], SHOP['price_year']),
             root, '%s/product/%s.html' % (SHOP['base'], product['slug']),
             '<script type="application/ld+json">%s</script>\n' % json.dumps(schema))
        + header(root, product['line_slug'], catalogue['lines'])
        + '<main>'
        + crumbs(root, [(product['line'], '%s/category/%s.html' % (root, product['line_slug'])),
                        (product['group'], '%s/category/%s.html' % (root, product['group_page'])),
                        (product['name'], '')])
        + '<div class="wrap" style="padding-bottom:56px">'
        '<div class="detail" data-code="%s" data-name="%s" data-price="%s" data-poa="%s" '
        'data-uom="%s" data-img="%s" data-href="%s/product/%s.html">'
        '<div class="shot"><img src="%s/%s" alt="%s" width="480" height="480"></div>'
        '<div><h1>%s</h1><div class="sku">Code %s · %s</div>'
        '<div class="pricebox">%s<div class="buyrow"><div class="qty">'
        '<button type="button" data-step="-" aria-label="Fewer">−</button>'
        '<input type="number" min="1" value="1" aria-label="Quantity">'
        '<button type="button" data-step="+" aria-label="More">+</button></div>'
        '<button type="button" class="add">Add to cart</button></div></div>'
        '<table class="specs"><tbody>'
        '<tr><th>Product code</th><td>%s</td></tr>'
        '<tr><th>Manufacturer</th><td>%s</td></tr>'
        '<tr><th>Pack size</th><td>%s</td></tr>'
        '<tr><th>Sold by</th><td>%s</td></tr>'
        '<tr><th>Category</th><td><a href="%s/category/%s.html">%s</a></td></tr>'
        '<tr><th>Range</th><td><a href="%s/category/%s.html">%s</a></td></tr>'
        '%s</tbody></table>'
        '<p class="notice">Ordering is by enquiry: your basket becomes a priced order request, '
        'and we confirm stock, carriage and lead time before anything is charged.</p>'
        '</div></div>'
        % (esc(product['code']), esc(product['name']), product['price'],
           1 if product['poa'] else 0, esc(product['uom']), product['img'], root, product['slug'],
           root, product['img'], esc(product['name']), esc(product['name']),
           esc(product['code']), esc(product['pack']), price_block,
           esc(product['code']), esc(product['brand']), esc(product['pack']), esc(product['uom']),
           root, product['group_page'], esc(product['group']),
           root, product['line_slug'], esc(product['line']), changed)
        + ('<section class="section"><div class="head"><h2>More from %s</h2>'
           '<a href="%s/category/%s.html">See all %s →</a></div><div class="grid">%s</div></section>'
           % (esc(product['group']), root, product['group_page'], esc(product['group']),
              ''.join(card(p, root) for p in related)) if related else '')
        + '</div></main>' + footer(root, catalogue['lines'])
    )


def page_search(catalogue):
    root = '.'
    return (
        head('Search | %s %s' % (SHOP['name'], SHOP['store']),
             'Search %d waterproofing and damp-proofing products by name or product code.'
             % len(catalogue['products']),
             root, SHOP['base'] + '/search.html',
             '<meta name="robots" content="noindex, follow">\n')
        + header(root, None, catalogue['lines'])
        + '<main>' + crumbs(root, [('Search', '')])
        + '<div class="wrap" style="padding:18px 0 56px">'
        '<h1 data-results-head>Search the catalogue</h1>'
        '<div class="grid" data-results></div>'
        '<div class="empty" data-no-results hidden>Nothing matched. Try a product code '
        '(<code>WYK-CM8</code>), a range (<code>Mapelastic</code>) or a category '
        '(<code>cavity drain</code>).</div>'
        '</div></main>' + footer(root, catalogue['lines'])
    )


def page_cart(catalogue):
    root = '.'
    return (
        head('Your basket | %s %s' % (SHOP['name'], SHOP['store']),
             'Your basket and order enquiry.', root, SHOP['base'] + '/cart.html',
             '<meta name="robots" content="noindex, nofollow">\n')
        + header(root, None, catalogue['lines'])
        + '<main>' + crumbs(root, [('Basket', '')])
        + '<div class="wrap" style="padding:18px 0 56px"><h1>Your basket</h1>'
        '<div class="empty" data-basket-empty hidden>Your basket is empty. '
        '<a href="./catalogue.html">Browse the catalogue</a>.</div>'
        '<div class="cartgrid">'
        '<div class="lines" data-basket></div>'
        '<div class="totals" data-summary hidden>'
        '<dl><dt>Goods (excl VAT)</dt><dd data-net>£0.00</dd>'
        '<dt>VAT at %d%%</dt><dd data-vat>£0.00</dd>'
        '<dt>Delivery</dt><dd>quoted</dd></dl>'
        '<dl class="grand"><dt>Total</dt><dd data-gross>£0.00</dd></dl>'
        '<p class="small muted" data-poa-note hidden>Some lines are priced on application and are '
        'not in the total above.</p>'
        '<a class="btn" data-mailto data-email="%s" href="mailto:%s">Email this order enquiry</a>'
        '<p class="small muted" style="margin-top:12px">No payment is taken on this site. '
        'We reply with stock, carriage and a confirmed price.</p>'
        '<details><summary class="small">Copy the order as text</summary>'
        '<textarea class="order" readonly aria-label="Order as text"></textarea></details>'
        '<button class="rm small" data-clear type="button" style="margin-top:10px;border:0;'
        'background:none;text-decoration:underline;cursor:pointer;color:#5C6874">Empty the basket</button>'
        '</div></div></div></main>'
        % (VAT * 100, esc(SHOP['email']), esc(SHOP['email']))
        + footer(root, catalogue['lines'])
    )


def page_ordering(catalogue):
    root = '.'
    return (
        head('How ordering works | %s %s' % (SHOP['name'], SHOP['store']),
             'How prices, VAT, the basket and order enquiries work on the %s trade store.' % SHOP['name'],
             root, SHOP['base'] + '/ordering.html')
        + header(root, None, catalogue['lines'])
        + '<main>' + crumbs(root, [('How ordering works', '')])
        + '<div class="wrap" style="padding:18px 0 56px;max-width:760px">'
        '<h1>How ordering works</h1>'
        '<h2>Prices</h2>'
        '<p>Every price on this site is the manufacturer\'s %s trade list price, shown excluding '
        'VAT, with the VAT-inclusive figure underneath at %d%%. A handful of lines are quoted per '
        'order and show <em>price on application</em>.</p>'
        '<h2>The basket</h2>'
        '<p>Your basket is held in your own browser — nothing is sent anywhere until you choose to '
        'send it. On the basket page it becomes an order enquiry you can email in one click, or '
        'copy as text.</p>'
        '<h2>Payment</h2>'
        '<p>No card payment is taken on this site. We reply to an enquiry with stock, carriage and '
        'a confirmed price, and invoice against a trade account or a proforma.</p>'
        '<h2>Product images</h2>'
        '<p>Illustrations show the pack format each product ships in — a 20&nbsp;kg bucket, a '
        'dimpled membrane roll, a helical bar. Where a photograph exists it is used instead. '
        'If an illustration does not match what you expect, check the product code before ordering.</p>'
        '<h2>Getting in touch</h2>'
        '<p><a href="mailto:%s">%s</a>%s</p>'
        '</div></main>'
        % (SHOP['price_year'], VAT * 100, esc(SHOP['email']), esc(SHOP['email']),
           ' · ' + esc(SHOP['phone']) if SHOP['phone'] else '')
        + footer(root, catalogue['lines'])
    )


def page_404(catalogue):
    root = '.'
    return (
        head('Page not found | %s %s' % (SHOP['name'], SHOP['store']),
             'That page does not exist.', root, SHOP['base'] + '/404.html',
             '<meta name="robots" content="noindex, nofollow">\n')
        + header(root, None, catalogue['lines'])
        + '<main><div class="wrap" style="padding:56px 0"><h1>That page has moved or never existed</h1>'
        '<p class="muted">Search by product code above, or start from the '
        '<a href="./catalogue.html">full catalogue</a>.</p></div></main>'
        + footer(root, catalogue['lines'])
    )


# ---------------------------------------------------------------------------
def find_photo(code):
    for ext in PHOTO_EXTS:
        name = code + ext
        if os.path.exists(os.path.join(PHOTO_DIR, name)):
            return 'img/photos/' + name
    return None


def build():
    catalogue = load_catalogue()
    products, lines = catalogue['products'], catalogue['lines']

    # ---- images ----
    drawn = write_all(IMG_DIR, ((p['kind'], p['brand']) for p in products))
    photos = 0
    for product in products:
        photo = find_photo(product['code'])
        if photo:
            product['img'] = photo
            photos += 1
        else:
            product['img'] = 'img/' + drawn[(product['kind'], product['brand'])]

    # ---- page names: a group keeps its own slug unless two ranges share it ----
    seen = {}
    for line in lines:
        for group in line['groups']:
            seen.setdefault(group['slug'], []).append(group)
    for slug, sharers in seen.items():
        for group in sharers:
            group['page'] = slug if len(sharers) == 1 else '%s-%s' % (group['line_slug'], slug)
    page_of = {(g['line_slug'], g['slug']): g['page'] for line in lines for g in line['groups']}
    for product in products:
        product['group_page'] = page_of[(product['line_slug'], product['group_slug'])]

    for line in lines:
        # the tile shows whatever this range mostly ships as
        kinds = {}
        for product in products:
            if product['line_slug'] == line['slug']:
                kinds[product['kind']] = kinds.get(product['kind'], 0) + 1
        common = max(kinds, key=kinds.get)
        line['thumb'] = next(p['img'] for p in products
                             if p['line_slug'] == line['slug'] and p['kind'] == common)

    # ---- pages ----
    for path in ('category', 'product'):
        shutil.rmtree(os.path.join(OUT, path), ignore_errors=True)

    write('index.html', page_home(catalogue))
    write('catalogue.html', page_catalogue(catalogue))
    write('search.html', page_search(catalogue))
    write('cart.html', page_cart(catalogue))
    write('ordering.html', page_ordering(catalogue))
    write('404.html', page_404(catalogue))

    for line in lines:
        write('category/%s.html' % line['slug'], page_line(catalogue, line))
        for group in line['groups']:
            write('category/%s.html' % group['page'], page_group(catalogue, line, group))

    by_group = {}
    for product in products:
        by_group.setdefault(product['group_page'], []).append(product)
    for product in products:
        siblings = [p for p in by_group[product['group_page']] if p['code'] != product['code']]
        # things that look and work like this one first, then the rest of the category
        siblings.sort(key=lambda p: (p['kind'] != product['kind'], p['brand'] != product['brand']))
        write('product/%s.html' % product['slug'], page_product(catalogue, product, siblings[:5]))

    # ---- data for search ----
    with open(os.path.join(OUT, 'products.json'), 'w', encoding='utf-8') as handle:
        json.dump([{k: p[k] for k in ('code', 'slug', 'name', 'price', 'poa', 'uom', 'pack',
                                      'img', 'brand', 'group', 'line')} for p in products],
                  handle, separators=(',', ':'))

    # ---- sitemap ----
    urls = ['%s/' % SHOP['base'], '%s/catalogue.html' % SHOP['base'],
            '%s/ordering.html' % SHOP['base']]
    urls += ['%s/category/%s.html' % (SHOP['base'], line['slug']) for line in lines]
    urls += ['%s/category/%s.html' % (SHOP['base'], group['page'])
             for line in lines for group in line['groups']]
    urls += ['%s/product/%s.html' % (SHOP['base'], p['slug']) for p in products]
    with open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8') as handle:
        handle.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in urls:
            handle.write('  <url><loc>%s</loc></url>\n' % html.escape(url))
        handle.write('</urlset>\n')

    print('%d products · %d ranges · %d categories · %d pages'
          % (len(products), len(lines), sum(len(l['groups']) for l in lines), len(urls) + 3))
    print('%d drawn illustrations, %d photographs' % (len(drawn), photos))


if __name__ == '__main__':
    build()
