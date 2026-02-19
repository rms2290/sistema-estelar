"""
Utilitários para geração de relatórios em PDF e Excel
"""
import logging
import io
import os
import tempfile
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


def format_brazilian_currency(value):
    """Formata valor como moeda brasileira"""
    if value is None:
        return 'R$ 0,00'
    
    try:
        float_value = float(value)
        if float_value == 0:
            return 'R$ 0,00'
        
        formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return str(value)


def get_logo_path():
    """Retorna o caminho da logo Estelar"""
    # Tentar encontrar a logo em diferentes formatos
    logo_paths = [
        os.path.join(settings.BASE_DIR, 'static', 'logo-estelar.png'),
        os.path.join(settings.BASE_DIR, 'static', 'logo-estelar.jpg'),
        os.path.join(settings.BASE_DIR, 'static', 'logo-estelar.svg'),
    ]
    
    for path in logo_paths:
        if os.path.exists(path):
            return path
    
    return None


def add_logo_to_story(story, para_style, width=4*cm):
    """Adiciona a logo Estelar ao story do PDF"""
    logo_path = get_logo_path()
    if logo_path and os.path.exists(logo_path):
        try:
            # Se for SVG, tentar converter usando svglib
            if logo_path.endswith('.svg'):
                try:
                    from svglib.svglib import svg2rlg
                    
                    drawing = svg2rlg(logo_path)
                    if drawing:
                        # Escalar o drawing para o tamanho desejado
                        if drawing.width > 0:
                            scale = width / drawing.width
                            drawing.width = width
                            drawing.height = drawing.height * scale
                            drawing.scale(scale, scale)
                        
                        # Adicionar o drawing diretamente ao story (ReportLab suporta isso)
                        story.append(drawing)
                        story.append(Spacer(1, 10))
                        return True
                    else:
                        return False
                except (ImportError, Exception):
                    # Se svglib não estiver disponível ou houver erro, pular logo
                    return False
            else:
                # PNG, JPG ou outros formatos suportados
                logo_img = Image(logo_path, width=width, height=width * 0.3)
                logo_img.hAlign = 'CENTER'
                story.append(logo_img)
                story.append(Spacer(1, 10))
                return True
        except Exception as e:
            logger.debug('Erro ao carregar logo no PDF: %s', e)
            return False
    return False


def gerar_relatorio_pdf_totalizador_estado(resultados, data_inicial, data_final, total_geral, total_seguro_geral):
    """
    Gera relatório PDF para Totalizador por Estado
    """
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Estilo para subtítulo
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkgrey
    )
    
    # Estilo para parágrafo
    para_style = ParagraphStyle(
        'CustomPara',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    # Conteúdo do relatório
    story = []
    
    # Título
    story.append(Paragraph("RELATÓRIO - TOTALIZADOR POR ESTADO", title_style))
    story.append(Spacer(1, 12))
    
    # Período
    periodo_text = f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}"
    story.append(Paragraph(periodo_text, subtitle_style))
    story.append(Spacer(1, 20))
    
    # Data de geração
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    story.append(Paragraph(f"Relatório gerado em: {data_geracao}", para_style))
    story.append(Spacer(1, 20))
    
    # Resumo
    story.append(Paragraph("RESUMO EXECUTIVO", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    resumo_data = [
        ['Total de Estados', str(len(resultados))],
        ['Valor Total', format_brazilian_currency(total_geral)],
        ['Seguro Total', format_brazilian_currency(total_seguro_geral)]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[8*cm, 6*cm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 30))
    
    # Tabela de resultados
    story.append(Paragraph("DETALHAMENTO POR ESTADO", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Cabeçalho da tabela
    table_data = [['ESTADO', 'QTD. ROMANEIOS', 'VALOR TOTAL', '% SEGURO', 'VALOR SEGURO']]
    
    # Dados da tabela
    for resultado in resultados:
        table_data.append([
            f"{resultado['nome_estado']} ({resultado['estado']})",
            str(resultado['quantidade_romaneios']),
            format_brazilian_currency(resultado['total_valor']),
            f"{resultado['percentual_seguro']:.2f}%",
            format_brazilian_currency(resultado['valor_seguro'])
        ])
    
    # Criar tabela
    table = Table(table_data, colWidths=[4*cm, 3*cm, 3*cm, 2.5*cm, 3*cm])
    table.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Dados
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Estado
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Demais colunas
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Rodapé
    story.append(Paragraph("Sistema Estelar - Relatório de Totalizador por Estado", para_style))
    
    # Construir PDF
    doc.build(story)
    
    # Obter conteúdo do buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def gerar_relatorio_excel_totalizador_estado(resultados, data_inicial, data_final, total_geral, total_seguro_geral):
    """
    Gera relatório Excel para Totalizador por Estado
    """
    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Totalizador por Estado"
    
    # Estilos
    title_font = Font(name='Arial', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    data_font = Font(name='Arial', size=10)
    
    title_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    data_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    right_alignment = Alignment(horizontal='right', vertical='center')
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Título
    ws.merge_cells('A1:F1')
    ws['A1'] = 'RELATÓRIO - TOTALIZADOR POR ESTADO'
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = center_alignment
    
    # Período
    ws.merge_cells('A2:F2')
    ws['A2'] = f'Período: {data_inicial.strftime("%d/%m/%Y")} a {data_final.strftime("%d/%m/%Y")}'
    ws['A2'].font = data_font
    ws['A2'].alignment = center_alignment
    
    # Data de geração
    ws.merge_cells('A3:F3')
    ws['A3'] = f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
    ws['A3'].font = data_font
    ws['A3'].alignment = center_alignment
    
    # Resumo
    ws['A5'] = 'RESUMO EXECUTIVO'
    ws['A5'].font = header_font
    ws['A5'].fill = header_fill
    ws['A5'].alignment = left_alignment
    
    ws['A6'] = 'Total de Estados:'
    ws['B6'] = len(resultados)
    ws['A7'] = 'Valor Total:'
    ws['B7'] = format_brazilian_currency(total_geral)
    ws['A8'] = 'Seguro Total:'
    ws['B8'] = format_brazilian_currency(total_seguro_geral)
    
    # Aplicar estilos ao resumo
    for row in range(6, 9):
        ws[f'A{row}'].font = data_font
        ws[f'B{row}'].font = data_font
        ws[f'B{row}'].alignment = right_alignment
    
    # Cabeçalho da tabela
    headers = ['ESTADO', 'QTD. ROMANEIOS', 'VALOR TOTAL', '% SEGURO', 'VALOR SEGURO']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=10, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border
    
    # Dados da tabela
    for row, resultado in enumerate(resultados, 11):
        ws.cell(row=row, column=1, value=f"{resultado['nome_estado']} ({resultado['estado']})")
        ws.cell(row=row, column=2, value=resultado['quantidade_romaneios'])
        ws.cell(row=row, column=3, value=format_brazilian_currency(resultado['total_valor']))
        ws.cell(row=row, column=4, value=f"{resultado['percentual_seguro']:.2f}%")
        ws.cell(row=row, column=5, value=format_brazilian_currency(resultado['valor_seguro']))
        
        # Aplicar estilos
        for col in range(1, 6):
            cell = ws.cell(row=row, column=col)
            cell.font = data_font
            cell.border = thin_border
            if row % 2 == 0:
                cell.fill = data_fill
            
            # Alinhamento
            if col == 1:  # Estado
                cell.alignment = left_alignment
            else:  # Demais colunas
                cell.alignment = center_alignment
    
    # Ajustar largura das colunas
    column_widths = [25, 15, 18, 12, 18]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # Salvar em buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()


def gerar_resposta_pdf(conteudo_pdf, nome_arquivo, inline=False):
    """Cria resposta HTTP para PDF
    
    Args:
        conteudo_pdf: Bytes do conteúdo PDF
        nome_arquivo: Nome do arquivo para o header
        inline: Se True, abre na página (inline). Se False, faz download (attachment)
    """
    response = HttpResponse(content_type='application/pdf')
    disposition = 'inline' if inline else 'attachment'
    response['Content-Disposition'] = f'{disposition}; filename="{nome_arquivo}"'
    response.write(conteudo_pdf)
    return response


def gerar_resposta_excel(conteudo_excel, nome_arquivo):
    """Cria resposta HTTP para Excel"""
    response = HttpResponse(
        conteudo_excel,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    return response


def gerar_relatorio_pdf_totalizador_cliente(lista_hierarquica, data_inicial, data_final, total_geral, total_seguro_geral):
    """
    Gera relatório PDF para Totalizador por Cliente com estrutura hierárquica
    """
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    # Estilo para subtítulo
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkgrey
    )
    
    # Estilo para parágrafo
    para_style = ParagraphStyle(
        'CustomPara',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )
    
    # Estilo para cabeçalho de estado
    estado_style = ParagraphStyle(
        'EstadoStyle',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=8,
        textColor=colors.darkblue,
        backColor=colors.lightblue
    )
    
    # Estilo para total de estado
    total_estado_style = ParagraphStyle(
        'TotalEstadoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        spaceBefore=8,
        textColor=colors.darkgreen,
        backColor=colors.lightgrey
    )
    
    # Conteúdo do relatório
    story = []
    
    # Título
    story.append(Paragraph("RELATÓRIO - TOTALIZADOR POR CLIENTE", title_style))
    story.append(Spacer(1, 12))
    
    # Período
    periodo_text = f"Período: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}"
    story.append(Paragraph(periodo_text, subtitle_style))
    story.append(Spacer(1, 20))
    
    # Data de geração
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    story.append(Paragraph(f"Relatório gerado em: {data_geracao}", para_style))
    story.append(Spacer(1, 20))
    
    # Resumo
    story.append(Paragraph("RESUMO EXECUTIVO", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Contar estados e clientes
    estados_count = len([item for item in lista_hierarquica if item['tipo'] == 'estado'])
    clientes_count = len([item for item in lista_hierarquica if item['tipo'] == 'cliente'])
    
    resumo_data = [
        ['Total de Estados', str(estados_count)],
        ['Total de Clientes', str(clientes_count)],
        ['Valor Total', format_brazilian_currency(total_geral)],
        ['Seguro Total', format_brazilian_currency(total_seguro_geral)]
    ]
    
    resumo_table = Table(resumo_data, colWidths=[8*cm, 6*cm])
    resumo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(resumo_table)
    story.append(Spacer(1, 30))
    
    # Tabela hierárquica
    story.append(Paragraph("DETALHAMENTO HIERÁRQUICO POR ESTADO", styles['Heading2']))
    story.append(Spacer(1, 10))
    
    # Cabeçalho da tabela
    table_data = [['CLIENTE / ESTADO', 'QTD. ROMANEIOS', 'VALOR TOTAL', '% SEGURO', 'VALOR SEGURO']]
    
    # Dados hierárquicos
    for item in lista_hierarquica:
        if item['tipo'] == 'estado':
            # Cabeçalho do estado
            estado_text = f"🗺️ {item['estado']} - {item['nome_estado']}"
            table_data.append([
                estado_text,
                str(item['quantidade_romaneios']),
                format_brazilian_currency(item['total_valor']),
                '-',
                format_brazilian_currency(item['total_seguro'])
            ])
        elif item['tipo'] == 'cliente':
            # Cliente
            cliente = item['cliente']
            cliente_text = f"    👤 {cliente.razao_social}\n    {cliente.cnpj}"
            table_data.append([
                cliente_text,
                str(item['quantidade_romaneios']),
                format_brazilian_currency(item['total_valor']),
                f"{item['percentual_seguro']:.2f}%",
                format_brazilian_currency(item['valor_seguro'])
            ])
        elif item['tipo'] == 'total_estado':
            # Total do estado
            total_text = f"    📊 TOTAL {item['estado']}"
            table_data.append([
                total_text,
                str(item['quantidade_romaneios']),
                format_brazilian_currency(item['total_valor']),
                '-',
                format_brazilian_currency(item['total_seguro'])
            ])
    
    # Criar tabela
    table = Table(table_data, colWidths=[6*cm, 2.5*cm, 3*cm, 2.5*cm, 3*cm])
    
    # Estilos da tabela
    table_style = [
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]
    
    # Aplicar estilos específicos por tipo de linha
    for i, item in enumerate(lista_hierarquica, 1):
        row_idx = i  # +1 porque o cabeçalho está na linha 0
        
        if item['tipo'] == 'estado':
            # Cabeçalho de estado - fundo azul claro
            table_style.extend([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.lightblue),
                ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, row_idx), (-1, row_idx), 10),
            ])
        elif item['tipo'] == 'cliente':
            # Cliente - fundo branco
            table_style.extend([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white),
                ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica'),
                ('FONTSIZE', (0, row_idx), (-1, row_idx), 9),
            ])
        elif item['tipo'] == 'total_estado':
            # Total de estado - fundo cinza claro
            table_style.extend([
                ('BACKGROUND', (0, row_idx), (-1, row_idx), colors.lightgrey),
                ('FONTNAME', (0, row_idx), (-1, row_idx), 'Helvetica-Bold'),
                ('FONTSIZE', (0, row_idx), (-1, row_idx), 9),
            ])
        
        # Alinhamento
        table_style.extend([
            ('ALIGN', (0, row_idx), (0, row_idx), 'LEFT'),  # Primeira coluna
            ('ALIGN', (1, row_idx), (-1, row_idx), 'CENTER'),  # Demais colunas
        ])
    
    table.setStyle(TableStyle(table_style))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Rodapé
    story.append(Paragraph("Sistema Estelar - Relatório de Totalizador por Cliente", para_style))
    
    # Construir PDF
    doc.build(story)
    
    # Obter conteúdo do buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def gerar_relatorio_excel_totalizador_cliente(lista_hierarquica, data_inicial, data_final, total_geral, total_seguro_geral):
    """
    Gera relatório Excel para Totalizador por Cliente com estrutura hierárquica
    """
    # Criar workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Totalizador por Cliente"
    
    # Estilos
    title_font = Font(name='Arial', size=16, bold=True, color='FFFFFF')
    header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    data_font = Font(name='Arial', size=10)
    estado_font = Font(name='Arial', size=11, bold=True, color='000080')
    total_font = Font(name='Arial', size=10, bold=True, color='006400')
    
    title_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    data_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    estado_fill = PatternFill(start_color='B0E0E6', end_color='B0E0E6', fill_type='solid')
    total_fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')
    
    center_alignment = Alignment(horizontal='center', vertical='center')
    left_alignment = Alignment(horizontal='left', vertical='center')
    right_alignment = Alignment(horizontal='right', vertical='center')
    
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Título
    ws.merge_cells('A1:F1')
    ws['A1'] = 'RELATÓRIO - TOTALIZADOR POR CLIENTE'
    ws['A1'].font = title_font
    ws['A1'].fill = title_fill
    ws['A1'].alignment = center_alignment
    
    # Período
    ws.merge_cells('A2:F2')
    ws['A2'] = f'Período: {data_inicial.strftime("%d/%m/%Y")} a {data_final.strftime("%d/%m/%Y")}'
    ws['A2'].font = data_font
    ws['A2'].alignment = center_alignment
    
    # Data de geração
    ws.merge_cells('A3:F3')
    ws['A3'] = f'Relatório gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
    ws['A3'].font = data_font
    ws['A3'].alignment = center_alignment
    
    # Resumo
    ws['A5'] = 'RESUMO EXECUTIVO'
    ws['A5'].font = header_font
    ws['A5'].fill = header_fill
    ws['A5'].alignment = left_alignment
    
    # Contar estados e clientes
    estados_count = len([item for item in lista_hierarquica if item['tipo'] == 'estado'])
    clientes_count = len([item for item in lista_hierarquica if item['tipo'] == 'cliente'])
    
    ws['A6'] = 'Total de Estados:'
    ws['B6'] = estados_count
    ws['A7'] = 'Total de Clientes:'
    ws['B7'] = clientes_count
    ws['A8'] = 'Valor Total:'
    ws['B8'] = format_brazilian_currency(total_geral)
    ws['A9'] = 'Seguro Total:'
    ws['B9'] = format_brazilian_currency(total_seguro_geral)
    
    # Aplicar estilos ao resumo
    for row in range(6, 10):
        ws[f'A{row}'].font = data_font
        ws[f'B{row}'].font = data_font
        ws[f'B{row}'].alignment = right_alignment
    
    # Cabeçalho da tabela
    headers = ['CLIENTE / ESTADO', 'QTD. ROMANEIOS', 'VALOR TOTAL', '% SEGURO', 'VALOR SEGURO']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=11, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
        cell.border = thin_border
    
    # Dados hierárquicos
    current_row = 12
    for item in lista_hierarquica:
        if item['tipo'] == 'estado':
            # Cabeçalho do estado
            estado_text = f"🗺️ {item['estado']} - {item['nome_estado']}"
            ws.cell(row=current_row, column=1, value=estado_text)
            ws.cell(row=current_row, column=2, value=item['quantidade_romaneios'])
            ws.cell(row=current_row, column=3, value=format_brazilian_currency(item['total_valor']))
            ws.cell(row=current_row, column=4, value='-')
            ws.cell(row=current_row, column=5, value=format_brazilian_currency(item['total_seguro']))
            
            # Aplicar estilos de estado
            for col in range(1, 6):
                cell = ws.cell(row=current_row, column=col)
                cell.font = estado_font
                cell.fill = estado_fill
                cell.border = thin_border
                cell.alignment = left_alignment if col == 1 else center_alignment
            
        elif item['tipo'] == 'cliente':
            # Cliente
            cliente = item['cliente']
            cliente_text = f"    👤 {cliente.razao_social}\n    {cliente.cnpj}"
            ws.cell(row=current_row, column=1, value=cliente_text)
            ws.cell(row=current_row, column=2, value=item['quantidade_romaneios'])
            ws.cell(row=current_row, column=3, value=format_brazilian_currency(item['total_valor']))
            ws.cell(row=current_row, column=4, value=f"{item['percentual_seguro']:.2f}%")
            ws.cell(row=current_row, column=5, value=format_brazilian_currency(item['valor_seguro']))
            
            # Aplicar estilos de cliente
            for col in range(1, 6):
                cell = ws.cell(row=current_row, column=col)
                cell.font = data_font
                cell.border = thin_border
                cell.alignment = left_alignment if col == 1 else center_alignment
                # Fundo alternado para clientes
                if current_row % 2 == 0:
                    cell.fill = data_fill
            
        elif item['tipo'] == 'total_estado':
            # Total do estado
            total_text = f"    📊 TOTAL {item['estado']}"
            ws.cell(row=current_row, column=1, value=total_text)
            ws.cell(row=current_row, column=2, value=item['quantidade_romaneios'])
            ws.cell(row=current_row, column=3, value=format_brazilian_currency(item['total_valor']))
            ws.cell(row=current_row, column=4, value='-')
            ws.cell(row=current_row, column=5, value=format_brazilian_currency(item['total_seguro']))
            
            # Aplicar estilos de total
            for col in range(1, 6):
                cell = ws.cell(row=current_row, column=col)
                cell.font = total_font
                cell.fill = total_fill
                cell.border = thin_border
                cell.alignment = left_alignment if col == 1 else center_alignment
        
        current_row += 1
    
    # Ajustar largura das colunas
    column_widths = [35, 15, 18, 12, 18]
    for col, width in enumerate(column_widths, 1):
        ws.column_dimensions[get_column_letter(col)].width = width
    
    # Salvar em buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()


# ============================================================================
# FUNÇÕES AUXILIARES COMPARTILHADAS - COBRANÇA DE CARREGAMENTO
# ============================================================================

def _criar_estilos_relatorio_cobranca():
    """Cria estilos comuns para relatórios de cobrança"""
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=16
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        spaceBefore=12,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=11,
        leftIndent=0
    )
    
    para_style = ParagraphStyle(
        'ParaStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=2,
        alignment=TA_LEFT,
        textColor=colors.black,
        leading=10,
        leftIndent=0,
        rightIndent=0
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=2,
        alignment=TA_LEFT,
        textColor=colors.black,
        leading=9,
        leftIndent=0,
        rightIndent=0
    )
    
    return {
        'title': title_style,
        'section': section_style,
        'para': para_style,
        'info': info_style
    }


def _adicionar_linha_separadora(story, width=None):
    """Adiciona uma linha horizontal para separar seções"""
    # Largura da página A4 menos margens (1.5cm cada lado) = 21cm - 3cm = 18cm
    if width is None:
        width = 18*cm
    linha = Table([['']], colWidths=[width], rowHeights=[0.3*cm])
    linha.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(linha)
    story.append(Spacer(1, 4))


def _adicionar_cabecalho_cobranca(story, cobranca, title_style, section_style, para_style, info_style):
    """Adiciona cabeçalho comum (título, cliente)"""
    story.append(Paragraph("COBRANÇA DE CARREGAMENTO", title_style))
    story.append(Spacer(1, 6))
    
    _adicionar_linha_separadora(story)
    story.append(Paragraph("CLIENTE", section_style))
    story.append(Paragraph(cobranca.cliente.razao_social, para_style))
    if cobranca.cliente.cnpj:
        story.append(Paragraph(f"CNPJ: {cobranca.cliente.cnpj}", info_style))
    story.append(Spacer(1, 5))


def _adicionar_romaneios_cobranca(story, cobranca, section_style, para_style):
    """Adiciona seção de romaneios"""
    _adicionar_linha_separadora(story)
    story.append(Paragraph("ROMANEIOS", section_style))
    
    romaneios_list = []
    for romaneio in cobranca.romaneios.all().select_related('motorista', 'veiculo_principal', 'reboque_1', 'reboque_2'):
        data_emissao = romaneio.data_emissao.strftime('%d/%m/%Y') if romaneio.data_emissao else '-'
        motorista_nome = romaneio.motorista.nome if romaneio.motorista else '-'
        
        placas = []
        if romaneio.veiculo_principal:
            placas.append(romaneio.veiculo_principal.placa)
        if romaneio.reboque_1:
            placas.append(romaneio.reboque_1.placa)
        if romaneio.reboque_2:
            placas.append(romaneio.reboque_2.placa)
        placas_str = ' / '.join(placas) if placas else '-'
        
        romaneio_info = f"<b>{romaneio.codigo}</b> • {data_emissao}"
        if motorista_nome != '-':
            romaneio_info += f" • {motorista_nome}"
        if placas_str != '-':
            romaneio_info += f" • {placas_str}"
        
        romaneios_list.append(romaneio_info)
    
    for romaneio_info in romaneios_list:
        story.append(Paragraph(romaneio_info, para_style))
    
    story.append(Spacer(1, 6))


def _adicionar_rodape_cobranca(story, info_style):
    """Adiciona rodapé comum"""
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    story.append(Spacer(1, 8))
    linha_rodape = Table([['']], colWidths=[13*cm], rowHeights=[0.2*cm])
    linha_rodape.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    story.append(linha_rodape)
    story.append(Spacer(1, 3))
    story.append(Paragraph(f"Gerado em {data_geracao}", info_style))


# ============================================================================
# RELATÓRIO ESPECIALIZADO - MENSALISTA
# ============================================================================

def gerar_relatorio_pdf_cobranca_mensalista(cobranca):
    """
    Gera relatório PDF para Cobrança de Carregamento - Cliente Mensalista
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    doc.title = "Relatório Cobrança - Mensalista"
    
    # Obter estilos
    estilos = _criar_estilos_relatorio_cobranca()
    
    story = []
    
    # Cabeçalho
    _adicionar_cabecalho_cobranca(story, cobranca, estilos['title'], estilos['section'], estilos['para'], estilos['info'])
    
    # Romaneios
    _adicionar_romaneios_cobranca(story, cobranca, estilos['section'], estilos['para'])
    
    # Valores - Mensalista (sem armazenamento)
    _adicionar_linha_separadora(story)
    story.append(Paragraph("VALORES", estilos['section']))
    
    valores_data = [
        ['Carregamento', format_brazilian_currency(cobranca.valor_carregamento)],
        ['CTE/Manifesto', format_brazilian_currency(cobranca.valor_cte_manifesto)],
    ]
    
    valores_table = Table(valores_data, colWidths=[10*cm, 6*cm])
    valores_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    
    story.append(valores_table)
    story.append(Spacer(1, 2))
    
    # Total
    total_data = [['TOTAL', format_brazilian_currency(cobranca.valor_total)]]
    total_table = Table(total_data, colWidths=[10*cm, 6*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 6))
    
    # Informações adicionais
    if cobranca.data_vencimento or cobranca.status or cobranca.data_baixa:
        _adicionar_linha_separadora(story)
        story.append(Paragraph("INFORMAÇÕES ADICIONAIS", estilos['section']))
        info_items = []
        if cobranca.data_vencimento:
            info_items.append(f"Vencimento: {cobranca.data_vencimento.strftime('%d/%m/%Y')}")
        info_items.append(f"Status: {cobranca.get_status_display()}")
        if cobranca.data_baixa:
            info_items.append(f"Baixa: {cobranca.data_baixa.strftime('%d/%m/%Y')}")
        for item in info_items:
            story.append(Paragraph(item, estilos['info']))
        story.append(Spacer(1, 5))
    
    # Instruções de Pagamento
    _adicionar_linha_separadora(story)
    story.append(Paragraph("INSTRUÇÕES DE PAGAMENTO", estilos['section']))
    
    # Buscar dados bancários dos setores
    from financeiro.models import SetorBancario

    # Calcular valores por setor
    # Setor de Carregamento: Carregamento + CTE/Manifesto
    valor_carregamento = Decimal(str(cobranca.valor_carregamento)) if cobranca.valor_carregamento else Decimal('0.00')
    valor_cte_manifesto = Decimal(str(cobranca.valor_cte_manifesto)) if cobranca.valor_cte_manifesto else Decimal('0.00')
    valor_setor_carregamento = valor_carregamento + valor_cte_manifesto

    # Setor de Armazenagem: Armazenamento + Seguro
    valor_armazenagem = valor_armazenamento + total_seguro

    # Setor de Carregamento
    try:
        setor_carregamento = SetorBancario.objects.filter(setor='Carregamento', ativo=True).first()
        if setor_carregamento and valor_setor_carregamento > Decimal('0'):
            story.append(Paragraph(f"<b>SETOR DE CARREGAMENTO</b>", estilos['para']))
            story.append(Paragraph(f"Valor: {format_brazilian_currency(valor_setor_carregamento)} (Carregamento + CTE/Manifesto)", estilos['info']))
            story.append(Paragraph(f"DEPOSITAR: {format_brazilian_currency(valor_setor_carregamento)}", estilos['info']))
            story.append(Paragraph(f"Banco: {setor_carregamento.banco}", estilos['info']))
            story.append(Paragraph(f"Agência: {setor_carregamento.agencia}", estilos['info']))
            story.append(Paragraph(f"Conta Corrente: {setor_carregamento.conta_corrente}", estilos['info']))
            story.append(Paragraph(f"PIX: {setor_carregamento.get_chave_pix_formatada()}", estilos['info']))
            story.append(Paragraph(f"Beneficiário: {setor_carregamento.nome_responsavel}", estilos['info']))
            story.append(Spacer(1, 4))
    except Exception as e:
        logger.warning('Erro ao adicionar dados bancários (setor carregamento) ao PDF: %s', e)
    
    # Setor de Armazenagem
    try:
        setor_armazenagem = SetorBancario.objects.filter(setor='Armazenagem', ativo=True).first()
        if setor_armazenagem and valor_armazenagem > Decimal('0'):
            story.append(Paragraph(f"<b>SETOR DE ARMAZENAGEM</b>", estilos['para']))
            story.append(Paragraph(f"Valor: {format_brazilian_currency(valor_armazenagem)} (Armazenamento + Seguro)", estilos['info']))
            story.append(Paragraph(f"DEPOSITAR: {format_brazilian_currency(valor_armazenagem)}", estilos['info']))
            story.append(Paragraph(f"Banco: {setor_armazenagem.banco}", estilos['info']))
            story.append(Paragraph(f"Agência: {setor_armazenagem.agencia}", estilos['info']))
            story.append(Paragraph(f"Conta Corrente: {setor_armazenagem.conta_corrente}", estilos['info']))
            story.append(Paragraph(f"PIX: {setor_armazenagem.get_chave_pix_formatada()}", estilos['info']))
            story.append(Paragraph(f"Beneficiário: {setor_armazenagem.nome_responsavel}", estilos['info']))
            story.append(Spacer(1, 4))
    except Exception as e:
        logger.warning('Erro ao adicionar dados bancários (setor armazenagem) ao PDF: %s', e)
    
    # Observações
    observacoes = getattr(cobranca, 'observacoes', None)
    if observacoes and observacoes.strip():
        _adicionar_linha_separadora(story)
        story.append(Paragraph("OBSERVAÇÕES", estilos['section']))
        observacoes_texto = observacoes.replace('\n', '<br/>')
        story.append(Paragraph(observacoes_texto, estilos['para']))
        story.append(Spacer(1, 5))
    
    # Rodapé
    _adicionar_rodape_cobranca(story, estilos['info'])
    
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


# ============================================================================
# RELATÓRIO ESPECIALIZADO - POR CUBAGEM
# ============================================================================

def gerar_relatorio_pdf_cobranca_por_cubagem(cobranca):
    """
    Gera relatório PDF para Cobrança de Carregamento - Cliente Por Cubagem
    """
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    doc.title = "Relatório Cobrança - Por Cubagem"
    
    # Obter estilos
    estilos = _criar_estilos_relatorio_cobranca()
    
    story = []
    
    # Cabeçalho
    _adicionar_cabecalho_cobranca(story, cobranca, estilos['title'], estilos['section'], estilos['para'], estilos['info'])
    
    # Romaneios
    _adicionar_romaneios_cobranca(story, cobranca, estilos['section'], estilos['para'])
    
    # Valores - Por Cubagem (com armazenamento)
    _adicionar_linha_separadora(story)
    story.append(Paragraph("VALORES", estilos['section']))
    
    valores_data = [
        ['Carregamento', format_brazilian_currency(cobranca.valor_carregamento)],
        ['CTE/Manifesto', format_brazilian_currency(cobranca.valor_cte_manifesto)],
    ]
    
    # Adicionar armazenamento
    from decimal import Decimal
    valor_armazenamento = Decimal('0.00')
    try:
        cubagem = getattr(cobranca, 'cubagem', None)
        valor_cubagem = getattr(cobranca, 'valor_cubagem', None)
        
        if cubagem is not None and valor_cubagem is not None:
            cubagem_decimal = Decimal(str(cubagem)) if cubagem else Decimal('0')
            valor_cubagem_decimal = Decimal(str(valor_cubagem)) if valor_cubagem else Decimal('0')
            
            if cubagem_decimal > Decimal('0') and valor_cubagem_decimal > Decimal('0'):
                valor_armazenamento = cubagem_decimal * valor_cubagem_decimal
                if valor_armazenamento > Decimal('0'):
                    valores_data.append(['Armazenamento', format_brazilian_currency(valor_armazenamento)])
    except (TypeError, ValueError, AttributeError):
        pass
    
    # Adicionar seguro (sempre calculado para cobrança por cubagem)
    # Calcula: valor_total do romaneio * percentual_seguro do estado do cliente
    total_seguro = Decimal('0.00')
    try:
        # Obter estado do cliente
        estado_cliente = getattr(cobranca.cliente, 'estado', None)
        
        if estado_cliente:
            # Buscar percentual de seguro na TabelaSeguro
            from ..models import TabelaSeguro
            try:
                tabela_seguro = TabelaSeguro.objects.get(estado=estado_cliente)
                percentual_seguro = Decimal(str(tabela_seguro.percentual_seguro))
                
                # Calcular seguro para cada romaneio
                for romaneio in cobranca.romaneios.all():
                    valor_total_romaneio = getattr(romaneio, 'valor_total', None)
                    if valor_total_romaneio is not None:
                        valor_romaneio = Decimal(str(valor_total_romaneio)) if valor_total_romaneio else Decimal('0')
                        if valor_romaneio > Decimal('0'):
                            # Seguro = valor_total * (percentual / 100)
                            seguro_romaneio = (valor_romaneio * percentual_seguro) / Decimal('100')
                            total_seguro += seguro_romaneio
            except TabelaSeguro.DoesNotExist:
                # Se não houver tabela de seguro para o estado, seguro = 0
                pass
    except (TypeError, ValueError, AttributeError):
        pass
    
    # Sempre adicionar linha de seguro (mesmo que seja zero)
    valores_data.append(['Seguro', format_brazilian_currency(total_seguro)])
    
    valores_table = Table(valores_data, colWidths=[10*cm, 6*cm])
    valores_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    
    story.append(valores_table)
    story.append(Spacer(1, 2))
    
    # Total (sempre inclui seguro para cobrança por cubagem)
    total_calculado = cobranca.valor_total + total_seguro
    total_data = [['TOTAL', format_brazilian_currency(total_calculado)]]
    total_table = Table(total_data, colWidths=[10*cm, 6*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    
    story.append(total_table)
    story.append(Spacer(1, 12))
    
    # Informações adicionais
    if cobranca.data_vencimento or cobranca.status or cobranca.data_baixa:
        _adicionar_linha_separadora(story)
        story.append(Paragraph("INFORMAÇÕES ADICIONAIS", estilos['section']))
        info_items = []
        if cobranca.data_vencimento:
            info_items.append(f"Vencimento: {cobranca.data_vencimento.strftime('%d/%m/%Y')}")
        info_items.append(f"Status: {cobranca.get_status_display()}")
        if cobranca.data_baixa:
            info_items.append(f"Baixa: {cobranca.data_baixa.strftime('%d/%m/%Y')}")
        for item in info_items:
            story.append(Paragraph(item, estilos['info']))
        story.append(Spacer(1, 12))
    
    # Instruções de Pagamento
    _adicionar_linha_separadora(story)
    story.append(Paragraph("INSTRUÇÕES DE PAGAMENTO", estilos['section']))
    
    # Buscar dados bancários dos setores
    from financeiro.models import SetorBancario

    # Calcular valores por setor
    # Setor de Carregamento: Carregamento + CTE/Manifesto
    valor_carregamento = Decimal(str(cobranca.valor_carregamento)) if cobranca.valor_carregamento else Decimal('0.00')
    valor_cte_manifesto = Decimal(str(cobranca.valor_cte_manifesto)) if cobranca.valor_cte_manifesto else Decimal('0.00')
    valor_setor_carregamento = valor_carregamento + valor_cte_manifesto
    
    # Setor de Armazenagem: Armazenamento + Seguro
    valor_armazenagem = valor_armazenamento + total_seguro
    
    # Estilos para a seção de pagamento
    titulo_setor_style = ParagraphStyle(
        'TituloSetor',
        parent=estilos['section'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=0
    )
    
    valor_destaque_style = ParagraphStyle(
        'ValorDestaque',
        parent=estilos['para'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=4
    )
    
    info_bancaria_style = ParagraphStyle(
        'InfoBancaria',
        parent=estilos['info'],
        fontSize=8,
        fontName='Helvetica',
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=3,
        leading=10
    )
    
    # Preparar conteúdo para cada coluna
    coluna_esquerda = []
    coluna_direita = []
    
    # Coluna Esquerda - Setor de Carregamento
    try:
        setor_carregamento = SetorBancario.objects.filter(setor='Carregamento', ativo=True).first()
        if setor_carregamento and valor_setor_carregamento > Decimal('0'):
            coluna_esquerda.append(Paragraph("<b>SETOR DE CARREGAMENTO</b>", titulo_setor_style))
            coluna_esquerda.append(Spacer(1, 2))
            coluna_esquerda.append(Paragraph(f"<b>DEPOSITAR:</b>", info_bancaria_style))
            coluna_esquerda.append(Paragraph(f"<b><font size='16' color='#000000'>{format_brazilian_currency(valor_setor_carregamento)}</font></b>", valor_destaque_style))
            coluna_esquerda.append(Spacer(1, 6))
            coluna_esquerda.append(Paragraph(f"<b>Banco:</b> {setor_carregamento.banco}", info_bancaria_style))
            coluna_esquerda.append(Paragraph(f"<b>Agência:</b> {setor_carregamento.agencia}", info_bancaria_style))
            coluna_esquerda.append(Paragraph(f"<b>Conta:</b> {setor_carregamento.conta_corrente}", info_bancaria_style))
            coluna_esquerda.append(Paragraph(f"<b>PIX:</b> {setor_carregamento.get_chave_pix_formatada()}", info_bancaria_style))
            coluna_esquerda.append(Paragraph(f"<b>Beneficiário:</b> {setor_carregamento.nome_responsavel}", info_bancaria_style))
    except Exception as e:
        logger.warning('Erro ao adicionar dados bancários (coluna esquerda) ao PDF consolidado: %s', e)
        coluna_esquerda.append(Paragraph("", info_bancaria_style))
    
    # Coluna Direita - Setor de Armazenagem
    try:
        setor_armazenagem = SetorBancario.objects.filter(setor='Armazenagem', ativo=True).first()
        if setor_armazenagem and valor_armazenagem > Decimal('0'):
            coluna_direita.append(Paragraph("<b>SETOR DE ARMAZENAGEM</b>", titulo_setor_style))
            coluna_direita.append(Spacer(1, 2))
            coluna_direita.append(Paragraph(f"<b>DEPOSITAR:</b>", info_bancaria_style))
            coluna_direita.append(Paragraph(f"<b><font size='16' color='#000000'>{format_brazilian_currency(valor_armazenagem)}</font></b>", valor_destaque_style))
            coluna_direita.append(Spacer(1, 6))
            coluna_direita.append(Paragraph(f"<b>Banco:</b> {setor_armazenagem.banco}", info_bancaria_style))
            coluna_direita.append(Paragraph(f"<b>Agência:</b> {setor_armazenagem.agencia}", info_bancaria_style))
            coluna_direita.append(Paragraph(f"<b>Conta:</b> {setor_armazenagem.conta_corrente}", info_bancaria_style))
            coluna_direita.append(Paragraph(f"<b>PIX:</b> {setor_armazenagem.get_chave_pix_formatada()}", info_bancaria_style))
            coluna_direita.append(Paragraph(f"<b>Beneficiário:</b> {setor_armazenagem.nome_responsavel}", info_bancaria_style))
    except Exception as e:
        logger.warning('Erro ao adicionar dados bancários (coluna direita) ao PDF consolidado: %s', e)
        coluna_direita.append(Paragraph("", info_bancaria_style))
    
    # Criar tabela com duas colunas
    # Ajustar altura das colunas para alinhar
    max_items = max(len(coluna_esquerda), len(coluna_direita))
    
    # Preencher a coluna menor com espaços vazios para alinhar
    while len(coluna_esquerda) < max_items:
        coluna_esquerda.append(Spacer(1, 0.1))
    while len(coluna_direita) < max_items:
        coluna_direita.append(Spacer(1, 0.1))
    
    # Criar tabela de duas colunas
    dados_tabela = []
    for i in range(max_items):
        dados_tabela.append([
            coluna_esquerda[i] if i < len(coluna_esquerda) else Paragraph("", info_bancaria_style),
            coluna_direita[i] if i < len(coluna_direita) else Paragraph("", info_bancaria_style)
        ])
    
    tabela_pagamento = Table(dados_tabela, colWidths=[8*cm, 8*cm])
    tabela_pagamento.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f5f5f5')),
        ('LINEAFTER', (0, 0), (0, -1), 1, colors.grey),
    ]))
    
    story.append(tabela_pagamento)
    story.append(Spacer(1, 12))
    
    # Observações
    observacoes = getattr(cobranca, 'observacoes', None)
    if observacoes and observacoes.strip():
        _adicionar_linha_separadora(story)
        story.append(Paragraph("OBSERVAÇÕES", estilos['section']))
        observacoes_texto = observacoes.replace('\n', '<br/>')
        story.append(Paragraph(observacoes_texto, estilos['para']))
        story.append(Spacer(1, 12))
    
    # Rodapé
    _adicionar_rodape_cobranca(story, estilos['info'])
    
    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


# ============================================================================
# FUNÇÃO WRAPPER (MANTÉM COMPATIBILIDADE)
# ============================================================================

def gerar_relatorio_pdf_cobranca_carregamento(cobranca):
    """
    Wrapper que escolhe o relatório correto baseado no tipo de cliente.
    Mantém compatibilidade com código existente.
    """
    tipo = str(cobranca.tipo_cliente).upper() if getattr(cobranca, 'tipo_cliente', None) else ''
    
    if tipo == 'POR_CUBAGEM':
        return gerar_relatorio_pdf_cobranca_por_cubagem(cobranca)
    else:
        return gerar_relatorio_pdf_cobranca_mensalista(cobranca)


def gerar_relatorio_pdf_consolidado_cobranca(cobrancas_pendentes, cliente_selecionado=None):
    """
    Gera relatório PDF consolidado com cobranças pendentes - Formato Minimalista Profissional
    """
    buffer = io.BytesIO()
    
    # Criar documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Definir metadados do PDF (título da aba)
    doc.title = "Relatório Cobrança"
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=24
    )
    
    # Estilo para subtítulo/seção
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        spaceBefore=20,
        alignment=TA_LEFT,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=14
    )
    
    # Estilo para texto normal
    para_style = ParagraphStyle(
        'ParaStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        alignment=TA_LEFT,
        textColor=colors.black,
        leading=13
    )
    
    # Estilo para informações secundárias
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=6,
        alignment=TA_LEFT,
        textColor=colors.black,
        leading=12
    )
    
    # Conteúdo do relatório
    story = []
    
    # Título principal
    story.append(Paragraph("COBRANÇAS PENDENTES", title_style))
    story.append(Spacer(1, 25))
    
    # Informações do Cliente
    if cliente_selecionado:
        story.append(Paragraph("CLIENTE", section_style))
        story.append(Paragraph(cliente_selecionado.razao_social, para_style))
        if cliente_selecionado.cnpj:
            story.append(Paragraph(f"CNPJ: {cliente_selecionado.cnpj}", info_style))
        story.append(Spacer(1, 25))
    
    # Calcular totais (usar valor_total ou calcular)
    total_carregamento = sum([c.valor_carregamento or Decimal('0.00') for c in cobrancas_pendentes])
    total_cte_manifesto = sum([c.valor_cte_manifesto or Decimal('0.00') for c in cobrancas_pendentes])
    total_armazenamento = Decimal('0.00')
    
    # Tabela de cobranças - formato minimalista
    story.append(Paragraph("COBRANÇAS", section_style))
    
    cobrancas_data = []
    for cobranca in cobrancas_pendentes:
        romaneios_codigos = [r.codigo for r in cobranca.romaneios.all()]
        romaneios_str = ', '.join(romaneios_codigos[:3]) if romaneios_codigos else '-'
        if len(romaneios_codigos) > 3:
            romaneios_str += f" (+{len(romaneios_codigos) - 3})"
        
        data_cobranca = cobranca.criado_em.strftime('%d/%m/%Y') if cobranca.criado_em else '-'
        
        # Calcular valor de armazenamento
        valor_armazenamento = Decimal('0.00')
        try:
            cubagem = getattr(cobranca, 'cubagem', None)
            valor_cubagem = getattr(cobranca, 'valor_cubagem', None)
            if cubagem is not None and valor_cubagem is not None:
                cubagem_decimal = Decimal(str(cubagem)) if cubagem else Decimal('0')
                valor_cubagem_decimal = Decimal(str(valor_cubagem)) if valor_cubagem else Decimal('0')
                if cubagem_decimal > Decimal('0') and valor_cubagem_decimal > Decimal('0'):
                    valor_armazenamento = cubagem_decimal * valor_cubagem_decimal
                    total_armazenamento += valor_armazenamento
        except (TypeError, ValueError, AttributeError):
            pass
        
        # Usar valor_total (property) ou calcular
        valor_total = cobranca.valor_total if hasattr(cobranca, 'valor_total') else (cobranca.valor_carregamento or Decimal('0.00')) + (cobranca.valor_cte_manifesto or Decimal('0.00'))
        
        cobrancas_data.append([
            romaneios_str,
            data_cobranca,
            format_brazilian_currency(cobranca.valor_carregamento or Decimal('0.00')),
            format_brazilian_currency(cobranca.valor_cte_manifesto or Decimal('0.00')),
            format_brazilian_currency(valor_armazenamento) if valor_armazenamento > Decimal('0') else '-',
            format_brazilian_currency(valor_total)
        ])
    
    # Cabeçalho da tabela
    header_data = [['Romaneio', 'Data', 'Carregamento', 'CTE/Manifesto', 'Armazenamento', 'Total']]
    header_table = Table(header_data, colWidths=[3*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    story.append(header_table)
    
    # Dados das cobranças
    if cobrancas_data:
        dados_table = Table(cobrancas_data, colWidths=[3*cm, 2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        dados_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
        ]))
        story.append(dados_table)
    
    story.append(Spacer(1, 10))
    
    # Total consolidado
    total_data = [
        ['Total Carregamento', format_brazilian_currency(total_carregamento)],
        ['Total CTE/Manifesto', format_brazilian_currency(total_cte_manifesto)],
    ]
    
    # Adicionar total de armazenamento se houver
    if total_armazenamento > Decimal('0'):
        total_data.append(['Total Armazenamento', format_brazilian_currency(total_armazenamento)])
    
    total_table = Table(total_data, colWidths=[10*cm, 4*cm])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 5))
    
    # Total geral destacado (incluindo armazenamento)
    total_geral = total_carregamento + total_cte_manifesto + total_armazenamento
    total_geral_data = [['TOTAL GERAL', format_brazilian_currency(total_geral)]]
    total_geral_table = Table(total_geral_data, colWidths=[10*cm, 4*cm])
    total_geral_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
    ]))
    story.append(total_geral_table)
    story.append(Spacer(1, 30))
    
    # Rodapé minimalista
    data_geracao = datetime.now().strftime('%d/%m/%Y às %H:%M')
    linha_rodape = Table([['']], colWidths=[13*cm], rowHeights=[0.3*cm])
    linha_rodape.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#ecf0f1')),
    ]))
    story.append(linha_rodape)
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Gerado em {data_geracao}", info_style))
    
    # Construir PDF
    doc.build(story)
    
    # Obter conteúdo do buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content