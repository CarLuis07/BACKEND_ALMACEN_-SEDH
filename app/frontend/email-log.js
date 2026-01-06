// email-log.js
// Módulo para mostrar historial de envíos de correo en el dashboard

document.addEventListener('DOMContentLoaded', function () {
    const logContainer = document.getElementById('email-log-container');
    if (!logContainer) return;

    fetch('/api/v1/requisiciones/email-log')
        .then(res => res.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                logContainer.innerHTML = '<p>No hay registros de correo.</p>';
                return;
            }
            let html = `<table border="1" style="width:100%;font-size:14px"><thead><tr>
                <th>Fecha</th><th>Destinatario</th><th>Asunto</th><th>Estado</th><th>Error</th></tr></thead><tbody>`;
            for (const row of data) {
                html += `<tr>
                    <td>${row.fecha_envio ? row.fecha_envio.replace('T',' ').slice(0,19) : ''}</td>
                    <td>${row.destinatario}</td>
                    <td>${row.asunto}</td>
                    <td style="color:${row.estado==='enviado'?'green':'red'}">${row.estado}</td>
                    <td>${row.error ? row.error : ''}</td>
                </tr>`;
            }
            html += '</tbody></table>';
            logContainer.innerHTML = html;
        })
        .catch(err => {
            logContainer.innerHTML = `<p>Error al cargar historial: ${err}</p>`;
        });
});
