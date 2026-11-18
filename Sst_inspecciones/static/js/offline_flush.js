/**
 * Offline Outbox Flush
 * Reintenta automáticamente, sin acción del usuario, cada formulario
 * guardado en el outbox local cuando hay evidencia real de que volvió la
 * red (evento 'online', cambio de estado de network_status.js, o carga de
 * cualquier página). Usa Web Locks (si el navegador lo soporta) para que
 * dos pestañas no reintenten el mismo envío a la vez.
 */
(function () {
    function refreshCsrf(formEntries) {
        var token = (typeof getCSRFToken === 'function') ? getCSRFToken() : null;
        if (!token) return formEntries;
        return formEntries.map(function (pair) {
            return pair[0] === 'csrfmiddlewaretoken' ? [pair[0], token] : pair;
        });
    }

    function attempt(record) {
        var formEntries = refreshCsrf(record.formEntries);
        var formData = window.OfflineOutbox.buildFormData(formEntries);

        return fetch(record.url, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (response) {
            if (response.ok) {
                return response.json().then(function () {
                    return window.OfflineOutbox.remove(record.clientUuid).then(function () {
                        if (window.toastr) {
                            toastr.success((record.moduleLabel || 'Inspección') + ' sincronizada correctamente.');
                        }
                        return 'synced';
                    });
                });
            }
            if (response.status === 401) {
                // Sesión expirada: se deja pendiente, se reintentará tras volver a loguear.
                return 'auth_required';
            }
            // Dato rechazado por el servidor (no es problema de red): no
            // reintentar indefinidamente, queda visible para revisión manual.
            return window.OfflineOutbox.markFailed(record.clientUuid, 'El servidor rechazó los datos (revisar el registro)').then(function () {
                return 'failed';
            });
        }).catch(function () {
            // Sigue sin red: se deja pendiente para el próximo intento.
            return 'retry_later';
        });
    }

    function flushAll() {
        return window.OfflineOutbox.getAll().then(function (records) {
            var pending = records.filter(function (r) { return r.status === 'pending'; });
            if (pending.length === 0) return;

            var chain = Promise.resolve();
            var sawAuthRequired = false;
            pending.forEach(function (record) {
                chain = chain.then(function () {
                    if (sawAuthRequired) return; // evita martillar al servidor si ya sabemos que la sesión expiró
                    return attempt(record).then(function (result) {
                        if (result === 'auth_required') sawAuthRequired = true;
                    });
                });
            });
            return chain.then(function () {
                window.OfflineOutbox.renderBanner();
            });
        });
    }

    function flushNow() {
        if (window.navigator && navigator.locks && navigator.locks.request) {
            navigator.locks.request('offline-outbox-flush', { ifAvailable: true }, function (lock) {
                if (!lock) return; // otra pestaña ya está sincronizando
                return flushAll();
            });
        } else {
            flushAll();
        }
    }

    window.addEventListener('online', flushNow);
    document.addEventListener('app:network-change', function (e) {
        if (e.detail && e.detail.online) flushNow();
    });
    document.addEventListener('DOMContentLoaded', flushNow);

    window.OfflineFlush = { flushNow: flushNow };
})();
