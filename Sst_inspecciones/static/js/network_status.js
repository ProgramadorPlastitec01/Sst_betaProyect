/**
 * Network Status Indicator
 * Detecta si el navegador puede realmente alcanzar el servidor (no solo si
 * el adaptador de red del sistema operativo está "conectado") y actualiza
 * el badge "Estado Red" del header. No requiere acción del usuario.
 */
(function () {
    var PING_URL = '/ping/';
    var PING_INTERVAL_MS = 12000;
    var PING_TIMEOUT_MS = 4000;

    var isOnline = true;
    var checking = false;

    function setState(online) {
        var changed = online !== isOnline;
        isOnline = online;
        renderBadge();
        if (changed) {
            document.dispatchEvent(new CustomEvent('app:network-change', { detail: { online: online } }));
        }
    }

    function renderBadge() {
        var dot = document.getElementById('network-status-dot');
        var label = document.getElementById('network-status-label');
        if (!dot || !label) return;
        if (isOnline) {
            dot.style.backgroundColor = '#28a745';
            label.textContent = 'Conectado';
        } else {
            dot.style.backgroundColor = '#dc3545';
            label.textContent = 'Sin conexión';
        }
    }

    function check() {
        if (checking) return;
        checking = true;
        var controller = ('AbortController' in window) ? new AbortController() : null;
        var timeoutId = controller ? setTimeout(function () { controller.abort(); }, PING_TIMEOUT_MS) : null;

        fetch(PING_URL, {
            method: 'GET',
            cache: 'no-store',
            credentials: 'same-origin',
            signal: controller ? controller.signal : undefined
        }).then(function (response) {
            setState(response.ok || response.status === 204);
        }).catch(function () {
            setState(false);
        }).finally(function () {
            if (timeoutId) clearTimeout(timeoutId);
            checking = false;
        });
    }

    // Señales auxiliares del navegador: no son definitivas (reflejan el
    // adaptador de red, no si el servidor es alcanzable), pero sirven para
    // reaccionar de inmediato en vez de esperar al siguiente ping.
    window.addEventListener('online', check);
    window.addEventListener('offline', function () { setState(false); });

    document.addEventListener('DOMContentLoaded', function () {
        renderBadge();
        check();
        setInterval(check, PING_INTERVAL_MS);
    });

    window.AppNetwork = {
        isOnline: function () { return isOnline; },
        checkNow: check
    };
})();
