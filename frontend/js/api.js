const API_BASE = "http://localhost:8000";

function getToken() {
    return localStorage.getItem("access_token");
}

function getRefreshToken() {
    return localStorage.getItem("refresh_token");
}

function setTokens(access, refresh) {
    if(access) localStorage.setItem("access_token", access);
    if(refresh) localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    if (!window.location.pathname.endsWith('login.html')) {
        window.location.href = "login.html";
    }
}

async function refreshToken() {
    const refresh = getRefreshToken();
    if (!refresh) {
        clearTokens();
        return false;
    }
    try {
        const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });
        if (res.ok) {
            const data = await res.json();
            setTokens(data.access, null);
            return true;
        } else {
            clearTokens();
            return false;
        }
    } catch (err) {
        clearTokens();
        return false;
    }
}

async function apiRequest(endpoint, options = {}) {
    let token = getToken();
    const headers = { ...options.headers };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    
    const config = { ...options, headers };
    if (config.body && typeof config.body !== 'string' && !(config.body instanceof FormData)) {
        config.body = JSON.stringify(config.body);
    }

    let response = await fetch(`${API_BASE}${endpoint}`, config);
    if (response.status === 401 && token) {
        const refreshed = await refreshToken();
        if (refreshed) {
            token = getToken();
            headers['Authorization'] = `Bearer ${token}`;
            response = await fetch(`${API_BASE}${endpoint}`, config);
        } else {
            clearTokens();
            throw new Error('Unauthorized');
        }
    }
    
    if (!response.ok) {
        let msg = 'API Request Failed';
        try {
            const errData = await response.json();
            msg = errData.detail || errData.error || JSON.stringify(errData);
        } catch(e) {}
        throw new Error(msg);
    }
    
    if (response.status === 204) return null;
    return response.json();
}
