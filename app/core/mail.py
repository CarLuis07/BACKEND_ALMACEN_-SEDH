import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Tuple
from app.core.config import settings


def send_email(
    to_email: str,
    subject: str,
    body_text: str,
    body_html: Optional[str] = None,
    attachments: Optional[list[tuple[str, bytes, str]]] = None,
    inline_images: Optional[dict[str, bytes]] = None,
) -> Tuple[str, Optional[str]]:
    """
    Envía un correo soportando texto plano y HTML, con adjuntos e imágenes embebidas.
    - body_text: contenido en texto plano (recomendado siempre)
    - body_html: contenido en HTML (opcional)
    - attachments: lista de tuplas (filename, file_bytes, mime_type)
    - inline_images: dict {cid_name: image_bytes} para insertar con <img src="cid:cid_name">.
    Retorna (estado, error).
    """
    # Validar configuración SMTP
    if not settings.SMTP_SERVER or not settings.SMTP_USERNAME:
        return "error", "SMTP no configurado (faltan SMTP_SERVER o SMTP_USERNAME)"

    msg = EmailMessage()
    msg["From"] = settings.SMTP_USERNAME
    msg["To"] = to_email
    msg["Subject"] = subject
    # Contenido en texto
    msg.set_content(body_text)
    # Contenido HTML opcional
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    # Imágenes embebidas (inline)
    if inline_images:
        # Se adjuntan a la parte HTML; los clientes usan cid: para resolver
        for cid_name, img_bytes in inline_images.items():
            if not img_bytes:
                continue
            # Adjuntar a mensaje como imagen inline
            msg.get_payload()[-1].add_related(
                img_bytes,
                maintype="image",
                subtype="png",
                cid=make_msgid(cid_name),
            )

    # Adjuntos
    if attachments:
        for filename, file_bytes, mime_type in attachments:
            if not file_bytes:
                continue
            maintype, subtype = (mime_type.split("/", 1) + ["octet-stream"])[:2]
            msg.add_attachment(file_bytes, maintype=maintype, subtype=subtype, filename=filename)

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()  # Gmail requiere TLS
            server.ehlo()
            
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            response = server.send_message(msg)
        
        # smtplib devuelve dict de fallos; vacío significa todos enviados
        if response:
            return "error", str(response)
        return "enviado", None
    except Exception as e:
        return "error", str(e)
