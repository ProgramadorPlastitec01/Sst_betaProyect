/**
 * Offline-first form submission.
 * Intercepta el submit de un formulario e intenta enviarlo por fetch. Si no
 * hay red (o se corta a mitad del envío), guarda el payload completo
 * (incluyendo archivos de evidencia) en el outbox local y lo reintenta
 * automáticamente cuando vuelva la conexión — sin que el usuario tenga que
 * hacer nada manual.
 */
(function () {
    var FETCH_TIMEOUT_MS = 9000;

    function uuidv4() {
        if (window.crypto && window.crypto.randomUUID) {
            return window.crypto.randomUUID();
        }
        // Fallback para navegadores sin crypto.randomUUID
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            var r = Math.random() * 16 | 0;
            var v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function ensureClientUuid(form) {
        var input = form.querySelector('input[name="client_uuid"]');
        if (!input) return null;
        if (!input.value) {
            input.value = uuidv4();
        }
        return input.value;
    }

    function saveToOutbox(form, clientUuid, moduleLabel) {
        var formData = new FormData(form);
        var formEntries = Array.from(formData.entries());
        return window.OfflineOutbox.put({
            clientUuid: clientUuid,
            url: form.action || window.location.href,
            moduleLabel: moduleLabel || document.title,
            formEntries: formEntries,
            createdAt: Date.now(),
            attempts: 0,
            status: 'pending',
            lastError: null
        });
    }

    function showOfflineNotice() {
        if (window.toastr) {
            toastr.info('Guardado en dispositivo (Esperando RED). Se enviará automáticamente al recuperar la conexión.', '', { timeOut: 6000 });
        }
        window.OfflineOutbox.renderBanner();
    }

    /**
     * @param {HTMLFormElement} form
     * @param {Object} options
     * @param {string} options.moduleLabel - texto descriptivo para el outbox/banner (ej. "Extintor")
     * @param {string} options.fallbackUrl - a dónde navegar si el envío queda pendiente (ej. lista del módulo)
     */
    window.submitFormOffline = function (form, options) {
        options = options || {};
        var clientUuid = ensureClientUuid(form);
        var formData = new FormData(form);

        var controller = ('AbortController' in window) ? new AbortController() : null;
        var timeoutId = controller ? setTimeout(function () { controller.abort(); }, FETCH_TIMEOUT_MS) : null;

        fetch(form.action || window.location.href, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            signal: controller ? controller.signal : undefined
        }).then(function (response) {
            if (timeoutId) clearTimeout(timeoutId);

            if (response.status === 401) {
                // Sesión expirada: no se pierde el dato, se guarda igual.
                if (clientUuid) saveToOutbox(form, clientUuid, options.moduleLabel);
                if (window.toastr) {
                    toastr.warning('Tu sesión expiró. Lo diligenciado quedó guardado en este dispositivo — inicia sesión de nuevo para sincronizarlo.', '', { timeOut: 8000 });
                }
                window.location.href = '/accounts/login/';
                return;
            }

            if (response.ok) {
                response.json().then(function (data) {
                    window.location.href = data.redirect_url || (options.fallbackUrl || '/');
                });
                return;
            }

            // El servidor respondió (no es problema de red) pero rechazó los
            // datos: mismo comportamiento que un submit nativo con errores.
            response.text().then(function (html) {
                document.open();
                document.write(html);
                document.close();
            });
        }).catch(function () {
            // No llegó respuesta: red caída o se cortó a mitad del envío.
            if (timeoutId) clearTimeout(timeoutId);
            if (!clientUuid) {
                if (window.toastr) toastr.error('No se pudo guardar: formulario sin identificador local.');
                return;
            }
            saveToOutbox(form, clientUuid, options.moduleLabel).then(function () {
                // Importante: NO navegar aquí. Estamos offline, así que cualquier
                // navegación de página completa (incluso al "fallbackUrl") fallará
                // con la pantalla nativa del navegador y tapará este aviso. Nos
                // quedamos en la página ya cargada (no requiere red) y dejamos
                // el formulario deshabilitado para evitar un doble envío.
                showOfflineNotice();
                var submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) submitBtn.disabled = true;
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    };
})();
