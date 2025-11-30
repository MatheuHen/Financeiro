# Pós-processador robusto para garantir todas as regras obrigatórias do JSON
import copy
import re
def corrigir_json_nfe(json_extraido, texto_front=None):
    base = {
        "fornecedor": {"razao_social": None, "fantasia": None, "cnpj": None},
        "faturado": {"nome": None, "cpf": None},
        "nota_fiscal": {
            "numero": None,
            "serie": None,
            "data_emissao": None,
            "produtos": [],
            "parcelas": {
                "quantidade_total": 1,
                "itens": [{"numero": None, "data_vencimento": None, "valor": None}]
            },
            "valor_total": None,
            "classificacao_despesa": None
        }
    }
    issues = []
    data = copy.deepcopy(base)
    def get_val(d, k):
        return d.get(k) if d and isinstance(d, dict) else None
    # Fornecedor
    for campo in base["fornecedor"]:
        val = get_val(json_extraido.get("fornecedor", {}), campo)
        if val == "": val = None
        data["fornecedor"][campo] = val
    if "fantasia" not in data["fornecedor"]:
        data["fornecedor"]["fantasia"] = None
    # Faturado
    for campo in base["faturado"]:
        val = get_val(json_extraido.get("faturado", {}), campo)
        if val == "": val = None
        data["faturado"][campo] = val
    # Nota Fiscal
    nf = json_extraido.get("nota_fiscal", {})
    for campo in ["numero", "serie", "data_emissao"]:
        val = get_val(nf, campo)
        if val == "": val = None
        data["nota_fiscal"][campo] = val
    # valor_total: normalização
    val = get_val(nf, "valor_total")
    antes = val
    if val is not None:
        val = str(val).replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            val = f"{float(val):.2f}"
        except Exception:
            val = None
    data["nota_fiscal"]["valor_total"] = val
    if antes != val:
        issues.append({"campo": "nota_fiscal.valor_total", "status": "normalizado", "detalhe": "Valor total normalizado", "antes": antes, "depois": val})
    # Produtos
    produtos = nf.get("produtos", [])
    data["nota_fiscal"]["produtos"] = []
    for idx, prod in enumerate(produtos):
        p = {}
        for campo in ["descricao", "quantidade", "valor_unitario", "valor_total"]:
            v = prod.get(campo)
            if v == "": v = None
            if campo in ["valor_unitario", "valor_total"] and v is not None:
                antes = v
                v = str(v).replace("R$", "").replace(".", "").replace(",", ".").strip()
                try:
                    v = f"{float(v):.2f}"
                except Exception:
                    v = None
                if antes != v:
                    issues.append({"campo": f"nota_fiscal.produtos[{idx}].{campo}", "status": "normalizado", "detalhe": "Valor normalizado", "antes": antes, "depois": v})
            if campo == "quantidade" and v is not None:
                try:
                    v = float(str(v).replace(",", "."))
                except Exception:
                    v = None
            p[campo] = v
        data["nota_fiscal"]["produtos"].append(p)
    # Parcelas
    parcelas = nf.get("parcelas", {})
    if isinstance(parcelas, list):
        itens = []
        for par in parcelas:
            itens.append({
                "numero": par.get("numero"),
                "data_vencimento": par.get("data_vencimento"),
                "valor": par.get("valor")
            })
        parcelas = {"quantidade_total": max(1, len(itens)), "itens": itens or [{"numero": None, "data_vencimento": None, "valor": None}]}
    if not isinstance(parcelas, dict):
        parcelas = {"quantidade_total": 1, "itens": [{"numero": None, "data_vencimento": None, "valor": None}]}
    if parcelas.get("quantidade_total", 0) < 1:
        issues.append({"campo": "nota_fiscal.parcelas", "status": "corrigido", "detalhe": "quantidade_total < 1; ajustado para 1", "antes": parcelas, "depois": {"quantidade_total": 1}})
        parcelas["quantidade_total"] = 1
    if "itens" not in parcelas or not parcelas["itens"]:
        parcelas["itens"] = [{"numero": None, "data_vencimento": None, "valor": None}]
    for item in parcelas["itens"]:
        for campo in ["numero", "data_vencimento", "valor"]:
            if campo not in item:
                item[campo] = None
            if item[campo] == "":
                item[campo] = None
    data["nota_fiscal"]["parcelas"] = parcelas
    # Classificação da despesa
    descs = " ".join([str(p.get("descricao", "")).lower() for p in data["nota_fiscal"]["produtos"]])
    categorias = [
        (['óleo diesel', 'combustível', 'lubrificante', 'pneu', 'filtro', 'correia', 'parafuso', 'peça', 'kit cabo de aço', 'manutenção'], 'MANUTENÇÃO E OPERAÇÃO'),
        (['tubo', 'material hidráulico', 'cimento', 'construção', 'reforma', 'energia'], 'INFRAESTRUTURA E UTILIDADES'),
        (['notebook', 'computador', 'máquina', 'implemento', 'veículo', 'imóvel'], 'INVESTIMENTOS'),
        (['honorários', 'taxa bancária', 'tarifa'], 'ADMINISTRATIVAS'),
        (['semente', 'fertilizante', 'defensivo', 'corretivo'], 'INSUMOS AGRÍCOLAS'),
        (['seguro'], 'SEGUROS E PROTEÇÃO'),
        (['itr', 'iptu', 'ipva', 'taxa'], 'IMPOSTOS E TAXAS'),
    ]
    found = None
    for palavras, classe in categorias:
        for palavra in palavras:
            if palavra in descs:
                found = classe
                break
        if found:
            break
    antes = data["nota_fiscal"].get("classificacao_despesa")
    data["nota_fiscal"]["classificacao_despesa"] = found if found else None
    if antes != data["nota_fiscal"]["classificacao_despesa"]:
        issues.append({"campo": "nota_fiscal.classificacao_despesa", "status": "corrigido", "detalhe": f"Classificação ajustada", "antes": antes, "depois": data["nota_fiscal"]["classificacao_despesa"]})
    # Divergência front (opcional)
    if texto_front:
        if "Nenhuma parcela encontrada" in texto_front and (parcelas.get("quantidade_total", 1) > 1 or any(x for x in parcelas.get("itens", []) if x.get("valor"))):
            issues.append({"campo": "nota_fiscal.parcelas", "status": "divergencia_front", "detalhe": "Front diz nenhuma parcela, mas JSON tem duplicata"})
    return {
        "json_corrigido": data,
        "issues": issues
    }
# Pós-processador para garantir todas as regras obrigatórias do JSON
def posprocessar_json_nfe(json_extraido):
    import copy
    data = copy.deepcopy(json_extraido)
    # 1. Fornecedor
    if 'fornecedor' not in data or not isinstance(data['fornecedor'], dict):
        data['fornecedor'] = {}
    for campo in ['razao_social', 'fantasia', 'cnpj']:
        if campo not in data['fornecedor']:
            data['fornecedor'][campo] = None
        if data['fornecedor'][campo] == '':
            data['fornecedor'][campo] = None
    # 2. Faturado
    if 'faturado' not in data or not isinstance(data['faturado'], dict):
        data['faturado'] = {}
    for campo in ['nome', 'cpf']:
        if campo not in data['faturado']:
            data['faturado'][campo] = None
        if data['faturado'][campo] == '':
            data['faturado'][campo] = None
    # 3. Nota Fiscal
    if 'nota_fiscal' not in data or not isinstance(data['nota_fiscal'], dict):
        data['nota_fiscal'] = {}
    for campo in ['numero', 'serie', 'data_emissao', 'valor_total']:
        if campo not in data['nota_fiscal']:
            data['nota_fiscal'][campo] = None
        if data['nota_fiscal'][campo] == '':
            data['nota_fiscal'][campo] = None
    # Padroniza valor_total
    if data['nota_fiscal']['valor_total'] is not None:
        try:
            valor = str(data['nota_fiscal']['valor_total']).replace(',', '.')
            data['nota_fiscal']['valor_total'] = f"{float(valor):.2f}"
        except Exception:
            data['nota_fiscal']['valor_total'] = None
    # 4. Produtos
    if 'produtos' not in data['nota_fiscal'] or not isinstance(data['nota_fiscal']['produtos'], list):
        data['nota_fiscal']['produtos'] = []
    for prod in data['nota_fiscal']['produtos']:
        for campo in ['descricao', 'quantidade', 'valor_unitario', 'valor_total']:
            if campo not in prod:
                prod[campo] = None
            if prod[campo] == '':
                prod[campo] = None
        # Padroniza valores
        if prod['valor_unitario'] is not None:
            try:
                prod['valor_unitario'] = f"{float(str(prod['valor_unitario']).replace(',', '.')):.2f}"
            except Exception:
                prod['valor_unitario'] = None
        if prod['valor_total'] is not None:
            try:
                prod['valor_total'] = f"{float(str(prod['valor_total']).replace(',', '.')):.2f}"
            except Exception:
                prod['valor_total'] = None
        if prod['quantidade'] is not None:
            try:
                prod['quantidade'] = float(str(prod['quantidade']).replace(',', '.'))
            except Exception:
                prod['quantidade'] = None
    # 5. Parcelas
    parcelas = data['nota_fiscal'].get('parcelas')
    if not parcelas or not isinstance(parcelas, dict):
        # Se vier como lista, converte
        if isinstance(parcelas, list):
            itens = []
            for p in parcelas:
                if isinstance(p, dict):
                    itens.append({
                        'numero': p.get('numero'),
                        'data_vencimento': p.get('data_vencimento'),
                        'valor': p.get('valor')
                    })
            data['nota_fiscal']['parcelas'] = {
                'quantidade_total': max(1, len(itens)),
                'itens': itens if itens else [{'numero': None, 'data_vencimento': None, 'valor': None}]
            }
        else:
            # Garante estrutura mínima
            data['nota_fiscal']['parcelas'] = {
                'quantidade_total': 1,
                'itens': [{'numero': None, 'data_vencimento': None, 'valor': None}]
            }
    else:
        # Garante estrutura mínima
        if 'quantidade_total' not in parcelas or not parcelas['quantidade_total']:
            parcelas['quantidade_total'] = 1
        if 'itens' not in parcelas or not isinstance(parcelas['itens'], list) or len(parcelas['itens']) == 0:
            parcelas['itens'] = [{'numero': None, 'data_vencimento': None, 'valor': None}]
        # Corrige cada item
        for item in parcelas['itens']:
            for campo in ['numero', 'data_vencimento', 'valor']:
                if campo not in item:
                    item[campo] = None
                if item[campo] == '':
                    item[campo] = None
    # 6. Classificação da despesa
    if 'classificacao_despesa' not in data['nota_fiscal']:
        data['nota_fiscal']['classificacao_despesa'] = None
    descs = ' '.join([str(p.get('descricao', '')).lower() for p in data['nota_fiscal']['produtos']])
    categorias = [
        (['óleo diesel', 'combustível', 'lubrificante'], 'MANUTENÇÃO E OPERAÇÃO'),
        (['tubo', 'material hidráulico', 'cimento'], 'INFRAESTRUTURA E UTILIDADES'),
        (['notebook', 'computador', 'máquina', 'implemento', 'veículo'], 'INVESTIMENTOS'),
        (['honorários', 'taxa bancária'], 'ADMINISTRATIVAS'),
        (['semente', 'fertilizante', 'defensivo', 'corretivo'], 'INSUMOS AGRÍCOLAS'),
        (['seguro'], 'SEGUROS E PROTEÇÃO'),
        (['itr', 'iptu', 'ipva', 'taxa'], 'IMPOSTOS E TAXAS'),
    ]
    found = None
    for palavras, classe in categorias:
        for palavra in palavras:
            if palavra in descs:
                found = classe
                break
        if found:
            break
    data['nota_fiscal']['classificacao_despesa'] = found if found else None
    return data
import re
import json
import pdfplumber

# Função principal de validação/correção do JSON extraído da NF-e

def validar_corrigir_nfe(texto_pdf, json_extraido):
    """
    Valida e corrige o JSON extraído da NF-e conforme as regras do projeto.
    - Corrige campos obrigatórios se existirem no PDF e não foram extraídos.
    - Se não existir no PDF, deixa como null e reporta em 'issues'.
    - Nunca inventa informação.
    Retorna: dict { 'json': ..., 'issues': [...] }
    """
    issues = []

    # Funções auxiliares para busca de padrões
    def busca_cnpj(texto):
        match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
        return match.group(0) if match else None

    def busca_cpf(texto):
        match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)
        return match.group(0) if match else None

    def busca_data(texto):
        match = re.search(r'\d{2}/\d{2}/\d{4}', texto)
        return match.group(0) if match else None

    def busca_valor(texto):
        match = re.search(r'\d+[\.,]\d{2}', texto)
        if match:
            return match.group(0).replace(',', '.')
        return None

    # 1) fornecedor: razao_social, fantasia, cnpj
    # Razão social
    if not json_extraido['fornecedor'].get('razao_social'):
        # Busca por linha "Razão Social" ou similar
        match = re.search(r'Raz[aã]o Social:?\s*(.+)', texto_pdf, re.IGNORECASE)
        if match:
            json_extraido['fornecedor']['razao_social'] = match.group(1).strip()
            issues.append({"campo": "fornecedor.razao_social", "status": "corrigido", "detalhe": "Encontrado no PDF"})
        else:
            json_extraido['fornecedor']['razao_social'] = None
            issues.append({"campo": "fornecedor.razao_social", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    # Fantasia
    if not json_extraido['fornecedor'].get('fantasia'):
        match = re.search(r'Fantasia:?\s*(.+)', texto_pdf, re.IGNORECASE)
        if match:
            json_extraido['fornecedor']['fantasia'] = match.group(1).strip()
            issues.append({"campo": "fornecedor.fantasia", "status": "corrigido", "detalhe": "Encontrado no PDF"})
        else:
            json_extraido['fornecedor']['fantasia'] = None
            issues.append({"campo": "fornecedor.fantasia", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    # CNPJ
    if not json_extraido['fornecedor'].get('cnpj'):
        cnpj = busca_cnpj(texto_pdf)
        if cnpj:
            json_extraido['fornecedor']['cnpj'] = cnpj
            issues.append({"campo": "fornecedor.cnpj", "status": "corrigido", "detalhe": f"Encontrado no PDF: {cnpj}"})
        else:
            json_extraido['fornecedor']['cnpj'] = None
            issues.append({"campo": "fornecedor.cnpj", "status": "ausente", "detalhe": "Não encontrado no PDF"})

    # 2) faturado: nome, cpf
    if not json_extraido['faturado'].get('nome'):
        match = re.search(r'Nome:?\s*(.+)', texto_pdf, re.IGNORECASE)
        if match:
            json_extraido['faturado']['nome'] = match.group(1).strip()
            issues.append({"campo": "faturado.nome", "status": "corrigido", "detalhe": "Encontrado no PDF"})
        else:
            json_extraido['faturado']['nome'] = None
            issues.append({"campo": "faturado.nome", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    if not json_extraido['faturado'].get('cpf'):
        cpf = busca_cpf(texto_pdf)
        if cpf:
            json_extraido['faturado']['cpf'] = cpf
            issues.append({"campo": "faturado.cpf", "status": "corrigido", "detalhe": f"Encontrado no PDF: {cpf}"})
        else:
            json_extraido['faturado']['cpf'] = None
            issues.append({"campo": "faturado.cpf", "status": "ausente", "detalhe": "Não encontrado no PDF"})

    # 3) nota_fiscal: numero, serie, data_emissao, valor_total
    nota = json_extraido['nota_fiscal']
    if not nota.get('numero'):
        match = re.search(r'Nota Fiscal\s*No?\s*:?\s*(\d+)', texto_pdf, re.IGNORECASE)
        if match:
            nota['numero'] = match.group(1)
            issues.append({"campo": "nota_fiscal.numero", "status": "corrigido", "detalhe": "Encontrado no PDF"})
        else:
            nota['numero'] = None
            issues.append({"campo": "nota_fiscal.numero", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    if not nota.get('serie'):
        match = re.search(r'S[ée]rie:?\s*(\d+)', texto_pdf, re.IGNORECASE)
        if match:
            nota['serie'] = match.group(1)
            issues.append({"campo": "nota_fiscal.serie", "status": "corrigido", "detalhe": "Encontrado no PDF"})
        else:
            nota['serie'] = None
            issues.append({"campo": "nota_fiscal.serie", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    if not nota.get('data_emissao'):
        data = busca_data(texto_pdf)
        if data:
            nota['data_emissao'] = data
            issues.append({"campo": "nota_fiscal.data_emissao", "status": "corrigido", "detalhe": f"Encontrado no PDF: {data}"})
        else:
            nota['data_emissao'] = None
            issues.append({"campo": "nota_fiscal.data_emissao", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    if not nota.get('valor_total'):
        valor = busca_valor(texto_pdf)
        if valor:
            nota['valor_total'] = valor
            issues.append({"campo": "nota_fiscal.valor_total", "status": "corrigido", "detalhe": f"Encontrado no PDF: {valor}"})
        else:
            nota['valor_total'] = None
            issues.append({"campo": "nota_fiscal.valor_total", "status": "ausente", "detalhe": "Não encontrado no PDF"})

    # 4) produtos[]: descricao, quantidade, valor_unitario, valor_total
    for idx, prod in enumerate(nota.get('produtos', [])):
        for campo in ['descricao', 'quantidade', 'valor_unitario', 'valor_total']:
            if not prod.get(campo):
                prod[campo] = None
                issues.append({"campo": f"nota_fiscal.produtos[{idx}].{campo}", "status": "ausente", "detalhe": "Não encontrado no PDF"})

    # 5) parcelas[]: quantidade_total, itens[{numero, data_vencimento, valor}]
    parcelas = nota.get('parcelas', {})
    # Se vier como lista, converte para dict padrão
    if isinstance(parcelas, list):
        # Considera que cada item da lista é uma parcela (item de pagamento)
        parcelas_dict = {
            'quantidade_total': len(parcelas),
            'itens': []
        }
        for p in parcelas:
            if isinstance(p, dict):
                item = {
                    'numero': p.get('numero'),
                    'data_vencimento': p.get('data_vencimento'),
                    'valor': p.get('valor')
                }
                parcelas_dict['itens'].append(item)
        parcelas = parcelas_dict
    # Se vier como dict, segue o fluxo normal
    if 'quantidade_total' not in parcelas:
        parcelas['quantidade_total'] = 1
        issues.append({"campo": "nota_fiscal.parcelas.quantidade_total", "status": "corrigido", "detalhe": "Default 1 (não informado no PDF)"})
    if 'itens' not in parcelas:
        parcelas['itens'] = []
        issues.append({"campo": "nota_fiscal.parcelas.itens", "status": "corrigido", "detalhe": "Default vazio (não informado no PDF)"})
    else:
        for idx, item in enumerate(parcelas['itens']):
            for campo in ['numero', 'data_vencimento', 'valor']:
                if not item.get(campo):
                    item[campo] = None
                    issues.append({"campo": f"nota_fiscal.parcelas.itens[{idx}].{campo}", "status": "ausente", "detalhe": "Não encontrado no PDF"})
    nota['parcelas'] = parcelas

    # 6) classificacao_despesa
    if not nota.get('classificacao_despesa'):
        # Mapeamento por palavras-chave
        descs = ' '.join([str(p.get('descricao', '')).lower() for p in nota.get('produtos', [])])
        classificacoes = [
            (['óleo diesel', 'combustível', 'lubrificante', 'pneu', 'filtro', 'correia', 'peças'], 'MANUTENÇÃO E OPERAÇÃO'),
            (['material hidráulico', 'tubo pvc', 'cimento', 'reforma'], 'INFRAESTRUTURA E UTILIDADES'),
            (['honorários', 'taxa bancária'], 'ADMINISTRATIVAS'),
            (['seguro'], 'SEGUROS E PROTEÇÃO'),
            (['itr', 'iptu', 'ipva', 'taxa'], 'IMPOSTOS E TAXAS'),
            (['semente', 'fertilizante', 'defensivo', 'corretivo'], 'INSUMOS AGRÍCOLAS'),
            (['notebook', 'computador', 'máquina', 'implemento', 'veículo', 'imóvel'], 'INVESTIMENTOS'),
        ]
        found = None
        for palavras, classe in classificacoes:
            for palavra in palavras:
                if palavra in descs:
                    found = classe
                    break
            if found:
                break
        if found:
            nota['classificacao_despesa'] = found
            issues.append({"campo": "nota_fiscal.classificacao_despesa", "status": "corrigido", "detalhe": f"Detectado por palavra-chave: {found}"})
        else:
            nota['classificacao_despesa'] = None
            issues.append({"campo": "nota_fiscal.classificacao_despesa", "status": "ausente", "detalhe": "Não identificado por palavras-chave"})

    return {
        "json": json_extraido,
        "issues": issues
    }
