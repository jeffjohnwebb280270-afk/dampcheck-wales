# Outstanding — DampCheck Wales

Three jobs left on the Welsh side, as of 24 August 2026. Everything else
across the four damp sites is merged and live.

Ask Claude for "the 3 damp site jobs" and it should pick this up from here.

---

## 1. Make the letter translatable  ← the one that matters

The generated letter is still entirely in English, on both the English and
the Welsh page. It is the document a tenant sends their landlord, so it is
the last thing on the site that should be English.

It cannot be translated as it stands. The body is built as one template
literal with the name, address, rooms and dates interpolated through it:

    `... at the above property, which I occupy under an occupation
     contract. I first noticed the problem on ${firstTxt}. ...`

`build_cy.py` deliberately skips any text adjacent to a `${...}` — half a
sentence makes an unstable translation key. So the letter needs
restructuring into translatable pieces with the values slotted in, and only
then can the Welsh go in.

Two paragraphs of Welsh for it were already supplied and are recorded here
so they are not lost:

> Rwy'n ysgrifennu i roi gwybod am leithder a llwydni yn yr eiddo uchod, yr
> wyf yn ei feddiannu o dan gytundeb meddiannaeth. Sylwais ar y broblem
> gyntaf ar…

> O dan Ddeddf Rhentu Cartrefi (Cymru) 2016, mae fy nghytundeb meddiannaeth
> yn cynnwys amod bod yn rhaid i chi sicrhau bod yr annedd yn addas i bobl
> fyw ynddi…

Note both use *cytundeb meddiannaeth*, which now matches the rest of the
site — see job 3.

The same problem affects two smaller fragments in the deadline panel:
"days since you reported it", and "days has that fact on the record now."

## 2. Two remaining `anwedd` phrases

The site settled on **cyddwysiad** for *condensation*, but two older strings
still read *anwedd*:

    …a'r ddadl anwedd…        ("the condensation argument")
    …blocio, neu anwedd.…     ("a blocked airbrick, or condensation")

They were left alone deliberately: the mutation after a feminine noun and
after *neu* is not something to guess at. Translate these two short phrases
and they can go straight in:

    the condensation argument
    a blocked airbrick, or condensation

## 3. Decide how far `cytundeb` goes

*Occupation contract* is now **cytundeb meddiannaeth** in the three places
it appears as the full term. Nine other uses of the word *contract* were
left untouched, and may or may not be a loose end:

- **four are `deiliad contract`** — contract-holder, its own statutory term
- **four are a bare `contract`** standing in for the same thing
  ("eich contract", "ar ddechrau'r contract", "trwy gydol y contract")
- **one is `gontractio`**, the verb "to contract out" — unrelated, leave it

`contract` and `cytundeb` share an initial c, so every Welsh mutation
applies identically and a careful swap preserves them.

---

## Worth knowing before touching the Welsh build

`build_cy.py` reports how many strings are "still English". That number
only counts strings it is **able to offer**. It cannot see anything wrapped
around a `${...}` interpolation — which is exactly what the letter is.

It previously reported zero while two dozen English strings sat on the
page. Three separate defects caused that and are now fixed (silent drops in
`look()`, a regex that ran across newlines, and HTML entities failing the
prose test). The count is honest now, but it is still a count of what the
build can reach, not of what a visitor sees.

`i18n/cy.todo.json` is generated and gitignored. It is only meaningful
immediately after a build — a stale committed copy is what made six
long-finished strings look outstanding for weeks.
