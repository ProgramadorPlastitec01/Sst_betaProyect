/**
 * Offline Outbox
 * Bandeja de salida local (IndexedDB) para formularios que no se pudieron
 * enviar por falta de red. Guarda el payload completo (campos + archivos)
 * y permite reintentarlo más tarde sin perder datos.
 *
 * Nota importante: FormData NO es clonable por IndexedDB (structured clone
 * no lo soporta). Por eso cada entrada guarda `formEntries` como un array
 * de pares [clave, valor-o-archivo] en vez del objeto FormData crudo.
 */
(function () {
    var DB_NAME = 'sst_offline_db';
    var DB_VERSION = 1;
    var STORE_NAME = 'outbox';

    var dbPromise = null;

    function openDB() {
        if (dbPromise) return dbPromise;
        dbPromise = new Promise(function (resolve, reject) {
            var request = indexedDB.open(DB_NAME, DB_VERSION);
            request.onupgradeneeded = function (event) {
                var db = event.target.result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    db.createObjectStore(STORE_NAME, { keyPath: 'clientUuid' });
                }
            };
            request.onsuccess = function (event) { resolve(event.target.result); };
            request.onerror = function (event) { reject(event.target.error); };
        });
        return dbPromise;
    }

    function withStore(mode, callback) {
        return openDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(STORE_NAME, mode);
                var store = tx.objectStore(STORE_NAME);
                var result = callback(store);
                tx.oncomplete = function () { resolve(result); };
                tx.onerror = function () { reject(tx.error); };
            });
        });
    }

    function put(record) {
        return withStore('readwrite', function (store) {
            store.put(record);
        });
    }

    function remove(clientUuid) {
        return withStore('readwrite', function (store) {
            store.delete(clientUuid);
        });
    }

    function markFailed(clientUuid, errorMessage) {
        return getAll().then(function (records) {
            var record = records.find(function (r) { return r.clientUuid === clientUuid; });
            if (!record) return;
            record.status = 'failed';
            record.lastError = errorMessage || 'Error de validación';
            return put(record);
        });
    }

    function getAll() {
        return openDB().then(function (db) {
            return new Promise(function (resolve, reject) {
                var tx = db.transaction(STORE_NAME, 'readonly');
                var store = tx.objectStore(STORE_NAME);
                var request = store.getAll();
                request.onsuccess = function () { resolve(request.result || []); };
                request.onerror = function () { reject(request.error); };
            });
        });
    }

    function counts() {
        return getAll().then(function (records) {
            var pending = records.filter(function (r) { return r.status === 'pending'; }).length;
            var failed = records.filter(function (r) { return r.status === 'failed'; }).length;
            return { pending: pending, failed: failed };
        });
    }

    function buildFormData(formEntries) {
        var fd = new FormData();
        formEntries.forEach(function (pair) {
            fd.append(pair[0], pair[1]);
        });
        return fd;
    }

    // ── Banner persistente ──────────────────────────────────────────────
    function renderBanner() {
        var banner = document.getElementById('offline-banner');
        if (!banner) return;
        counts().then(function (c) {
            if (c.pending === 0 && c.failed === 0) {
                banner.style.display = 'none';
                banner.innerHTML = '';
                return;
            }
            banner.style.display = 'block';
            var parts = [];
            if (c.pending > 0) {
                parts.push('📶 ' + c.pending + ' inspección(es) guardada(s) en este dispositivo (Esperando RED)');
            }
            if (c.failed > 0) {
                parts.push(c.failed + ' con error de datos, requiere revisión');
            }
            banner.innerHTML =
                '<div style="display:flex; align-items:center; justify-content:space-between; gap:12px; padding:8px 20px;">' +
                '  <span>' + parts.join(' · ') + '</span>' +
                '  <button type="button" id="offline-banner-toggle" style="background:none; border:1px solid #664d03; border-radius:4px; padding:2px 10px; font-size:0.8rem; color:#664d03; cursor:pointer;">Ver detalle</button>' +
                '</div>' +
                '<div id="offline-banner-list" style="display:none; padding:0 20px 10px;"></div>';

            var toggle = document.getElementById('offline-banner-toggle');
            if (toggle) {
                toggle.addEventListener('click', function () { toggleList(); });
            }
        });
    }

    function toggleList() {
        var list = document.getElementById('offline-banner-list');
        if (!list) return;
        if (list.style.display === 'none') {
            getAll().then(function (records) {
                var itemStyle = 'display:flex; align-items:center; justify-content:space-between; gap:12px; padding:4px 0; border-top:1px solid #ffe69c;';
                list.innerHTML = records.map(function (r) {
                    var statusLabel = r.status === 'failed'
                        ? ('Error: ' + (r.lastError || 'dato inválido'))
                        : 'Pendiente de red';
                    return (
                        '<div style="' + itemStyle + '">' +
                        '  <span>' + (r.moduleLabel || 'Inspección') + ' — ' + statusLabel + '</span>' +
                        (r.status === 'failed'
                            ? '<button type="button" data-discard="' + r.clientUuid + '" style="background:none; border:1px solid #664d03; border-radius:4px; padding:2px 8px; font-size:0.75rem; color:#664d03; cursor:pointer;">Descartar</button>'
                            : '') +
                        '</div>'
                    );
                }).join('') || ('<div style="' + itemStyle + '">Sin pendientes</div>');

                list.querySelectorAll('[data-discard]').forEach(function (btn) {
                    btn.addEventListener('click', function () {
                        remove(btn.getAttribute('data-discard')).then(renderBanner);
                    });
                });
                list.style.display = 'block';
            });
        } else {
            list.style.display = 'none';
        }
    }

    window.OfflineOutbox = {
        put: put,
        remove: remove,
        markFailed: markFailed,
        getAll: getAll,
        counts: counts,
        buildFormData: buildFormData,
        renderBanner: renderBanner
    };

    document.addEventListener('DOMContentLoaded', renderBanner);
})();
