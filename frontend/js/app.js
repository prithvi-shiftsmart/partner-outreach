async function init() {
    try {
        const resp = await fetch('/api/health');
        const data = await resp.json();
        document.getElementById('status').textContent = `API connected — ${data.conversations} conversations tracked`;
    } catch (e) {
        document.getElementById('status').textContent = 'API not reachable';
    }
}
init();
