/* ============================================================
   Villa Warner #48 — interactions
   ============================================================ */
(function () {
  'use strict';

  /* ---------- Sticky header: solid bar once scrolled ---------- */
  var header = document.getElementById('siteHeader');
  function onScroll() {
    if (window.scrollY > 40) header.classList.add('scrolled');
    else header.classList.remove('scrolled');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ============================================================
     LIGHTBOX
     ============================================================ */
  var items = Array.prototype.slice.call(document.querySelectorAll('.gallery-item'));
  var lightbox = document.getElementById('lightbox');
  var lbImg = document.getElementById('lbImg');
  var lbCaption = document.getElementById('lbCaption');
  var lbClose = document.getElementById('lbClose');
  var lbPrev = document.getElementById('lbPrev');
  var lbNext = document.getElementById('lbNext');

  // Build the slide list from gallery DOM (keeps JS in sync with HTML)
  var slides = items.map(function (el) {
    var img = el.querySelector('img');
    var capEl = el.querySelector('.gallery-caption');
    return {
      src: img.getAttribute('src'),
      alt: img.getAttribute('alt') || '',
      caption: capEl ? capEl.textContent.trim() : ''
    };
  });

  var current = 0;
  var lastFocused = null;

  function showSlide(i) {
    current = (i + slides.length) % slides.length;
    var s = slides[current];
    lbImg.setAttribute('src', s.src);
    lbImg.setAttribute('alt', s.alt);
    lbCaption.textContent = s.caption;
    lbCaption.style.display = s.caption ? '' : 'none';
  }

  function openLightbox(i) {
    lastFocused = document.activeElement;
    showSlide(i);
    lightbox.hidden = false;
    // next frame for transition
    requestAnimationFrame(function () { lightbox.classList.add('is-open'); });
    document.body.style.overflow = 'hidden';
    lbClose.focus();
    document.addEventListener('keydown', onKey);
  }

  function closeLightbox() {
    lightbox.classList.remove('is-open');
    document.removeEventListener('keydown', onKey);
    document.body.style.overflow = '';
    // wait for fade-out before hiding
    setTimeout(function () { lightbox.hidden = true; }, 200);
    if (lastFocused && typeof lastFocused.focus === 'function') lastFocused.focus();
  }

  function onKey(e) {
    if (e.key === 'Escape') closeLightbox();
    else if (e.key === 'ArrowRight') showSlide(current + 1);
    else if (e.key === 'ArrowLeft') showSlide(current - 1);
    else if (e.key === 'Tab') {
      // simple focus trap among the three controls
      e.preventDefault();
    }
  }

  items.forEach(function (el) {
    el.addEventListener('click', function () {
      openLightbox(parseInt(el.getAttribute('data-index'), 10) || 0);
    });
  });

  lbClose.addEventListener('click', closeLightbox);
  lbPrev.addEventListener('click', function () { showSlide(current - 1); });
  lbNext.addEventListener('click', function () { showSlide(current + 1); });

  // Click on backdrop (not the image/controls) closes
  lightbox.addEventListener('click', function (e) {
    if (e.target === lightbox || e.target.classList.contains('lb-figure')) closeLightbox();
  });

  // Swipe on mobile
  var touchStartX = 0, touchStartY = 0;
  lightbox.addEventListener('touchstart', function (e) {
    touchStartX = e.changedTouches[0].clientX;
    touchStartY = e.changedTouches[0].clientY;
  }, { passive: true });
  lightbox.addEventListener('touchend', function (e) {
    var dx = e.changedTouches[0].clientX - touchStartX;
    var dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy)) {
      if (dx < 0) showSlide(current + 1);
      else showSlide(current - 1);
    }
  }, { passive: true });

  /* ============================================================
     SHOWING FORM
     ============================================================ */
  var form = document.getElementById('showingForm');
  var statusEl = document.getElementById('formStatus');
  var submitBtn = document.getElementById('submitBtn');

  var validators = {
    'f-name': function (v) { return v.trim().length >= 2 ? '' : 'Please enter your name.'; },
    'f-email': function (v) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim()) ? '' : 'Please enter a valid email address.';
    },
    'f-phone': function (v) {
      var digits = v.replace(/\D/g, '');
      return digits.length >= 10 ? '' : 'Please enter a valid phone number.';
    }
  };

  function setFieldError(id, msg) {
    var input = document.getElementById(id);
    var field = input.closest('.field');
    var errEl = document.querySelector('[data-error-for="' + id + '"]');
    if (msg) {
      field.classList.add('invalid');
      input.setAttribute('aria-invalid', 'true');
      if (errEl) errEl.textContent = msg;
    } else {
      field.classList.remove('invalid');
      input.removeAttribute('aria-invalid');
      if (errEl) errEl.textContent = '';
    }
  }

  function validateForm() {
    var ok = true;
    var firstBad = null;
    Object.keys(validators).forEach(function (id) {
      var input = document.getElementById(id);
      var msg = validators[id](input.value);
      setFieldError(id, msg);
      if (msg) { ok = false; if (!firstBad) firstBad = input; }
    });
    if (firstBad) firstBad.focus();
    return ok;
  }

  // Clear error as the user fixes a field
  Object.keys(validators).forEach(function (id) {
    var input = document.getElementById(id);
    input.addEventListener('input', function () {
      if (input.closest('.field').classList.contains('invalid')) {
        setFieldError(id, validators[id](input.value));
      }
    });
  });

  function setStatus(msg, type) {
    statusEl.textContent = msg;
    statusEl.classList.remove('is-success', 'is-error');
    if (type) statusEl.classList.add('is-' + type);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    setStatus('', null);

    // Honeypot: if filled, silently pretend success (drop the bot)
    var hp = form.querySelector('input[name="botcheck"]');
    if (hp && hp.checked) {
      setStatus('Thank you — your message has been sent.', 'success');
      form.reset();
      return;
    }

    if (!validateForm()) {
      setStatus('Please fix the highlighted fields above.', 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending…';
    setStatus('', null);

    var data = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: data,
      headers: { 'Accept': 'application/json' }
    })
      .then(function (res) { return res.json().then(function (json) { return { ok: res.ok, json: json }; }); })
      .then(function (result) {
        if (result.ok && result.json.success) {
          form.reset();
          setStatus('Thank you — your message has been sent. Matthew will be in touch shortly.', 'success');
        } else {
          var m = (result.json && result.json.message) ? result.json.message : '';
          setStatus('Sorry, something went wrong' + (m ? ' (' + m + ')' : '') +
            '. Please call or text Matthew at (657) 342-0611.', 'error');
        }
      })
      .catch(function () {
        setStatus('Network error — please call or text Matthew at (657) 342-0611.', 'error');
      })
      .then(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send to Matthew';
      });
  });

})();

/* ============================================================
   LIVE MORTGAGE RATES — pulled from Airtable on page load
   ------------------------------------------------------------
   Source: base "Interest Rates" -> table "From Kevin" (latest row).
   The static values in the HTML are the fallback; this overwrites them
   with the latest values on load. If the fetch fails (offline, JS off,
   token not set), the page simply keeps the last-known static rates.

   SECURITY: the token below ships in this public file, so it MUST be a
   READ-ONLY Airtable token scoped to ONLY the "Interest Rates" base
   (scope: data.records:read). Never put a broader/edit token here.
   ============================================================ */
(function () {
  'use strict';

  var AIRTABLE_TOKEN = 'AIRTABLE_READONLY_TOKEN'; // <-- paste read-only, single-base PAT here
  var BASE = 'appxtXl28vrEIHz0Z';
  var TABLE = 'tblVrlngw97M9CA5j';
  var URL = 'https://api.airtable.com/v0/' + BASE + '/' + TABLE +
            '?maxRecords=1&sort%5B0%5D%5Bfield%5D=Timestamp&sort%5B0%5D%5Bdirection%5D=desc';

  // Airtable stores rates as decimals (0.0575). Convert to "5.75%".
  function pct(x) {
    if (x === null || x === undefined || isNaN(x)) return null;
    var v = parseFloat((x * 100).toFixed(4)); // *100 then strip float noise
    return v + '%';
  }
  function setRate(key, val) {
    if (val === null || val === undefined) return;
    var els = document.querySelectorAll('[data-rate="' + key + '"]');
    for (var i = 0; i < els.length; i++) els[i].textContent = val;
  }

  if (!AIRTABLE_TOKEN || AIRTABLE_TOKEN === 'AIRTABLE_READONLY_TOKEN') return; // not configured yet

  fetch(URL, { headers: { Authorization: 'Bearer ' + AIRTABLE_TOKEN } })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
    .then(function (d) {
      var f = d.records && d.records[0] && d.records[0].fields;
      if (!f) return;
      setRate('15yr',     pct(f['15 Yr. Fixed']));
      setRate('15yr-apr', pct(f['15 Yr. Fixed APR']));
      setRate('30yr',     pct(f['30 Yr. Fixed']));
      setRate('30yr-apr', pct(f['30 Yr. Fixed APR']));
      setRate('30yr-fha', pct(f['30 Yr. FHA']));
      setRate('30yr-fha-apr', pct(f['30 Yr. FHA APR']));
      setRate('30yr-va',  pct(f['30 Yr. VA']));
      setRate('30yr-va-apr', pct(f['30 Yr. VA APR']));

      var dd = f['display date']; // e.g. "6/1/2026"
      if (dd) {
        setRate('asof', dd);
        setRate('assumptions-date', dd);
        var m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(dd);
        if (m) setRate('effective', ('0' + m[1]).slice(-2) + '/' + ('0' + m[2]).slice(-2) + '/' + m[3].slice(-2));
      }
    })
    .catch(function () { /* keep the static fallback rates */ });
})();
