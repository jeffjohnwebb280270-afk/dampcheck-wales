# Trade store — `shop/`

A static shop for the 2026 waterproofing price list: 593 products, 13 ranges,
53 categories, a page each, a basket, and search. No server, no database, no
build tooling beyond Python and `openpyxl` — it deploys as plain files next to
the rest of the site.

    pip install openpyxl
    python3 build_shop.py

## Where things come from

| | |
|---|---|
| `data/waterproofing-price-list-2026.xlsx` | the price list, unedited, as supplied |
| `shop_catalogue.py` | reads it: names, prices, pack sizes, manufacturers, categories |
| `shop_images.py` | draws the product illustrations |
| `build_shop.py` | writes every page, `products.json` and `sitemap.xml` |
| `shop/assets/` | the only hand-written files under `shop/` — CSS and JS |

Everything else under `shop/` is generated. Never edit it: change the
spreadsheet or the `SHOP` block at the top of `build_shop.py` and re-run.

To publish a new price list, drop the new spreadsheet in over the old one
(keep the filename, or point `XLSX` in `shop_catalogue.py` at it) and rebuild.
Products that leave the list lose their pages; new ones get theirs. Only rows
marked `Active` are published.

## Before it goes live

The `SHOP` dictionary at the top of `build_shop.py` holds every hand-written
fact on the site. Two of them are placeholders:

- `email` — `sales@dampcheckwales.co.uk`. The basket's "email this order
  enquiry" button sends here.
- `phone` — empty, so the phone line is hidden. Fill it in and it appears in
  the top bar and on the ordering page.

Nothing else needs touching. Prices, names, codes, pack sizes and categories
all come from the spreadsheet.

## Product photographs

Every product is drawn rather than photographed — a 20 kg bucket, a dimpled
membrane roll, a helical bar, tinted by manufacturer. The illustrations are
generated from the product's unit and description, so they always match the
pack format, and 56 SVGs cover all 593 products.

A real photograph always wins. Drop it in `shop/img/photos/` named after the
product code and rebuild:

    shop/img/photos/WYK-CM202X10.jpg     ->  used for WYK-CM202X10
    shop/img/photos/WYK-WGCHANNEL2M.png  ->  used for WYK-WGCHANNEL2M

`.jpg`, `.jpeg`, `.png`, `.webp` and `.avif` are all picked up. Square images
around 800×800 sit best in the card grid. The build prints how many photographs
it found. There is no bulk source for these: manufacturer images are theirs,
so use your own photographs or ones you have permission to use.

## How the shop behaves

- **Works without JavaScript.** Every listing page ships its products as real
  HTML. JavaScript only adds filtering, sorting, paging, the basket and search.
- **The basket lives in the customer's browser** (`localStorage`), and becomes
  an order enquiry — an email or a block of text. No payment is taken, and
  nothing is sent anywhere until the customer presses the button.
- **Prices are 2026 trade list, excluding VAT**, with the VAT-inclusive figure
  under each one. 38 lines have no list price and show *price on application*;
  they are kept out of basket totals and are never filtered out by price.
- **Search** covers name, product code, category and manufacturer, from
  `products.json` (180 KB). The header box suggests as you type.

## Deploying

Upload `shop/` alongside `index.html`. It expects to live at `/shop/` — that
path is in `SHOP['base']`, which sets the canonical URLs and the sitemap, so
change it there if it moves. `shop/sitemap.xml` lists all 665 pages and is
already referenced from `robots.txt`.

`shop/catalogue.html` carries all 593 products in one page (about 660 KB
uncompressed, far less over gzip). Serve it compressed, as any host does by
default, or link customers to the category pages instead.
