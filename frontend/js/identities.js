document.addEventListener("DOMContentLoaded", async () => {
    const tbody = document.getElementById("identities-tbody");
    
    async function loadIdentities() {
        try {
            const data = await apiRequest('/api/identities/');
            const results = data.results || data;
            tbody.innerHTML = '';
            if (results.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No identities found.</td></tr>';
                return;
            }
            results.forEach(id => {
                let badgeClass = 'badge-green';
                if(id.role === 'admin') badgeClass = 'badge-blue';
                else if(id.role === 'auditor') badgeClass = 'badge-yellow';

                tbody.innerHTML += `
                    <tr>
                        <td>${id.did || id.id}</td>
                        <td>${id.username}</td>
                        <td>${id.email}</td>
                        <td><span class="badge ${badgeClass}">${id.role}</span></td>
                        <td>${id.is_active ? 'Active' : 'Inactive'}</td>
                        <td>
                            <button class="btn btn-outline" style="padding:4px 8px; font-size:0.8rem;">Edit</button>
                        </td>
                    </tr>
                `;
            });
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="6" class="error-msg">Error loading identities: ${err.message}</td></tr>`;
        }
    }

    loadIdentities();

    const modal = document.getElementById("identity-modal");
    const btnAdd = document.getElementById("btn-add-identity");
    const btnClose = document.getElementById("btn-close-modal");
    const form = document.getElementById("identity-form");

    if (btnAdd) btnAdd.onclick = () => modal.style.display = "flex";
    if (btnClose) btnClose.onclick = () => modal.style.display = "none";
    window.onclick = (e) => { if (e.target == modal) modal.style.display = "none"; }

    if (form) {
        form.onsubmit = async (e) => {
            e.preventDefault();
            const payload = {
                username: document.getElementById("id-username").value,
                email: document.getElementById("id-email").value,
                role: document.getElementById("id-role").value
            };
            try {
                await apiRequest('/api/identities/', { method: 'POST', body: payload });
                modal.style.display = "none";
                form.reset();
                loadIdentities();
            } catch (err) {
                alert("Error: " + err.message);
            }
        };
    }
});
