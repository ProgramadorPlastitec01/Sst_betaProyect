/**
 * Evidence Management System
 * Handles AJAX upload, deletion, and preview of photographic evidence.
 */

// Global function to open preview
window.openEvidencePreview = function (url, description) {
    const modal = document.getElementById('evidencePreviewModal');
    const img = document.getElementById('evidencePreviewImage');
    const desc = document.getElementById('evidencePreviewDesc');

    if (modal && img) {
        img.src = url;
        desc.textContent = description || 'Sin descripción';
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scroll
    }
};

// Global function to close preview
window.closeEvidencePreview = function () {
    const modal = document.getElementById('evidencePreviewModal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
};

// Function to get CSRF token
function getCSRFToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue;
}

// Global upload function
window.uploadEvidence = function (input, contentTypeId, objectId) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];
    if (file.size > 5 * 1024 * 1024) {
        toastr.error('La imagen excede los 5MB');
        input.value = '';
        return;
    }

    const containerId = objectId ? `evidence-container-${contentTypeId}-${objectId}` : `evidence-container-${contentTypeId}-`;
    const container = document.getElementById(containerId);
    const addBtn = input.closest('.evidence-add-btn');

    const isLocal = !objectId || objectId === 'None' || objectId === '' || isNaN(parseInt(objectId, 10));

    // Local mode: if no objectId exists (record hasn't been saved yet)
    if (isLocal) {
        const reader = new FileReader();
        const tempId = 'temp_' + Date.now() + '_' + Math.floor(Math.random() * 1000);

        reader.onload = function (e) {
            const dataUrl = e.target.result;
            const wrapper = document.createElement('div');
            wrapper.className = 'evidence-wrapper pending-evidence';
            wrapper.setAttribute('id', 'wrapper_' + tempId);
            wrapper.onclick = () => openEvidencePreview(dataUrl, 'Nueva evidencia (sin guardar)');
            wrapper.innerHTML = `
                <img src="${dataUrl}" alt="Evidence">
                <div class="evidence-remove" onclick="event.stopPropagation(); removePendingEvidence('${tempId}')">&times;</div>
            `;

            if (container && addBtn) {
                container.insertBefore(wrapper, addBtn);
            }
        };

        // Clone the input to leave a fresh one in the button
        const clonedInput = input.cloneNode(true);
        clonedInput.value = ''; // clear for next pick
        input.parentNode.replaceChild(clonedInput, input);

        let inputName = `pending_evidences_${contentTypeId}`;
        if (objectId && objectId !== 'None') {
            inputName += `_${objectId}`; // e.g., pending_evidences_15_items-0
        }

        // Modify the original input to be hidden and appended to the form
        input.name = inputName;
        input.id = tempId;
        input.style.display = 'none';

        if (clonedInput.form) {
            clonedInput.form.appendChild(input);
        } else {
            const form = container.closest('form');
            if (form) form.appendChild(input);
        }

        reader.readAsDataURL(file);
        return;
    }

    // Remote mode: upload immediately
    const loadingElem = document.createElement('div');
    loadingElem.className = 'evidence-loading';
    loadingElem.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"></div>';

    if (addBtn) addBtn.style.display = 'none';
    if (container) container.appendChild(loadingElem);

    const formData = new FormData();
    formData.append('image', file);
    formData.append('content_type_id', contentTypeId);
    formData.append('object_id', objectId);
    formData.append('csrfmiddlewaretoken', getCSRFToken());

    fetch('/inspections/evidence/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                toastr.error(data.error);
            } else {
                const wrapper = document.createElement('div');
                wrapper.className = 'evidence-wrapper';
                wrapper.setAttribute('data-id', data.id);
                wrapper.onclick = () => openEvidencePreview(data.url, data.description);
                wrapper.innerHTML = `
                <img src="${data.url}" alt="Evidence">
                <div class="evidence-remove" onclick="event.stopPropagation(); deleteEvidence(${data.id}, this)">&times;</div>
            `;

                if (container) {
                    container.insertBefore(wrapper, loadingElem);
                    toastr.success('Imagen cargada correctamente');
                }
            }
        })
        .catch(error => {
            console.error('Error uploading evidence:', error);
            toastr.error('Error al cargar la imagen');
        })
        .finally(() => {
            if (loadingElem) loadingElem.remove();
            if (addBtn) addBtn.style.display = 'flex';
            input.value = '';
        });
};

window.removePendingEvidence = function (tempId) {
    const wrapper = document.getElementById('wrapper_' + tempId);
    if (wrapper) wrapper.remove();

    const input = document.getElementById(tempId);
    if (input) input.remove();
};

// Global delete function
window.deleteEvidence = function (id, btn) {
    if (!confirm('¿Está seguro de eliminar esta evidencia?')) return;

    const formData = new FormData();
    formData.append('csrfmiddlewaretoken', getCSRFToken());

    fetch(`/inspections/evidence/${id}/delete/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const wrapper = btn.closest('.evidence-wrapper');
                if (wrapper) {
                    wrapper.style.opacity = '0';
                    setTimeout(() => wrapper.remove(), 300);
                }
                toastr.success('Evidencia eliminada');
            } else {
                toastr.error(data.error || 'No se pudo eliminar la evidencia');
            }
        })
        .catch(error => {
            console.error('Error deleting evidence:', error);
            toastr.error('Error al eliminar la evidencia');
        });
};

// Close modal when clicking outside
window.addEventListener('click', function (event) {
    const modal = document.getElementById('evidencePreviewModal');
    if (event.target === modal) {
        closeEvidencePreview();
    }
});
