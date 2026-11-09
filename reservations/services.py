from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
# Opcional si generas PDF:
# from weasyprint import HTML

def enviar_comprobante_email(reserva):
    """
    Renderiza el comprobante y lo envía por correo al cliente.
    """
    subject = f"Confirmación y Comprobante de Reserva #{reserva.pk}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [reserva.cliente.email]

    # 1. Renderizar contenido HTML
    context = {'reserva': reserva}
    html_content = render_to_string('emails/comprobante.html', context)
    text_content = strip_tags(html_content)  # Versión texto sin HTML para clientes de correo básicos

    # 2. Crear objeto del correo
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list
    )
    email.attach_alternative(html_content, "text/html")

    # 3. (OPCIONAL) Adjuntar PDF generado al vuelo con WeasyPrint
    # pdf_bytes = HTML(string=html_content).write_pdf()
    # email.attach(
    #     filename=f"Comprobante_{reserva.codigo}.pdf",
    #     content=pdf_bytes,
    #     mimetype="application/pdf"
    # )

    # 4. Enviar correo
    email.send(fail_silently=False)