"""
Utilitários para geração de relatórios em PDF e Excel
"""

import io
from datetime import datetime
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


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


def gerar_resposta_pdf(conteudo_pdf, nome_arquivo):
    """Cria resposta HTTP para PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
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
