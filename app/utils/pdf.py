"""
Utilidades para generar PDFs de requisiciones
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from io import BytesIO
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def generar_pdf_requisicion(
    cod_requisicion: str,
    solicitante: str,
    fecha_solicitud: str,
    dependencia: str,
    productos: List[Dict[str, Any]],
    observaciones_empleado: Optional[str] = None,
    observaciones_almacen: Optional[str] = None,
    jefe_aprobador: Optional[str] = None,
    almacen_aprobador: Optional[str] = None,
    numero_historial: Optional[str] = None,
    fecha_entrega: Optional[str] = None,
    estado: str = "COMPLETADO"
) -> bytes:
    """
    Genera un PDF con los detalles de una requisición.
    
    Args:
        cod_requisicion: Código de la requisición (ej: UIT-007-2026)
        solicitante: Nombre del empleado que solicitó
        fecha_solicitud: Fecha en que se creó la requisición
        dependencia: Nombre de la dependencia
        productos: Lista de dicts con {descripcion, cantidad, unidad, precio_unitario, total}
        observaciones_empleado: Observaciones del solicitante
        observaciones_almacen: Observaciones del almacén
        jefe_aprobador: Nombre del jefe que aprobó
        almacen_aprobador: Nombre del empleado de almacén que procesó
        numero_historial: Número de historial/proceso
        fecha_entrega: Fecha de entrega/finalización
        estado: Estado actual de la requisición
    
    Returns:
        bytes: Contenido del PDF
    """
    try:
        buffer = BytesIO()
        
        # Configurar documento
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            spaceBefore=6,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            spaceAfter=4
        )
        
        # Encabezado
        elements.append(Paragraph("REPORTE DE REQUISICIÓN COMPLETADA", title_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Información general
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        info_general = [
            ['INFORMACIÓN GENERAL', ''],
            [f'Código de Requisición:', cod_requisicion],
            [f'Estado:', f'<b>{estado}</b>'],
            [f'Número de Historial:', numero_historial or 'N/A'],
            [f'Fecha de Solicitud:', fecha_solicitud],
            [f'Fecha de Finalización:', fecha_entrega or fecha_generacion],
            [f'Generado:', fecha_generacion],
        ]
        
        table_info = Table(info_general, colWidths=[2*inch, 4.5*inch])
        table_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
        ]))
        elements.append(table_info)
        elements.append(Spacer(1, 0.15*inch))
        
        # Datos del solicitante
        elements.append(Paragraph("SOLICITANTE Y DEPENDENCIA", heading_style))
        
        solicitante_data = [
            [f'Nombre:', solicitante],
            [f'Dependencia:', dependencia],
        ]
        
        if observaciones_empleado:
            solicitante_data.append([f'Observaciones Solicitante:', observaciones_empleado])
        
        table_solicitante = Table(solicitante_data, colWidths=[1.5*inch, 5*inch])
        table_solicitante.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#F9F9F9')])
        ]))
        elements.append(table_solicitante)
        elements.append(Spacer(1, 0.15*inch))
        
        # Tabla de productos
        elements.append(Paragraph("PRODUCTOS SOLICITADOS", heading_style))
        
        # Construir encabezados de tabla
        productos_data = [
            ['Descripción', 'Cantidad', 'Unidad', 'Precio Unit.', 'Total']
        ]
        
        total_general = 0
        for producto in productos:
            desc = producto.get('descripcion', 'N/A')
            cant = str(producto.get('cantidad', 0))
            unidad = producto.get('unidad', '')
            precio_unit = f"${producto.get('precio_unitario', 0):,.2f}"
            total = float(producto.get('total', 0))
            total_general += total
            productos_data.append([
                desc,
                cant,
                unidad,
                precio_unit,
                f"${total:,.2f}"
            ])
        
        # Agregar fila de total
        productos_data.append(['', '', '', 'TOTAL:', f"${total_general:,.2f}"])
        
        table_productos = Table(productos_data, colWidths=[2.5*inch, 1*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table_productos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -2), 9),
            ('ALIGN', (1, 1), (-1, -2), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E7E6E6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('ALIGN', (3, -1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        elements.append(table_productos)
        elements.append(Spacer(1, 0.15*inch))
        
        # Aprobaciones
        elements.append(Paragraph("APROBACIONES Y PROCESAMIENTO", heading_style))
        
        aprobaciones_data = [
            ['Rol', 'Aprobador'],
        ]
        
        if jefe_aprobador:
            aprobaciones_data.append(['Jefe Inmediato:', jefe_aprobador])
        
        if almacen_aprobador:
            aprobaciones_data.append(['Empleado Almacén:', almacen_aprobador])
        
        if observaciones_almacen:
            aprobaciones_data.append(['Observaciones Almacén:', observaciones_almacen])
        
        table_aprobaciones = Table(aprobaciones_data, colWidths=[2*inch, 5*inch])
        table_aprobaciones.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F9F9F9')])
        ]))
        elements.append(table_aprobaciones)
        elements.append(Spacer(1, 0.2*inch))
        
        # Pie de página
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph(
            "Este documento fue generado automáticamente por el Sistema de Gestión de Requisiciones.",
            footer_style
        ))
        elements.append(Paragraph(
            f"Líneas: {len(productos)} | Total: ${total_general:,.2f}",
            footer_style
        ))
        
        # Construir PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    except Exception as e:
        logger.error(f"Error generando PDF: {str(e)}")
        raise
