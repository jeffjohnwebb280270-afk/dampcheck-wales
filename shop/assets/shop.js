/* DampCheck Wales trade store.
   Every listing page ships its products as real HTML, so the shop works with
   JavaScript off. This file only enhances: filtering, sorting, paging, the
   basket, and the search box. */
(function () {
  'use strict';

  var CART_KEY = 'dcw-cart-v1';
  var VAT = 0.2;
  var root = document.body.getAttribute('data-root') || '.';

  // ---- money -------------------------------------------------------------
  function money(value) {
    return '£' + value.toLocaleString('en-GB', {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
  }

  // ---- basket ------------------------------------------------------------
  function readCart() {
    try {
      return JSON.parse(localStorage.getItem(CART_KEY)) || {};
    } catch (err) {
      return {};
    }
  }

  function writeCart(cart) {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
    } catch (err) { /* private mode: the basket just will not persist */ }
    paintCount(cart);
  }

  function paintCount(cart) {
    cart = cart || readCart();
    var items = 0;
    Object.keys(cart).forEach(function (code) { items += cart[code].q; });
    [].forEach.call(document.querySelectorAll('[data-cart-count]'), function (node) {
      node.textContent = items;
      node.hidden = items === 0;
    });
  }

  function addToCart(product, quantity) {
    var cart = readCart();
    var existing = cart[product.code];
    cart[product.code] = {
      q: (existing ? existing.q : 0) + quantity,
      name: product.name, price: product.price, img: product.img,
      href: product.href, uom: product.uom, poa: product.poa
    };
    writeCart(cart);
  }

  // "Add to cart" buttons, wherever they appear
  document.addEventListener('click', function (event) {
    var button = event.target.closest('.add');
    if (!button) return;
    var scope = button.closest('[data-code]');
    if (!scope) return;
    var box = scope.querySelector('.qty input');
    var quantity = Math.max(1, parseInt(box && box.value, 10) || 1);
    addToCart({
      code: scope.getAttribute('data-code'),
      name: scope.getAttribute('data-name'),
      price: parseFloat(scope.getAttribute('data-price')) || 0,
      poa: scope.getAttribute('data-poa') === '1',
      uom: scope.getAttribute('data-uom') || '',
      img: scope.getAttribute('data-img') || '',
      href: scope.getAttribute('data-href') || ''
    }, quantity);
    var label = button.textContent;
    button.classList.add('done');
    button.textContent = 'Added ✓';
    setTimeout(function () {
      button.classList.remove('done');
      button.textContent = label;
    }, 1400);
  });

  // quantity steppers
  document.addEventListener('click', function (event) {
    var step = event.target.closest('.qty button');
    if (!step) return;
    var box = step.parentNode.querySelector('input');
    var next = (parseInt(box.value, 10) || 1) + (step.getAttribute('data-step') === '+' ? 1 : -1);
    box.value = Math.max(1, next);
    box.dispatchEvent(new Event('change', { bubbles: true }));
  });

  // ---- listing: filter, sort, page --------------------------------------
  var listing = document.querySelector('[data-listing]');
  if (listing) setupListing(listing);

  function setupListing(grid) {
    var cards = [].slice.call(grid.querySelectorAll('.card'));
    cards.forEach(function (card, index) { card.dataset.pos = index; });

    var perPage = document.getElementById('per-page');
    var sortBy = document.getElementById('sort-by');
    var pager = document.querySelector('[data-pager]');
    var counter = document.querySelector('[data-count]');
    var brandBoxes = [].slice.call(document.querySelectorAll('[data-brand]'));
    var minSlider = document.getElementById('price-min');
    var maxSlider = document.getElementById('price-max');
    var minOut = document.getElementById('price-min-out');
    var maxOut = document.getElementById('price-max-out');
    var fill = document.querySelector('.sliders .fill');
    var page = 1;

    function priceOf(card) { return parseFloat(card.dataset.price) || 0; }

    function paintSlider() {
      if (!minSlider) return;
      var low = +minSlider.value, high = +maxSlider.value;
      if (low > high) { var swap = low; low = high; high = swap; }
      var span = +minSlider.max - +minSlider.min || 1;
      fill.style.left = ((low - +minSlider.min) / span * 100) + '%';
      fill.style.width = ((high - low) / span * 100) + '%';
      minOut.textContent = money(low);
      maxOut.textContent = money(high) + (high >= +minSlider.max ? '+' : '');
    }

    function apply() {
      var brands = brandBoxes.filter(function (b) { return b.checked; })
                             .map(function (b) { return b.getAttribute('data-brand'); });
      var low = minSlider ? Math.min(+minSlider.value, +maxSlider.value) : 0;
      var high = minSlider ? Math.max(+minSlider.value, +maxSlider.value) : Infinity;
      var top = minSlider ? +minSlider.max : Infinity;

      var visible = cards.filter(function (card) {
        if (brands.length && brands.indexOf(card.dataset.brand) === -1) return false;
        var price = priceOf(card);
        if (card.dataset.poa === '1') return true;      // price on application: never filtered out
        if (price < low) return false;
        if (high < top && price > high) return false;
        return true;
      });

      var how = sortBy ? sortBy.value : 'position';
      visible.sort(function (a, b) {
        if (how === 'name') return a.dataset.name.localeCompare(b.dataset.name);
        if (how === 'name-desc') return b.dataset.name.localeCompare(a.dataset.name);
        if (how === 'price') return priceOf(a) - priceOf(b);
        if (how === 'price-desc') return priceOf(b) - priceOf(a);
        return a.dataset.pos - b.dataset.pos;
      });

      var size = perPage ? parseInt(perPage.value, 10) : visible.length;
      var pages = Math.max(1, Math.ceil(visible.length / size));
      if (page > pages) page = pages;
      var from = (page - 1) * size;

      cards.forEach(function (card) { card.hidden = true; });
      visible.slice(from, from + size).forEach(function (card) {
        card.hidden = false;
        grid.appendChild(card);
      });

      if (counter) {
        counter.textContent = visible.length
          ? 'Showing ' + (from + 1) + '–' + Math.min(from + size, visible.length) +
            ' of ' + visible.length + ' product' + (visible.length === 1 ? '' : 's')
          : 'No products match those filters';
      }
      var empty = document.querySelector('[data-empty]');
      if (empty) empty.hidden = visible.length > 0;
      paintPager(pages);
    }

    function paintPager(pages) {
      if (!pager) return;
      pager.innerHTML = '';
      if (pages < 2) return;
      var add = function (label, target, current, disabled) {
        var button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        if (current) button.setAttribute('aria-current', 'page');
        if (disabled) button.disabled = true;
        button.addEventListener('click', function () {
          page = target;
          apply();
          window.scrollTo({ top: grid.offsetTop - 120, behavior: 'smooth' });
        });
        pager.appendChild(button);
      };
      add('‹', page - 1, false, page === 1);
      for (var n = 1; n <= pages; n++) {
        if (n === 1 || n === pages || Math.abs(n - page) <= 2) {
          add(String(n), n, n === page, false);
        } else if (Math.abs(n - page) === 3) {
          var gap = document.createElement('span');
          gap.textContent = '…';
          gap.className = 'muted';
          pager.appendChild(gap);
        }
      }
      add('›', page + 1, false, page === pages);
    }

    [perPage, sortBy].forEach(function (control) {
      if (control) control.addEventListener('change', function () { page = 1; apply(); });
    });
    brandBoxes.forEach(function (box) {
      box.addEventListener('change', function () { page = 1; apply(); });
    });
    [minSlider, maxSlider].forEach(function (slider) {
      if (slider) slider.addEventListener('input', function () { page = 1; paintSlider(); apply(); });
    });

    var view = document.querySelector('[data-view]');
    if (view) {
      var saved = null;
      try { saved = localStorage.getItem('dcw-view'); } catch (err) { /* ignore */ }
      if (saved === 'list') setView('list');
      view.addEventListener('click', function (event) {
        var button = event.target.closest('button');
        if (button) setView(button.getAttribute('data-set'));
      });
    }
    function setView(mode) {
      grid.classList.toggle('list', mode === 'list');
      [].forEach.call(document.querySelectorAll('[data-view] button'), function (button) {
        button.setAttribute('aria-pressed', String(button.getAttribute('data-set') === mode));
      });
      try { localStorage.setItem('dcw-view', mode); } catch (err) { /* ignore */ }
    }

    paintSlider();
    apply();
  }

  // On a phone the filter panels come before the products, so they start shut.
  if (window.matchMedia('(max-width: 900px)').matches) {
    [].forEach.call(document.querySelectorAll('.side .panel[open]'), function (panel) {
      panel.open = false;
    });
  }

  // ---- search ------------------------------------------------------------
  var catalogue = null;
  function loadCatalogue() {
    if (catalogue) return catalogue;
    catalogue = fetch(root + '/products.json').then(function (response) { return response.json(); });
    return catalogue;
  }

  var searchInput = document.getElementById('q');
  if (searchInput) {
    var panel = document.getElementById('suggest');
    var timer = null;
    searchInput.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { suggest(searchInput.value.trim()); }, 120);
    });
    searchInput.addEventListener('blur', function () {
      setTimeout(function () { if (panel) panel.hidden = true; }, 180);
    });
    searchInput.addEventListener('focus', function () {
      if (panel && panel.children.length && searchInput.value.trim()) panel.hidden = false;
    });
  }

  function suggest(term) {
    var panel = document.getElementById('suggest');
    if (!panel) return;
    if (term.length < 2) { panel.hidden = true; return; }
    loadCatalogue().then(function (products) {
      var hits = match(products, term).slice(0, 8);
      panel.innerHTML = hits.map(function (p) {
        return '<a href="' + root + '/product/' + p.slug + '.html">' +
               '<img src="' + root + '/' + p.img + '" alt="" loading="lazy">' +
               '<span>' + escapeHtml(p.name) + '</span>' +
               '<span class="c">' + p.code + '</span></a>';
      }).join('') || '<a href="' + root + '/search.html?q=' + encodeURIComponent(term) +
                     '">No match — search the full catalogue</a>';
      panel.hidden = false;
    });
  }

  function match(products, term) {
    var words = term.toLowerCase().split(/\s+/).filter(Boolean);
    return products.map(function (p) {
      var hay = (p.name + ' ' + p.code + ' ' + p.group + ' ' + p.brand).toLowerCase();
      var score = 0;
      for (var i = 0; i < words.length; i++) {
        var at = hay.indexOf(words[i]);
        if (at === -1) return null;
        score += at === 0 ? 3 : 1;
        if (p.code.toLowerCase().indexOf(words[i]) === 0) score += 4;
      }
      return { p: p, score: score };
    }).filter(Boolean)
      .sort(function (a, b) { return b.score - a.score || a.p.name.localeCompare(b.p.name); })
      .map(function (hit) { return hit.p; });
  }

  function escapeHtml(text) {
    return String(text).replace(/[&<>"]/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch];
    });
  }

  // ---- search results page ----------------------------------------------
  var results = document.querySelector('[data-results]');
  if (results) {
    var query = new URLSearchParams(location.search).get('q') || '';
    var field = document.getElementById('q');
    if (field) field.value = query;
    var heading = document.querySelector('[data-results-head]');
    loadCatalogue().then(function (products) {
      var hits = query.trim() ? match(products, query.trim()) : [];
      if (heading) {
        heading.textContent = query.trim()
          ? hits.length + ' result' + (hits.length === 1 ? '' : 's') + ' for “' + query + '”'
          : 'Search the catalogue';
      }
      results.innerHTML = hits.slice(0, 300).map(cardHtml).join('');
      var none = document.querySelector('[data-no-results]');
      if (none) none.hidden = !(query.trim() && !hits.length);
    });
  }

  function cardHtml(p) {
    var href = root + '/product/' + p.slug + '.html';
    var price = p.poa
      ? '<div class="poa">Price on application</div>'
      : '<div class="price">' + money(p.price) + ' <small>excl VAT</small></div>' +
        '<div class="incl">' + money(p.price * (1 + VAT)) + ' incl VAT</div>';
    return '<article class="card" data-code="' + escapeHtml(p.code) + '" data-name="' +
      escapeHtml(p.name) + '" data-price="' + p.price + '" data-poa="' + (p.poa ? 1 : 0) +
      '" data-uom="' + escapeHtml(p.uom) + '" data-img="' + p.img + '" data-href="' + href + '">' +
      '<a class="shot" href="' + href + '"><img src="' + root + '/' + p.img + '" alt="' +
      escapeHtml(p.name) + '" loading="lazy"></a><div class="body">' +
      '<a class="name" href="' + href + '">' + escapeHtml(p.name) + '</a>' +
      '<div class="meta">' + escapeHtml(p.code) + ' · ' + escapeHtml(p.pack) + '</div>' +
      price + '<div class="buyrow"><div class="qty">' +
      '<button type="button" data-step="-" aria-label="Fewer">−</button>' +
      '<input type="number" min="1" value="1" aria-label="Quantity">' +
      '<button type="button" data-step="+" aria-label="More">+</button></div>' +
      '<button type="button" class="add">Add to cart</button></div></div></article>';
  }

  // ---- basket page -------------------------------------------------------
  var basket = document.querySelector('[data-basket]');
  if (basket) paintBasket();

  function paintBasket() {
    var cart = readCart();
    var codes = Object.keys(cart);
    var lines = document.querySelector('[data-basket]');
    var summary = document.querySelector('[data-summary]');
    var emptyNote = document.querySelector('[data-basket-empty]');

    if (!codes.length) {
      lines.innerHTML = '';
      if (emptyNote) emptyNote.hidden = false;
      if (summary) summary.hidden = true;
      paintCount(cart);
      return;
    }
    if (emptyNote) emptyNote.hidden = true;
    if (summary) summary.hidden = false;

    lines.innerHTML = codes.map(function (code) {
      var item = cart[code];
      var sum = item.poa ? 'POA' : money(item.price * item.q);
      return '<div class="line" data-code="' + escapeHtml(code) + '">' +
        '<img src="' + root + '/' + item.img + '" alt="" loading="lazy">' +
        '<div class="info"><b><a href="' + item.href + '">' + escapeHtml(item.name) + '</a></b>' +
        '<span class="small muted">' + escapeHtml(code) + ' · ' +
        (item.poa ? 'price on application' : money(item.price) + ' excl VAT / ' +
         escapeHtml(item.uom)) + '</span><br>' +
        '<button class="rm" type="button" data-remove>Remove</button></div>' +
        '<div class="qty"><button type="button" data-step="-" aria-label="Fewer">−</button>' +
        '<input type="number" min="1" value="' + item.q + '" aria-label="Quantity">' +
        '<button type="button" data-step="+" aria-label="More">+</button></div>' +
        '<div class="sum">' + sum + '</div></div>';
    }).join('');

    var net = 0, hasPoa = false;
    codes.forEach(function (code) {
      if (cart[code].poa) hasPoa = true;
      else net += cart[code].price * cart[code].q;
    });
    setText('[data-net]', money(net));
    setText('[data-vat]', money(net * VAT));
    setText('[data-gross]', money(net * (1 + VAT)));
    var poaNote = document.querySelector('[data-poa-note]');
    if (poaNote) poaNote.hidden = !hasPoa;

    var order = document.querySelector('.order');
    if (order) order.value = orderText(cart, net);
    var mail = document.querySelector('[data-mailto]');
    if (mail) {
      mail.href = 'mailto:' + mail.getAttribute('data-email') +
        '?subject=' + encodeURIComponent('Order enquiry — ' + codes.length + ' line(s)') +
        '&body=' + encodeURIComponent(orderText(cart, net));
    }
    paintCount(cart);
  }

  function orderText(cart, net) {
    var rows = Object.keys(cart).map(function (code) {
      var item = cart[code];
      return item.q + ' x ' + code + '  ' + item.name +
        (item.poa ? '  (price on application)' : '  ' + money(item.price * item.q) + ' excl VAT');
    });
    return 'Order enquiry\n\n' + rows.join('\n') +
      '\n\nGoods total (excl VAT): ' + money(net) +
      '\nVAT at 20%: ' + money(net * VAT) +
      '\nTotal (incl VAT): ' + money(net * (1 + VAT)) +
      '\n\nDelivery address:\nContact name:\nPhone:\nAccount number (if you have one):\n';
  }

  function setText(selector, text) {
    var node = document.querySelector(selector);
    if (node) node.textContent = text;
  }

  document.addEventListener('click', function (event) {
    if (!event.target.matches('[data-remove]')) return;
    var cart = readCart();
    delete cart[event.target.closest('.line').getAttribute('data-code')];
    writeCart(cart);
    paintBasket();
  });

  document.addEventListener('change', function (event) {
    var line = event.target.closest('.line');
    if (!line || !event.target.matches('.qty input')) return;
    var cart = readCart();
    var code = line.getAttribute('data-code');
    if (cart[code]) {
      cart[code].q = Math.max(1, parseInt(event.target.value, 10) || 1);
      writeCart(cart);
      paintBasket();
    }
  });

  var clear = document.querySelector('[data-clear]');
  if (clear) {
    clear.addEventListener('click', function () {
      writeCart({});
      paintBasket();
    });
  }

  paintCount();
})();
