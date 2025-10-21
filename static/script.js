function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-link");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

document.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('api-key');
    const resultContainer = document.getElementById('result-container');
    const resultOutput = document.getElementById('result-output');
    const spinner = document.getElementById('spinner');

    // --- Sliders ---
    const creativeSlider = document.getElementById('creative-strength');
    const creativeValue = document.getElementById('creative-value');
    const controlSlider = document.getElementById('control-strength');
    const controlValue = document.getElementById('control-value');

    creativeSlider.oninput = () => creativeValue.textContent = creativeSlider.value;
    controlSlider.oninput = () => controlValue.textContent = controlSlider.value;

    // --- Form Handlers ---
    document.getElementById('t2i-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        setLoading(true);
        const payload = {
            prompt: document.getElementById('t2i-prompt').value,
            model: document.getElementById('t2i-model').value,
            size: document.getElementById('t2i-size').value,
            n: 1,
            response_format: "url"
        };
        try {
            const response = await fetch('/v1/images/generations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKeyInput.value}`
                },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            handleResult(result, 'image');
        } catch (error) {
            handleError(error);
        } finally {
            setLoading(false);
        }
    });

    document.getElementById('i2i-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        setLoading(true);
        const formData = new FormData();
        formData.append('image', document.getElementById('i2i-image').files[0]);
        formData.append('prompt', document.getElementById('i2i-prompt').value);
        formData.append('creative_strength', creativeSlider.value);
        formData.append('control_strength', controlSlider.value);

        try {
            const response = await fetch('/v1/images/edits', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${apiKeyInput.value}` },
                body: formData
            });
            const result = await response.json();
            handleResult(result, 'image');
        } catch (error) {
            handleError(error);
        } finally {
            setLoading(false);
        }
    });

    document.getElementById('i2v-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        setLoading(true);
        const formData = new FormData();
        formData.append('image', document.getElementById('i2v-image').files[0]);

        try {
            const response = await fetch('/v1/video/generations', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${apiKeyInput.value}` },
                body: formData
            });
            const result = await response.json();
            handleResult(result, 'video');
        } catch (error) {
            handleError(error);
        } finally {
            setLoading(false);
        }
    });

    // --- Helper Functions ---
    function setLoading(isLoading) {
        spinner.classList.toggle('hidden', !isLoading);
        resultContainer.classList.remove('hidden');
        if (isLoading) {
            resultOutput.innerHTML = '';
        }
    }

    function handleResult(result, type) {
        if (result.detail) {
            handleError(new Error(result.detail));
            return;
        }
        const url = result.data[0].url;
        if (type === 'image') {
            resultOutput.innerHTML = `<img src="${url}" alt="Generated Image"><p><a href="${url}" target="_blank">${url}</a></p>`;
        } else if (type === 'video') {
            resultOutput.innerHTML = `<video controls src="${url}"></video><p><a href="${url}" target="_blank">${url}</a></p>`;
        }
    }

    function handleError(error) {
        resultOutput.innerHTML = `<div class="error">错误: ${error.message}</div>`;
    }
});