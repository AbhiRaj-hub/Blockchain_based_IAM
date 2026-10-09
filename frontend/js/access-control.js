document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab-btn");
    const contents = document.querySelectorAll(".tab-content");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            contents.forEach(c => c.style.display = "none");
            
            tab.classList.add("active");
            document.getElementById(`${tab.dataset.tab}-tab`).style.display = "block";
        });
    });

    // Check Access form handling
    const checkForm = document.getElementById("check-access-form");
    const checkResult = document.getElementById("check-result");
    
    if (checkForm) {
        checkForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const did = document.getElementById("check-did").value;
            const resource = document.getElementById("check-resource").value;
            const action = document.getElementById("check-action").value;
            
            try {
                const res = await apiRequest('/api/access/check/', {
                    method: 'POST',
                    body: { identity_did: did, resource: resource, action: action }
                });
                if (res.allowed) {
                    checkResult.innerHTML = `<div class="badge badge-green" style="font-size:1rem; padding:10px;">ACCESS GRANTED</div>`;
                } else {
                    checkResult.innerHTML = `<div class="badge badge-red" style="font-size:1rem; padding:10px; background:#fecaca; color:#991b1b;">ACCESS DENIED: ${res.reason || ''}</div>`;
                }
            } catch (err) {
                checkResult.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
            }
        });
    }
});
