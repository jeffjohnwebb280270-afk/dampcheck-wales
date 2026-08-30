#!/usr/bin/env python3
"""
Draw the catalogue images.

Nobody has photographed 593 trade lines, and a grid of "NO IMAGE" boxes is what
the shop this one is modelled on already does badly. So every product gets a
drawn illustration of the thing it physically is — a 20kg bucket, a dimpled
membrane roll, a helical bar — tinted by manufacturer, generated straight from
the price list.

A real photograph always wins: drop <product-code>.jpg (or .png/.webp) into
shop/img/photos/ and build_shop.py will use it for that product instead.
"""
import os

# Manufacturer tints. Close enough to each brand's own colour to be recognisable
# on the shelf, muted enough that 25 of them in a grid still look like one shop.
BRAND_TINTS = {
    'Wykamol':            ('#17607A', '#0F485C'),
    'Mapei':              ('#0B5DA8', '#084681'),
    'Thor Helical':       ('#5A646E', '#414A53'),
    'Sika':               ('#C89A12', '#9A760B'),
    'Triton':             ('#243F6E', '#182B4D'),
    'Protimeter':         ('#2C7A5A', '#1F5A42'),
    'Other Manufacturers': ('#4C5862', '#374049'),
}
DEFAULT_TINT = BRAND_TINTS['Other Manufacturers']

CANVAS = 480
BG = '#F7F8F9'
LINE = '#20272E'
METAL = '#B9C2CA'
METAL_D = '#8D98A3'
LABEL = '#FFFFFF'


def _shadow(cx=240, cy=418, rx=132, ry=17):
    return ('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="#20272E" opacity=".13"/>'
            % (cx, cy, rx, ry))


def _label(x, y, w, h, tint):
    """The white band every trade container carries its name on."""
    return ('<rect x="%d" y="%d" width="%d" height="%d" rx="3" fill="%s" opacity=".93"/>'
            '<rect x="%d" y="%d" width="%d" height="7" rx="3.5" fill="%s"/>'
            % (x, y, w, h, LABEL, x + 14, y + 15, max(w - 60, 20), tint))


def bucket(t, d):
    return (_shadow() +
            '<path d="M148 158 L332 158 L312 400 Q310 414 296 414 L184 414 Q170 414 168 400 Z" fill="%s"/>'
            '<path d="M240 158 L332 158 L312 400 Q310 414 296 414 L240 414 Z" fill="%s"/>'
            '<rect x="140" y="140" width="200" height="26" rx="9" fill="%s"/>'
            '<rect x="140" y="140" width="200" height="10" rx="5" fill="#FFFFFF" opacity=".22"/>'
            '<path d="M158 150 Q240 96 322 150" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round"/>'
            % (t, d, d, METAL_D)) + _label(178, 214, 124, 96, t)


def bag(t, d):
    """A cement-style sack: pinched seams top and bottom, so it never reads as a tub."""
    return (_shadow(240, 418, 132, 15) +
            '<path d="M138 154 q102 -18 204 0 l14 34 q-14 100 0 200 l-14 30 q-102 18 -204 0 '
            'l-14 -30 q14 -100 0 -200 Z" fill="%s"/>'
            '<path d="M240 146 q56 0 102 8 l14 34 q-14 100 0 200 l-14 30 q-46 8 -102 8 Z" fill="%s"/>'
            '<path d="M138 154 q102 -18 204 0 l14 34 q-116 -20 -232 0 Z" fill="#FFFFFF" opacity=".2"/>'
            '<path d="M124 372 q116 20 232 0 l-14 30 q-102 18 -204 0 Z" fill="#000000" opacity=".12"/>'
            % (t, d)) + _label(172, 224, 136, 108, t)


def jerrycan(t, d):
    return (_shadow(240, 416, 118, 15) +
            '<rect x="146" y="150" width="188" height="264" rx="20" fill="%s"/>'
            '<rect x="240" y="150" width="94" height="264" rx="20" fill="%s"/>'
            '<rect x="146" y="150" width="188" height="264" rx="20" fill="none" stroke="%s" stroke-width="3" opacity=".35"/>'
            '<rect x="196" y="106" width="52" height="48" rx="8" fill="%s"/>'
            '<rect x="188" y="92" width="68" height="24" rx="9" fill="%s"/>'
            '<path d="M270 120 q46 0 46 34 v20" fill="none" stroke="%s" stroke-width="14" stroke-linecap="round"/>'
            % (t, d, d, d, METAL_D, d)) + _label(176, 212, 128, 122, t)


def bottle(t, d):
    return (_shadow(240, 418, 92, 13) +
            '<path d="M196 168 h88 l14 42 q10 26 10 54 v128 q0 22 -22 22 h-92 q-22 0 -22 -22 V264 q0 -28 10 -54 Z" fill="%s"/>'
            '<path d="M240 168 h44 l14 42 q10 26 10 54 v128 q0 22 -22 22 h-46 Z" fill="%s"/>'
            '<rect x="206" y="118" width="68" height="54" rx="6" fill="%s"/>'
            '<rect x="200" y="98" width="80" height="26" rx="8" fill="%s"/>'
            % (t, d, d, METAL_D)) + _label(184, 254, 112, 96, t)


def drum(t, d):
    return (_shadow(240, 420, 128, 16) +
            '<rect x="130" y="132" width="220" height="276" rx="16" fill="%s"/>'
            '<rect x="240" y="132" width="110" height="276" rx="16" fill="%s"/>'
            '<ellipse cx="240" cy="134" rx="110" ry="26" fill="%s"/>'
            '<ellipse cx="240" cy="134" rx="110" ry="26" fill="#FFFFFF" opacity=".14"/>'
            '<rect x="130" y="196" width="220" height="20" fill="#FFFFFF" opacity=".18"/>'
            '<rect x="130" y="330" width="220" height="20" fill="#FFFFFF" opacity=".18"/>'
            '<circle cx="204" cy="132" r="15" fill="%s"/>'
            % (t, d, d, METAL_D)) + _label(178, 240, 124, 78, t)


def ibc(t, d):
    return (_shadow(240, 424, 146, 14) +
            '<rect x="112" y="132" width="256" height="252" rx="10" fill="%s" opacity=".55"/>'
            '<g stroke="%s" stroke-width="9" fill="none">'
            '<rect x="106" y="126" width="268" height="264" rx="8"/>'
            '<path d="M106 192 h268 M106 258 h268 M106 324 h268 M172 126 v264 M240 126 v264 M308 126 v264"/>'
            '</g>'
            '<rect x="140" y="384" width="200" height="30" rx="6" fill="%s"/>'
            '<rect x="212" y="104" width="56" height="30" rx="6" fill="%s"/>'
            % (t, METAL_D, d, d))


def cartridge(t, d):
    return (_shadow(240, 420, 80, 12) +
            '<rect x="176" y="152" width="128" height="256" rx="10" fill="%s"/>'
            '<rect x="240" y="152" width="64" height="256" rx="10" fill="%s"/>'
            '<path d="M212 152 h56 l-6 -34 h-44 Z" fill="%s"/>'
            '<path d="M226 118 h28 l-4 -40 h-20 Z" fill="%s"/>'
            % (t, d, d, METAL_D)) + _label(192, 208, 96, 132, t)


def membrane(t, d):
    dimples = ''
    for row in range(6):
        for col in range(7):
            cx = 214 + col * 26 + (13 if row % 2 else 0)
            cy = 176 + row * 26
            dimples += '<circle cx="%d" cy="%d" r="7" fill="#FFFFFF" opacity=".22"/>' % (cx, cy)
    return (_shadow(250, 420, 130, 15) +
            '<path d="M188 148 q-58 96 0 246 l178 0 q-58 -150 0 -246 Z" fill="%s"/>' % t +
            '<path d="M188 148 q-58 96 0 246 l40 0 q-58 -150 0 -246 Z" fill="%s"/>' % d +
            dimples +
            '<ellipse cx="188" cy="271" rx="34" ry="123" fill="%s"/>' % d +
            '<ellipse cx="188" cy="271" rx="18" ry="66" fill="%s"/>' % BG +
            '<ellipse cx="188" cy="271" rx="18" ry="66" fill="none" stroke="%s" stroke-width="4"/>' % d)


def tape(t, d):
    return (_shadow(240, 412, 110, 14) +
            '<circle cx="240" cy="256" r="132" fill="%s"/>'
            '<circle cx="240" cy="256" r="132" fill="none" stroke="%s" stroke-width="6"/>'
            '<circle cx="240" cy="256" r="104" fill="%s" opacity=".55"/>'
            '<circle cx="240" cy="256" r="58" fill="%s"/>'
            '<circle cx="240" cy="256" r="58" fill="none" stroke="%s" stroke-width="5"/>'
            '<path d="M356 196 q30 22 8 54" fill="none" stroke="%s" stroke-width="16" stroke-linecap="round"/>'
            % (t, d, d, BG, d, t))


def roll(t, d):
    return tape(t, d)


def mesh(t, d):
    grid = ''
    for i in range(9):
        grid += '<path d="M%d 150 L%d 372" stroke="%s" stroke-width="5" opacity=".85"/>' % (
            152 + i * 22, 152 + i * 22, t)
    for j in range(11):
        grid += '<path d="M144 %d L360 %d" stroke="%s" stroke-width="5" opacity=".6"/>' % (
            156 + j * 22, 156 + j * 22, d)
    return _shadow(252, 400, 118, 13) + grid


def board(t, d):
    return (_shadow(240, 414, 138, 14) +
            '<path d="M120 176 L330 122 L364 152 L154 206 Z" fill="%s"/>'
            '<path d="M120 176 L154 206 L154 386 L120 356 Z" fill="%s"/>'
            '<path d="M154 206 L364 152 L364 332 L154 386 Z" fill="%s" opacity=".8"/>'
            % (t, d, t))


def channel(t, d):
    return (_shadow(240, 402, 140, 14) +
            '<path d="M96 268 L300 176 L392 214 L188 306 Z" fill="%s"/>'
            '<path d="M96 268 L188 306 L188 366 L96 328 Z" fill="%s"/>'
            '<path d="M188 306 L392 214 L392 274 L188 366 Z" fill="%s" opacity=".75"/>'
            '<path d="M126 254 L318 168 M158 240 L350 154" stroke="%s" stroke-width="7" opacity=".45" stroke-linecap="round"/>'
            % (t, d, t, BG))


def plug(t, d):
    body = ''
    for i, x in enumerate((150, 240, 330)):
        y = 176 + (18 if i == 1 else 0)
        body += ('<rect x="%d" y="%d" width="34" height="150" rx="12" fill="%s"/>'
                 '<circle cx="%d" cy="%d" r="34" fill="%s"/>'
                 '<circle cx="%d" cy="%d" r="20" fill="%s" opacity=".45"/>'
                 % (x - 17, y, t, x, y + 158, d, x, y + 158, BG))
    return _shadow(240, 402, 126, 13) + body


def tie(t, d):
    coils = ''
    for i in range(9):
        x = 132 + i * 26
        coils += ('<path d="M%d 300 q13 -78 26 0" fill="none" stroke="%s" stroke-width="13" stroke-linecap="round"/>'
                  % (x, METAL))
        coils += ('<path d="M%d 300 q13 78 26 0" fill="none" stroke="%s" stroke-width="13" stroke-linecap="round" opacity=".55"/>'
                  % (x, METAL_D))
    return (_shadow(240, 372, 132, 12) + coils +
            '<path d="M126 300 h240" stroke="%s" stroke-width="5" opacity=".35"/>' % t)


def drill(t, d):
    flutes = ''
    for i in range(7):
        y = 168 + i * 26
        flutes += ('<path d="M228 %d q24 13 0 26" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round"/>'
                   % (y, METAL_D))
    return (_shadow(240, 410, 62, 11) +
            '<rect x="224" y="120" width="32" height="240" rx="6" fill="%s"/>' % METAL +
            flutes +
            '<path d="M224 120 h32 l-16 -34 Z" fill="%s"/>' % t +
            '<rect x="220" y="356" width="40" height="52" rx="8" fill="%s"/>' % METAL_D)


def nozzle(t, d):
    return (_shadow(240, 402, 90, 12) +
            '<path d="M216 130 h48 l16 200 q2 30 -40 30 q-42 0 -40 -30 Z" fill="%s"/>'
            '<path d="M240 130 h24 l16 200 q2 30 -40 30 Z" fill="%s"/>'
            '<rect x="222" y="98" width="36" height="36" rx="6" fill="%s"/>'
            '<rect x="208" y="330" width="64" height="18" rx="6" fill="%s" opacity=".5"/>'
            % (t, d, METAL_D, BG))


def valve(t, d):
    return (_shadow(240, 396, 108, 13) +
            '<rect x="120" y="230" width="240" height="76" rx="14" fill="%s"/>'
            '<rect x="120" y="230" width="240" height="30" rx="14" fill="#FFFFFF" opacity=".16"/>'
            '<rect x="100" y="212" width="42" height="112" rx="9" fill="%s"/>'
            '<rect x="338" y="212" width="42" height="112" rx="9" fill="%s"/>'
            '<rect x="214" y="150" width="52" height="88" rx="10" fill="%s"/>'
            '<rect x="180" y="126" width="120" height="30" rx="12" fill="%s"/>'
            % (t, d, d, d, METAL_D))


def pump(t, d):
    return (_shadow(240, 414, 126, 15) +
            '<rect x="140" y="216" width="200" height="184" rx="18" fill="%s"/>'
            '<rect x="240" y="216" width="100" height="184" rx="18" fill="%s"/>'
            '<circle cx="240" cy="308" r="58" fill="%s"/>'
            '<circle cx="240" cy="308" r="34" fill="%s" opacity=".5"/>'
            '<rect x="206" y="130" width="68" height="94" rx="10" fill="%s"/>'
            '<path d="M274 158 h74 q18 0 18 18 v46" fill="none" stroke="%s" stroke-width="20" stroke-linecap="round"/>'
            % (t, d, BG, d, d, METAL_D))


def sump(t, d):
    return (_shadow(240, 420, 132, 15) +
            '<path d="M144 176 L336 176 L316 400 Q314 414 300 414 L180 414 Q166 414 164 400 Z" fill="%s"/>'
            '<path d="M240 176 L336 176 L316 400 Q314 414 300 414 L240 414 Z" fill="%s"/>'
            '<ellipse cx="240" cy="176" rx="96" ry="26" fill="%s"/>'
            '<ellipse cx="240" cy="176" rx="68" ry="17" fill="%s"/>'
            '<path d="M170 250 h140 M176 310 h128" stroke="#FFFFFF" stroke-width="7" opacity=".22"/>'
            % (t, d, d, BG))


def float_switch(t, d):
    return (_shadow(240, 414, 92, 12) +
            '<path d="M240 118 v92" stroke="%s" stroke-width="10" stroke-linecap="round"/>' % METAL_D +
            '<rect x="176" y="206" width="128" height="86" rx="16" fill="%s"/>' % t +
            '<rect x="240" y="206" width="64" height="86" rx="16" fill="%s"/>' % d +
            '<circle cx="212" cy="249" r="15" fill="#F5B32B"/>'
            '<circle cx="268" cy="249" r="15" fill="%s" opacity=".6"/>' % BG +
            '<path d="M240 292 q-70 34 -70 74" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round"/>' % METAL_D +
            '<ellipse cx="168" cy="382" rx="46" ry="32" fill="%s"/>' % d)


def fan(t, d):
    blades = ''
    for angle in (0, 90, 180, 270):
        blades += ('<path d="M240 256 q56 -30 76 -76 q-46 -20 -76 76 Z" fill="%s" '
                   'transform="rotate(%d 240 256)"/>' % (t, angle))
    return (_shadow(240, 414, 118, 13) +
            '<rect x="112" y="128" width="256" height="256" rx="26" fill="%s"/>' % d +
            '<rect x="112" y="128" width="256" height="256" rx="26" fill="#FFFFFF" opacity=".12"/>' +
            '<circle cx="240" cy="256" r="106" fill="%s"/>' % BG + blades +
            '<circle cx="240" cy="256" r="26" fill="%s"/>' % d)


def meter(t, d):
    return (_shadow(240, 418, 92, 12) +
            '<rect x="164" y="128" width="152" height="284" rx="22" fill="%s"/>' % t +
            '<rect x="240" y="128" width="76" height="284" rx="22" fill="%s"/>' % d +
            '<rect x="186" y="152" width="108" height="86" rx="8" fill="#DDE7E2"/>'
            '<rect x="200" y="176" width="66" height="12" rx="6" fill="%s"/>' % d +
            '<rect x="200" y="198" width="44" height="10" rx="5" fill="%s" opacity=".5"/>' % d +
            '<g fill="%s" opacity=".9">' % BG +
            ''.join('<rect x="%d" y="%d" width="30" height="24" rx="6"/>' % (190 + c * 38, 262 + r * 32)
                    for r in range(3) for c in range(3)) +
            '</g>'
            '<path d="M204 128 v-34 M276 128 v-34" stroke="%s" stroke-width="9" stroke-linecap="round"/>' % METAL_D)


def tool(t, d):
    return (_shadow(240, 410, 118, 13) +
            '<rect x="150" y="220" width="220" height="54" rx="18" fill="%s"/>' % METAL +
            '<rect x="150" y="220" width="220" height="22" rx="11" fill="#FFFFFF" opacity=".35"/>' +
            '<path d="M370 232 h40 l22 15 l-22 15 h-40 Z" fill="%s"/>' % d +
            '<rect x="126" y="204" width="42" height="86" rx="12" fill="%s"/>' % t +
            '<path d="M148 290 q-6 66 -52 84" fill="none" stroke="%s" stroke-width="22" stroke-linecap="round"/>' % t +
            '<path d="M164 290 q26 44 74 48" fill="none" stroke="%s" stroke-width="18" stroke-linecap="round"/>' % d)


def box(t, d):
    return (_shadow(240, 416, 130, 14) +
            '<path d="M240 128 L378 178 L240 228 L102 178 Z" fill="%s"/>'
            '<path d="M102 178 L240 228 L240 400 L102 350 Z" fill="%s"/>'
            '<path d="M378 178 L240 228 L240 400 L378 350 Z" fill="%s" opacity=".78"/>'
            '<path d="M240 228 v172" stroke="#FFFFFF" stroke-width="3" opacity=".2"/>'
            % (t, d, t)) + _label(126, 250, 92, 60, t)


def part(t, d):
    return (_shadow(240, 400, 104, 13) +
            '<circle cx="240" cy="256" r="118" fill="%s"/>' % t +
            '<circle cx="240" cy="256" r="118" fill="none" stroke="%s" stroke-width="8"/>' % d +
            ''.join('<rect x="230" y="120" width="20" height="34" rx="5" fill="%s" '
                    'transform="rotate(%d 240 256)"/>' % (d, a) for a in range(0, 360, 45)) +
            '<circle cx="240" cy="256" r="62" fill="%s"/>' % BG +
            '<circle cx="240" cy="256" r="30" fill="%s" opacity=".35"/>' % d)


KINDS = {
    'bucket': bucket, 'bag': bag, 'jerrycan': jerrycan, 'bottle': bottle,
    'drum': drum, 'ibc': ibc, 'cartridge': cartridge, 'membrane': membrane,
    'tape': tape, 'roll': roll, 'mesh': mesh, 'board': board, 'channel': channel,
    'plug': plug, 'tie': tie, 'drill': drill, 'nozzle': nozzle, 'valve': valve,
    'pump': pump, 'sump': sump, 'float': float_switch, 'fan': fan, 'meter': meter,
    'tool': tool, 'box': box, 'part': part,
}


def render(kind, brand):
    tint, dark = BRAND_TINTS.get(brand, DEFAULT_TINT)
    draw = KINDS.get(kind, part)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img">'
            '<rect width="%d" height="%d" fill="%s"/>%s</svg>'
            % (CANVAS, CANVAS, CANVAS, CANVAS, BG, draw(tint, dark)))


def write_all(out_dir, pairs):
    """pairs: iterable of (kind, brand). Returns {(kind, brand): filename}."""
    os.makedirs(out_dir, exist_ok=True)
    written = {}
    for kind, brand in sorted(set(pairs)):
        name = '%s--%s.svg' % (kind, brand.lower().replace(' ', '-'))
        with open(os.path.join(out_dir, name), 'w', encoding='utf-8') as handle:
            handle.write(render(kind, brand))
        written[(kind, brand)] = name
    return written
