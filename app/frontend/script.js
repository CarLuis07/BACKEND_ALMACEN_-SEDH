document.addEventListener("DOMContentLoaded", function () {
    // API Base URL - Detecta automáticamente el host
    const API_BASE_URL = `${window.location.protocol}//${window.location.host}/api/v1`;
    
    
    document.getElementById("login-form").addEventListener("submit", async function (e) {
        e.preventDefault(); // evita recargar la página

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const resultDiv = document.getElementById("result");
        resultDiv.innerHTML = "Procesando...";

        try {
            const response = await fetch(`${API_BASE_URL}/accesos/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem("token", data.access_token);
                resultDiv.innerHTML = "<p class='success'>Login exitoso ✅ Redirigiendo...</p>";

                // Verificar que el token funcione
                const meResponse = await fetch(`${API_BASE_URL}/accesos/me`, {
                    headers: {
                        "Authorization": `Bearer ${data.access_token}`
                    }
                });

                if (meResponse.ok) {
                    const meData = await meResponse.json();
                    // Mostrar mensaje de bienvenida brevemente antes de redirigir
                    resultDiv.innerHTML = `<p class='success'>¡Bienvenido ${meData.email}! Accediendo al sistema...</p>`;
                    
                    // Inicializar sistema de carrito individual
                    if (window.cartManager) {
                        window.cartManager.currentUser = meData;
                        await window.cartManager.migrateOldCarts();
                    }
                    
                    // Redirigir al dashboard después de 1.5 segundos
                    setTimeout(() => {
                        window.location.href = "/dashboard";
                    }, 1500);
                } else {
                    resultDiv.innerHTML = `<p class="error">Error al validar credenciales</p>`;
                    localStorage.removeItem("token");
                }

            } else {
                const errorData = await response.json();
                resultDiv.innerHTML = `<p class="error">Error: ${errorData.detail || 'Error en login'}</p>`;
            }
        } catch (err) {
            resultDiv.innerHTML = `<p class="error">Error al conectar con el servidor</p>`;
            console.error(err);
        }
    });

    // Función global de logout que limpia los carritos individuales
    window.logout = function() {
        if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
            // Limpiar carritos del usuario actual
            if (window.clearUserCarts) {
                window.clearUserCarts();
            }
            
            // Limpiar token y datos de sesión
            localStorage.removeItem('token');
            
            // Redirigir al login
            window.location.href = '/login';
        }
    };
});
