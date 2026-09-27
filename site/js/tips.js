/* Dime Bags: tap a line → bet slip → Garden Bucks (pretend). Wallet page fills from /api/wallet. */
(function () {
  var BASE = location.pathname.replace(/\/issues\/[^\/]*$/, '/').replace(/[^\/]*$/, '');
  var HDR = { 'Content-Type': 'application/json', 'X-Garden-App': '1' };
  function esc(t) { var d = document.createElement('div'); d.textContent = t == null ? '' : String(t); return d.innerHTML; }
  var wallet = null;
  function paintWallet() {
    var el = document.getElementById('tip-wallet'); if (!el || !wallet) return;
    var rows = (wallet.bets || []).slice(-20).reverse().map(function (b) {
      var st = b.status === 'won' ? '✅ won ' + b.payout : b.status === 'lost' ? '❌ lost' : '⏳ open';
      return '<tr><td>' + esc(b.date) + '</td><td>' + esc(b.market_title || b.market) + '</td><td><b>' + esc(b.label) + '</b> ' + esc(b.odds[0] + '-' + b.odds[1]) +
             '</td><td class="num">' + b.stake + '</td><td>' + st + '</td></tr>';
    }).join('');
    el.innerHTML = '<div class="tip-bank"><small>Garden Bucks</small><b>' + wallet.balance + '</b></div>' +
      (rows ? '<table class="agate"><thead><tr><th>Card</th><th>Market</th><th>Pick</th><th>Stake</th><th></th></tr></thead><tbody>' + rows + '</tbody></table>'
            : '<p class="small">No slips yet — tap a line on Tonight\'s Card.</p>');
  }
  function load() { fetch(BASE + 'api/wallet', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (w) { wallet = w; paintWallet(); }).catch(function () {}); }
  if (window.jQuery && jQuery.fn.turn) jQuery('#flipbook').bind('turned', function () { setTimeout(paintWallet, 50); });
  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('.tip-opt'); if (!b) return;
    ev.preventDefault(); ev.stopPropagation();
    var o = b.dataset.odds.split('/'), mkt = b.closest('.tip-mkt').querySelector('.tip-mh b').textContent;
    var wrap = document.createElement('div'); wrap.className = 'modal';
    wrap.innerHTML = '<div class="modal-card"><button type="button" class="modal-x" aria-label="Close">×</button><div class="kicker">' + esc(mkt) + '</div>' +
      '<h3>' + esc(b.dataset.label) + ' <span class="tip-odds">' + o[0] + '-' + o[1] + '</span></h3><p class="small">Balance: ' + (wallet ? wallet.balance : '…') + ' Garden Bucks</p>' +
      '<div class="tip-stakes">' + [10, 25, 50, 100, 250].map(function (s) { return '<button type="button" class="btn" data-s="' + s + '">' + s + '</button>'; }).join('') + '</div>' +
      '<p class="small tip-win"></p><p class="small dmsg"></p></div>';
    document.body.appendChild(wrap);
    ['touchstart', 'touchmove', 'wheel', 'mousedown', 'mousemove'].forEach(function (t) { wrap.addEventListener(t, function (e) { e.stopPropagation(); }, { passive: true }); });
    var close = function () { wrap.remove(); };
    wrap.querySelector('.modal-x').onclick = close;
    wrap.addEventListener('click', function (e) { if (e.target === wrap) close(); });
    Array.prototype.forEach.call(wrap.querySelectorAll('[data-s]'), function (s) {
      s.onmouseenter = function () { wrap.querySelector('.tip-win').textContent = 'A ' + s.dataset.s + ' stake returns ' + Math.round(+s.dataset.s * (1 + o[0] / o[1])) + ' if it wins.'; };
      s.onclick = function () {
        var m = wrap.querySelector('.dmsg'); m.textContent = 'Placing…';
        fetch(BASE + 'api/bet', { method: 'POST', headers: HDR, body: JSON.stringify({ date: window.TIP_DATE, market: b.dataset.m, option: b.dataset.o, stake: +s.dataset.s }) })
          .then(function (r) { return r.json(); }).then(function (res) { m.textContent = res.message || ''; if (res.ok) { load(); setTimeout(close, 1400); } })
          .catch(function () { m.textContent = 'Couldn\'t reach the bookie — try again.'; });
      };
    });
  }, true);
  load();
})();
