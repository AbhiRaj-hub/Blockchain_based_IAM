document.addEventListener("DOMContentLoaded", () => {
    // Auth guard for non-login pages
    if (!window.location.pathname.endsWith('login.html') && !window.location.pathname.endsWith('index.html')) {
        const token = getToken();
        if (!token) {
            window.location.href = "login.html";
        }
    }

    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const showRegister = document.getElementById("show-register");
    const showLogin = document.getElementById("show-login");
    const subtitle = document.getElementById("form-subtitle");
    
    if (showRegister) {
        showRegister.addEventListener("click", (e) => {
            e.preventDefault();
            loginForm.style.display = "none";
            registerForm.style.display = "block";
            subtitle.innerText = "Create an account";
        });
    }
    
    if (showLogin) {
        showLogin.addEventListener("click", (e) => {
            e.preventDefault();
            registerForm.style.display = "none";
            loginForm.style.display = "block";
            subtitle.innerText = "Login to your account";
        });
    }

    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("login-username").value;
            const password = document.getElementById("login-password").value;
            const errorDiv = document.getElementById("login-error");
            errorDiv.innerText = "";
            try {
                const res = await fetch(`${API_BASE}/api/auth/token/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                if (!res.ok) throw new Error("Invalid credentials");
                const data = await res.json();
                setTokens(data.access, data.refresh);
                window.location.href = "dashboard.html";
            } catch (err) {
                errorDiv.innerText = err.message;
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const username = document.getElementById("reg-username").value;
            const email = document.getElementById("reg-email").value;
            const password = document.getElementById("reg-password").value;
            const confirm = document.getElementById("reg-confirm").value;
            const errorDiv = document.getElementById("reg-error");
            const successDiv = document.getElementById("reg-success");
            errorDiv.innerText = "";
            successDiv.innerText = "";
            
            if (password !== confirm) {
                errorDiv.innerText = "Passwords do not match";
                return;
            }
            try {
                const res = await fetch(`${API_BASE}/api/auth/register/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, email, password })
                });
                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(JSON.stringify(data));
                }
                successDiv.innerText = "Registration successful! Please login.";
                setTimeout(() => { showLogin.click(); }, 2000);
            } catch (err) {
                errorDiv.innerText = "Registration failed. " + err.message;
            }
        });
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", (e) => {
            e.preventDefault();
            clearTokens();
        });
    }
});
