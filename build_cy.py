#!/usr/bin/env python3
"""
Generate the Welsh page (cy/index.html) from the English one.

The Welsh copy lives in i18n/cy.json as a plain English->Welsh map, so it can be
corrected by a translator who has never seen the code: edit the JSON, re-run this,
and the page is rebuilt. Anything still missing from the map is reported rather
than silently left in English.

    python3 build_cy.py
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'index.html')
OUT_DIR = os.path.join(HERE, 'cy')
MAP = os.path.join(HERE, 'i18n', 'cy.json')

EN_URL = 'https://www.dampcheckwales.co.uk/'
CY_URL = 'https://www.dampcheckwales.co.uk/cy/'

tr = json.load(open(MAP, encoding='utf-8'))
html = open(SRC, encoding='utf-8').read()

missing = []
PROSE_MIN_WORDS = 3

# ---- whole-block overrides ------------------------------------------------
# Some English fragments split a word across a <b> boundary in a way that only
# works in English word order — e.g. "Use the <b>first</b> date..." — because
# Welsh puts the adjective after the noun ("y dyddiad cyntaf", not "cyntaf y
# dyddiad"). Translating node-by-node there would emit correct words in the
# wrong order. These are matched and swapped in as raw HTML before the normal
# per-node pass runs, via a placeholder so they're not re-scanned afterwards.
BLOCK_OVERRIDES = [
    (
        'Use the <b>first</b> date you told them, even if it was a phone call or a text. If you have reported it several times, we will get to that in the letter.',
        "Defnyddiwch y dyddiad <b>cyntaf</b> y gwnaethoch chi roi gwybod iddyn nhw, hyd yn oed os oedd yn alwad ffôn neu'n neges destun. Os ydych chi wedi rhoi gwybod amdano sawl gwaith, byddwn yn mynd i'r afael â hynny yn y llythyr."
    ),
    (
        'If you rent from a council or housing association, exhaust their formal complaints process and then go to the <b>Public Services Ombudsman for Wales</b> — free, and independent. For private landlords, a disrepair claim in the county court can order the work done and award compensation. Get free advice from <b>Shelter Cymru</b> or <b>Citizens Advice</b> before starting anything.',
        "Os ydych yn rhentu gan gyngor neu gymdeithas dai, dihysbyddwch eu proses gwyno ffurfiol ac yna ewch i <b>Ombwdsmon Gwasanaethau Cyhoeddus Cymru</b> — am ddim, ac yn annibynnol. Ar gyfer landlordiaid preifat, gall hawliad adfeiliad yn y llys sirol orchymyn y gwaith a wnaed a dyfarnu iawndal. Mynnwch gyngor am ddim gan <b>Shelter Cymru</b> neu <b>Cyngor ar Bopeth</b> cyn dechrau unrhyw beth."
    ),
]

def is_prose(key):
    """Prose, not a code fragment. Guards the script-string pass."""
    if len(key.split()) < PROSE_MIN_WORDS:
        return False
    # An HTML entity is prose, not code, but &rsquo; carries a semicolon and
    # &amp; an ampersand — enough for the code test below to throw out a whole
    # sentence for containing a typographic apostrophe. Test without them.
    probe = re.sub(r'&[a-zA-Z]+;|&#\d+;', '', key)
    if re.search(r'[{}();=<>]|=>|\bfunction\b|\bconst\b|classList|querySelector', probe):
        return False
    return bool(re.match(r"^[A-Z\u00c0-\u017f\"\u2018\u201c]", key.strip()))

def look(s, prose_only=False):
    """Translate a whitespace-normalised string, recording anything unmapped."""
    key = re.sub(r'\s+', ' ', s).strip()
    if not key or not re.search(r'[A-Za-z]{3}', key) or '\x00BLOCK' in key:
        return None
    if prose_only and not is_prose(key):
        return None
    if key in tr and tr[key].strip():
        return tr[key]
    missing.append(key)
    return None

# ---- split the document so we only translate prose, never markup or code ----
body_at = html.index('<body>')
head, body = html[:body_at], html[body_at:]
js_m = re.search(r'<script>([\s\S]*)</script>', body)
static, js, tail = body[:js_m.start()], js_m.group(1), body[js_m.end():]

# ---- 0. protect whole-block overrides from the per-node pass ------------
block_map = {}
for i, (en_html, cy_html) in enumerate(BLOCK_OVERRIDES):
    token = f'\x00BLOCK{i}\x00'
    if en_html in static:
        static = static.replace(en_html, token, 1)
        block_map[token] = cy_html
    else:
        print(f"WARNING: block override {i} not found in source HTML — skipped")

# ---- 1. text nodes -------------------------------------------------------
def sub_node(m):
    lead, txt, trail = m.group(1), m.group(2), m.group(3)
    t = look(txt)
    return f'>{lead}{t}{trail}<' if t else m.group(0)
static = re.sub(r'>(\s*)([^<>]+?)(\s*)<', sub_node, static)

# ---- 2. translatable attributes -----------------------------------------
def sub_attr(m):
    t = look(m.group(2))
    return f'{m.group(1)}="{t}"' if t else m.group(0)
static = re.sub(r'(placeholder|aria-label|title|alt)="([^"]+)"', sub_attr, static)

# ---- 3. strings inside the script ----------------------------------------
# Three things this pass has to get right, each of which it previously did not:
#
#  a) A quoted literal cannot contain a raw newline. The old pattern allowed
#     one, so a run like  ...getElementById('x').innerHTML = `...it's...`
#     matched as a single 640-character "string" spanning ten lines, swallowing
#     every real string inside it. Anchoring on \n fixes that.
#  b) Template literals and double-quoted strings were never scanned at all.
#  c) Most UI text is a template literal wrapping markup, so the string as a
#     whole is not prose. Translating it wholesale is wrong; translating the
#     TEXT NODES inside it is exactly right, and is the same thing pass 1 does
#     to the static HTML.

JS_LITERAL = re.compile(
    r"'(?:[^'\\\n]|\\.)*'"      # single-quoted
    r'|"(?:[^"\\\n]|\\.)*"'     # double-quoted
    r'|`(?:[^`\\]|\\.)*`',       # template literal — may span lines
    re.S)

TAGGISH = re.compile(r'<[a-zA-Z/!]')

def esc_for(quote, t):
    """Escape a Welsh string for the quote style it is going back into."""
    t = t.replace('\\', '\\\\')
    if quote == "'":
        return t.replace("'", "\\'")
    if quote == '"':
        return t.replace('"', '\\"')
    return t.replace('`', '\\`').replace('${', '\\${')

def look_text(s):
    """Translate a run of user-facing text taken from inside a JS literal."""
    key = re.sub(r'\s+', ' ', s).strip()
    if not key or not re.search(r'[A-Za-z]{2}', key) or '\x00BLOCK' in key:
        return None
    if key in tr and tr[key].strip():
        return tr[key]
    # Record it only if it reads as something a person would see, so the
    # "still English" count means what it says instead of listing code.
    words = key.split()
    looks_like_ui = re.match(r"^[A-Z\u00c0-\u017f\u2018\u201c]", key) and (
        len(words) >= 2
        # a lone capitalised word is still UI text when it is purely alphabetic
        # ('Copied', 'Reported') — which also excludes fragments like T00:00:00
        or (len(key) >= 4 and re.fullmatch(r"[A-Za-z\u00c0-\u017f'\u2019-]+", key))
    )
    if looks_like_ui:
        missing.append(key)
    return None

def sub_js(m):
    lit = m.group(0)
    quote, raw = lit[0], lit[1:-1]

    if TAGGISH.search(raw):
        def node(nm):
            lead, txt, trail = nm.group(1), nm.group(2), nm.group(3)
            # Never translate across an interpolation: the English either side
            # of ${...} is half a sentence, and the key would not be stable.
            if '${' in txt:
                return nm.group(0)
            t = look_text(txt)
            return f'>{lead}{esc_for(quote, t)}{trail}<' if t else nm.group(0)
        return quote + re.sub(r'>(\s*)([^<>]+?)(\s*)<', node, raw) + quote

    if '${' in raw:
        return lit
    # An explicit entry in cy.json is a deliberate instruction to translate
    # that exact string, so honour it whatever its length — short UI labels
    # like 'Copy letter' and 'Copied' live in button-state assignments and
    # would otherwise never qualify as prose.
    key = re.sub(r'\s+', ' ', raw).strip()
    if key in tr and tr[key].strip():
        return f'{quote}{esc_for(quote, tr[key])}{quote}'
    if len(raw) < 15:
        look_text(raw)          # not translatable here, but still report it
        return lit
    t = look(raw, prose_only=True)
    return f'{quote}{esc_for(quote, t)}{quote}' if t else lit

js = JS_LITERAL.sub(sub_js, js)

# ---- 4. head: lang, canonical, hreflang, title, description --------------
head = head.replace('<html lang="en-GB">', '<html lang="cy">')
for tag, pat in (('title', r'<title>([\s\S]*?)</title>'),):
    m = re.search(pat, head)
    t = look(m.group(1))
    if t: head = head.replace(m.group(0), f'<{tag}>{t}</{tag}>')
for attr in ('name="description"', 'property="og:title"',
             'property="og:description"', 'name="twitter:title"',
             'name="twitter:description"'):
    m = re.search(re.escape(attr) + r' content="([^"]*)"', head)
    if m:
        t = look(m.group(1))
        if t: head = head.replace(m.group(0), f'{attr} content="{t}"')
# Only the canonical link and OG/Twitter url meta point at "this page" and
# need to flip to the Welsh URL. The hreflang alternates must NOT be touched —
# both pages declare the identical en-GB/cy/x-default trio, each pointing at
# the real URL for that language, so Google can pair them up.
head = head.replace(f'rel="canonical" href="{EN_URL}"', f'rel="canonical" href="{CY_URL}"')
head = head.replace(f'property="og:url" content="{EN_URL}"', f'property="og:url" content="{CY_URL}"')

# ---- 5. language switcher: mark Welsh as current -------------------------
static = static.replace('<a class="lang-opt on" href="/" hreflang="en-GB">',
                        '<a class="lang-opt" href="/" hreflang="en-GB">')
static = static.replace('<a class="lang-opt" href="/cy" hreflang="cy">',
                        '<a class="lang-opt on" href="/cy" hreflang="cy">')

# ---- 6. drop the whole-block overrides back in ----------------------------
for token, cy_html in block_map.items():
    static = static.replace(token, cy_html)

os.makedirs(OUT_DIR, exist_ok=True)
open(os.path.join(OUT_DIR, 'index.html'), 'w', encoding='utf-8').write(head + static + '<script>' + js + '</script>' + tail)

uniq = sorted(set(missing))
done = len(tr) - len([k for k in tr if not tr[k].strip()])
print(f"cy/index.html written — {done} strings translated, {len(uniq)} still English")
if uniq:
    print("\nNot yet translated:")
    for s in uniq[:40]:
        print(f"  - {s[:100]}")
    if len(uniq) > 40:
        print(f"  ... and {len(uniq)-40} more")
    json.dump({s: "" for s in uniq}, open(os.path.join(HERE, 'i18n', 'cy.todo.json'), 'w'),
              indent=1, ensure_ascii=False)
    print(f"\nWritten to i18n/cy.todo.json for a translator to fill in.")
sys.exit(0)
