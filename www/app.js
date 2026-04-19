const moduleList = document.getElementById('module-list');
const status = document.getElementById('status');
const themeButtons = document.querySelectorAll('.theme-btn');
document.getElementById('server-url').textContent = window.location.origin;

function applyTheme(theme) {
    if (theme === 'system') {
        document.body.removeAttribute('data-theme');
    } else {
        document.body.setAttribute('data-theme', theme);
    }

    themeButtons.forEach((button) => {
        button.classList.toggle('active', button.dataset.themeChoice === theme);
    });
}

function setTheme(theme) {
    localStorage.setItem('paf-theme', theme);
    applyTheme(theme);
}

const storedTheme = localStorage.getItem('paf-theme') || 'system';
applyTheme(storedTheme);

themeButtons.forEach((button) => {
    button.addEventListener('click', () => setTheme(button.dataset.themeChoice));
});

async function loadModules() {
    status.textContent = 'Loading module list...';
    try {
        const response = await fetch('/api/modules');
        const data = await response.json();
        moduleList.innerHTML = '';

        if (!data.modules || data.modules.length === 0) {
            moduleList.innerHTML = '<li>No modules are currently registered.</li>';
        } else {
            data.modules.forEach((name) => {
                const item = document.createElement('li');
                item.textContent = name;
                moduleList.appendChild(item);
            });
        }

        status.textContent = `Found ${data.modules.length} registered module(s).`;
    } catch (error) {
        status.textContent = `Unable to load modules: ${error}`;
    }
}

async function shutdownAllModules() {
    status.textContent = 'Sending shutdown broadcast...';
    try {
        const response = await fetch('/api/shutdown', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action: 'shutdown' })
        });
        const data = await response.json();
        status.textContent = (data.message || 'Shutdown broadcast sent.') + ' Attempting to close this tab...';

        setTimeout(() => {
            window.open('', '_self');
            window.close();
        }, 300);
    } catch (error) {
        status.textContent = `Unable to send shutdown: ${error}`;
    }
}

document.getElementById('refresh-btn').addEventListener('click', loadModules);
document.getElementById('shutdown-btn').addEventListener('click', shutdownAllModules);

loadModules();
window.setInterval(loadModules, 5000);
