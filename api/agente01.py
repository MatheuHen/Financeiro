"""
Agente 01 - IA de Extração de Dados de NFe
Responsável por processar arquivos de Nota Fiscal e extrair dados estruturados usando Gemini AI
"""

import os
import json
import logging
import re
import time
import hashlib
import math
from dotenv import load_dotenv

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente
load_dotenv()

# Cache simples em memória: mapeia hash do arquivo -> resultado processado
CACHE_EXTRACAO = {}
CACHE_MAX_ITEMS = 100  # limite básico para evitar crescimento sem controle


def _cache_get(file_hash):
    """Recupera resultado do cache"""
    return CACHE_EXTRACAO.get(file_hash)


def _cache_set(file_hash, value):
    """Armazena resultado no cache com política FIFO"""
    # política FIFO simples ao atingir o limite
    if len(CACHE_EXTRACAO) >= CACHE_MAX_ITEMS:
        # remove o primeiro item inserido
        try:
            first_key = next(iter(CACHE_EXTRACAO.keys()))
            CACHE_EXTRACAO.pop(first_key, None)
        except Exception:
            pass
    CACHE_EXTRACAO[file_hash] = value


def _parse_retry_seconds(error_text: str):
    """Tenta extrair o tempo de retry sugerido da mensagem do Gemini (em segundos)."""
    try:
        # Exemplo: "Please retry in 38.652568815s."
        m = re.search(r"Please retry in\s+([0-9]+(?:\.[0-9]+)?)s", error_text)
        if m:
            return int(math.ceil(float(m.group(1))))
        # Exemplo bloco: retry_delay { seconds: 38 }
        m2 = re.search(r"retry_delay\s*\{[^}]*seconds:\s*(\d+)", error_text)
        if m2:
            return int(m2.group(1))
    except Exception:
        pass
    return None


def normalize_money(value):
    """Normaliza valores monetários para formato padrão"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{value}"
    s = str(value).strip()
    if not s:
        return None
    s = re.sub(r"(?i)r\$\s*", "", s)
    if re.search(r",\d{1,2}$", s):
        s = s.replace(".", "").replace(",", ".")
    s = re.sub(r"[^0-9\.-]", "", s)
    if s in ("", ".", "-"):
        return None
    return s


# Dicionário para conversão de números por extenso em português
PT_NUMBERS = {
    'zero': 0, 'um': 1, 'uma': 1, 'dois': 2, 'duas': 2, 'três': 3, 'tres': 3, 'quatro': 4,
    'cinco': 5, 'seis': 6, 'sete': 7, 'oito': 8, 'nove': 9, 'dez': 10, 'onze': 11,
    'doze': 12, 'treze': 13, 'quatorze': 14, 'catorze': 14, 'quinze': 15, 'dezesseis': 16,
    'dezessete': 17, 'dezoito': 18, 'dezenove': 19, 'vinte': 20, 'trinta': 30, 'quarenta': 40,
    'cinquenta': 50, 'sessenta': 60, 'setenta': 70, 'oitenta': 80, 'noventa': 90,
    'cem': 100, 'cento': 100, 'duzentos': 200, 'trezentos': 300, 'quatrocentos': 400,
    'quinhentos': 500, 'seiscentos': 600, 'setecentos': 700, 'oitocentos': 800, 'novecentos': 900,
    'mil': 1000
}


def parse_quantity(q):
    """Converte quantidade para número (suporta números por extenso em português)"""
    if q is None:
        return None
    if isinstance(q, (int, float)):
        return int(q) if float(q).is_integer() else float(q)
    s = str(q).strip().lower()
    try:
        if re.match(r"^[0-9]+(\.[0-9]+)?$", s):
            v = float(s)
            return int(v) if v.is_integer() else v
    except Exception:
        pass
    tokens = re.split(r"[\s-]+e\s+|[\s-]+|,", s)
    total = 0
    current = 0
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t in PT_NUMBERS:
            val = PT_NUMBERS[t]
            if val == 1000:
                current = max(1, current) * 1000
                total += current
                current = 0
            else:
                current += val
        else:
            if re.search(r"\d", t):
                try:
                    v = float(t.replace(',', '.'))
                    current += v
                except Exception:
                    continue
    total += current
    if total == 0:
        return None
    return int(total) if float(total).is_integer() else float(total)


# Mapeamento de classificações de despesa com termos relacionados
CLASS_MAP = {
    'INSUMOS AGRÍCOLAS': [
        'semente','sementes','fertilizante','fertilizantes','defensivo','defensivos','agrotóxico','agrotoxico','corretivo','calcário','calcaro','adubo'
    ],
    'MANUTENÇÃO E OPERAÇÃO': [
        'óleo diesel','oleo diesel','diesel','combustível','combustivel','gasolina','etanol','lubrificante','graxa',
        'pneu','pneus','filtro','filtros','correia','correias','parafuso','parafusos','peça','peças','peca','pecas',
        'manutenção','manutencao','reparo','conserto','componentes mecânicos','componentes mecanicos','rolamento','rolamentos','kit cabo de aço','cabo de aço'
    ],
    'RECURSOS HUMANOS': [
        'mão de obra','mao de obra','temporária','temporaria','salário','salario','encargos','folha de pagamento','terceirização','terceirizacao'
    ],
    'SERVIÇOS OPERACIONAIS': [
        'frete','transporte','colheita terceirizada','terceirizada','secagem','armazenagem','armazém','pulverização','pulverizacao','aplicação','aplicacao', 'logística','logistica'
    ],
    'INFRAESTRUTURA E UTILIDADES': [
        'energia elétrica','energia eletrica','energia','arrendamento','aluguel de terras','construção','construcao','reformas','obra',
        'materiais de construção','materiais de construcao','cimento','areia','brita','tijolo','telha','hidráulico','hidraulico','tubo','canos'
    ],
    'ADMINISTRATIVAS': [
        'honorários','honorarios','contábil','contabil','advocatício','advocaticio','agronômico','agronomico',
        'despesa bancária','despesa bancaria','tarifa','taxa bancária','taxa bancaria','boletos','emolumentos','cartório'
    ],
    'SEGUROS E PROTEÇÃO': [
        'seguro agrícola','seguro agricola','seguro','apólice','apolice','premio de seguro','franquia','proteção'
    ],
    'IMPOSTOS E TAXAS': [
        'itr','iptu','ipva','incra','ccir','taxa','imposto','guia','darf','gnre'
    ],
    'INVESTIMENTOS': [
        'aquisição','aquisicao','compra de máquina','maquina','implemento','tratores','colheitadeira','veículo','veiculo','imóvel','imovel','infraestrutura rural','upgrade','capex','equipamento'
    ]
}

ALLOWED_CLASSES = set(CLASS_MAP.keys())


def classify_expense(produtos, atual, texto_ocr=''):
    """Classifica despesa baseada nos produtos e texto OCR"""
    # Se o modelo já trouxe uma das classes válidas, respeitar
    if isinstance(atual, str) and atual.strip().upper() in ALLOWED_CLASSES:
        return atual.strip().upper()

    texto = (
        ' '.join([str(p.get('descricao','')) for p in (produtos or [])]) + ' ' + str(texto_ocr or '')
    ).lower()
    for classe, termos in CLASS_MAP.items():
        for termo in termos:
            if termo in texto:
                return classe
    return ''


def ensure_required_shape(data, raw_json_text=None):
    """Garante que os dados extraídos tenham a estrutura correta"""
    fornecedor = data.get('fornecedor', {}) or {}
    faturado = data.get('faturado', {}) or {}
    nf = data.get('nota_fiscal', {}) or {}

    razao = (fornecedor.get('razao_social') or '').strip()
    fantasia = (fornecedor.get('fantasia') or '')
    cnpj = (fornecedor.get('cnpj') or '').strip()

    nome = (faturado.get('nome') or '').strip()
    cpf = (faturado.get('cpf') or '').strip()

    # Busca em texto_ocr e no JSON bruto
    texto_ocr = str(data.get('texto_ocr') or '')
    dump_json = ''
    try:
        dump_json = json.dumps(data, ensure_ascii=False)
    except Exception:
        pass
    search_space = (texto_ocr + "\n" + (raw_json_text or '') + "\n" + dump_json)
    CPF_RE = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
    if not cnpj:
        m_cnpj = CNPJ_RE.search(search_space)
        if m_cnpj:
            cnpj = m_cnpj.group(0)
    if not cpf:
        m_cpf = CPF_RE.search(search_space)
        if m_cpf:
            cpf = m_cpf.group(0)

    fornecedor_final = {
        'razao_social': razao,
        'fantasia': fantasia if fantasia.strip() else '',
        'cnpj': cnpj or ''
    }
    faturado_final = {
        'nome': nome,
        'cpf': cpf or ''
    }

    numero = (nf.get('numero') or '').strip()
    serie = (nf.get('serie') or '').strip()
    data_emissao = (nf.get('data_emissao') or '').strip()

    produtos_in = nf.get('produtos') or []
    produtos_out = []
    total_calc = 0.0
    for item in produtos_in:
        desc = (str(item.get('descricao') or '')).strip()
        qtd = parse_quantity(item.get('quantidade'))
        if qtd is None:
            qtd = 1
        vu = normalize_money(item.get('valor_unitario'))
        vt = normalize_money(item.get('valor_total'))
        if vt is None and vu is not None:
            try:
                vt = f"{float(str(vu)) * float(qtd):.2f}"
            except Exception:
                pass
        try:
            if vt is not None:
                total_calc += float(str(vt))
        except Exception:
            pass
        produtos_out.append({'descricao': desc, 'quantidade': qtd, 'valor_unitario': vu, 'valor_total': vt})

    parcelas_in = nf.get('parcelas')
    parcelas_out = []
    if isinstance(parcelas_in, list) and len(parcelas_in) > 0:
        for p in parcelas_in:
            valor_p = normalize_money(p.get('valor')) or ''
            parcelas_out.append({
                'numero': p.get('numero') if isinstance(p.get('numero'), (int, float)) else (p.get('numero') or 1),
                'data_vencimento': (p.get('data_vencimento') or ''),
                'valor': valor_p
            })
        if len(parcelas_out) == 1 and not parcelas_out[0]['valor']:
            parcelas_out[0]['valor'] = normalize_money(nf.get('valor_total')) or (f"{total_calc:.2f}" if total_calc > 0 else '')
    else:
        fallback_valor = normalize_money(nf.get('valor_total')) or (f"{total_calc:.2f}" if total_calc > 0 else '')
        parcelas_out = [{ 'numero': 1, 'data_vencimento': data_emissao or '', 'valor': fallback_valor or '' }]

    valor_total = normalize_money(nf.get('valor_total')) or (f"{total_calc:.2f}" if total_calc > 0 else '')
    classificacao = classify_expense(produtos_out, nf.get('classificacao_despesa'), texto_ocr)
    if not classificacao or not str(classificacao).strip():
        # Fallback simples para nunca deixar vazio caso o modelo não preencha
        classificacao = 'ADMINISTRATIVAS'

    return {
        'fornecedor': fornecedor_final,
        'faturado': faturado_final,
        'nota_fiscal': {
            'numero': numero,
            'serie': serie,
            'data_emissao': data_emissao,
            'produtos': produtos_out,
            'parcelas': parcelas_out,
            'valor_total': valor_total,
            'classificacao_despesa': classificacao
        }
    }


def try_parse_json_loose(t: str):
    """Tenta fazer parse do JSON de forma flexível"""
    # tentativa direta
    try:
        return json.loads(t), None
    except Exception as e1:
        # tentar extrair o primeiro bloco JSON grosso modo
        start = t.find('{')
        end = t.rfind('}')
        if start != -1 and end != -1 and end > start:
            raw = t[start:end+1]
            try:
                return json.loads(raw), None
            except Exception as e2:
                return None, f"Falha no parse do bloco bruto: {e2}"
        return None, f"Falha no parse direto: {e1}"


def extrair_dados_nfe(file_content, file_name):
    """
    Função principal para extrair dados de NFe usando Gemini AI
    
    Args:
        file_content: Conteúdo binário do arquivo
        file_name: Nome do arquivo para determinar tipo
        
    Returns:
        dict: Resultado da extração ou erro
    """
    try:
        logger.info("=== INICIANDO EXTRAÇÃO DE DADOS NFE ===")
        
        # Validações básicas
        allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
        file_extension = os.path.splitext(file_name)[1].lower()
        if file_extension not in allowed_extensions:
            return {
                "success": False,
                "error": f"Tipo de arquivo não suportado. Tipos permitidos: {', '.join(allowed_extensions)}"
            }

        if len(file_content) > 50 * 1024 * 1024:
            return {
                "success": False,
                "error": "Arquivo muito grande. Limite: 50MB"
            }

        # Verificar chave da API
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return {
                "success": False,
                "error": "Chave da API do Gemini não configurada",
                "details": "GEMINI_API_KEY não encontrada no arquivo .env"
            }

        # Configurar Gemini
        import google.generativeai as genai
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Verificar cache
        file_hash = hashlib.sha256(file_content).hexdigest()
        cached = _cache_get(file_hash)
        if cached:
            logger.info("Cache hit para este arquivo. Retornando resultado em memória.")
            return {"success": True, "message": "Dados extraídos com sucesso (cache)", "resultado": cached}

        # Preparar prompt
        mime_type = "application/pdf" if file_extension == ".pdf" else f"image/{file_extension[1:]}"
        prompt = (
            "Extraia os dados desta Nota Fiscal e retorne APENAS um JSON no formato:\n\n"
            "{\n"
            "  \"texto_ocr\": \"\",\n"
            "  \"fornecedor\": {\"razao_social\": \"\", \"fantasia\": \"\", \"cnpj\": \"\"},\n"
            "  \"faturado\": {\"nome\": \"\", \"cpf\": \"\"},\n"
            "  \"nota_fiscal\": {\n"
            "    \"numero\": \"\", \"serie\": \"\", \"data_emissao\": \"\",\n"
            "    \"produtos\": [{\"descricao\": \"\", \"quantidade\": 0, \"valor_unitario\": \"\", \"valor_total\": \"\"}],\n"
            "    \"parcelas\": [{\"numero\": 1, \"data_vencimento\": \"\", \"valor\": \"\"}],\n"
            "    \"valor_total\": \"\", \"classificacao_despesa\": \"\"\n"
            "  }\n"
            "}\n\n"
            "REGRAS:\n"
            "- Retorne APENAS o JSON válido.\n"
            "- Preencha \"texto_ocr\" com o texto completo lido do documento.\n"
            "- Se não encontrar um campo, deixe vazio (\"\"), EXCETO \"classificacao_despesa\", que NUNCA deve ficar vazia.\n"
            "- \"classificacao_despesa\" deve ser uma das categorias exatamente como abaixo (escolha a melhor com base na nota):\n"
            "  INSUMOS AGRÍCOLAS | MANUTENÇÃO E OPERAÇÃO | RECURSOS HUMANOS | SERVIÇOS OPERACIONAIS | INFRAESTRUTURA E UTILIDADES | ADMINISTRATIVAS | SEGUROS E PROTEÇÃO | IMPOSTOS E TAXAS | INVESTIMENTOS\n"
            "- Use os exemplos a seguir apenas como referência semântica (não retornar no JSON):\n"
            "  INSUMOS AGRÍCOLAS: Sementes, Fertilizantes, Defensivos Agrícolas, Corretivos.\n"
            "  MANUTENÇÃO E OPERAÇÃO: Combustíveis e Lubrificantes; Peças/Parafusos/Componentes Mecânicos; Manutenção de Máquinas e Equipamentos; Pneus/Filtros/Correias; Ferramentas e Utensílios.\n"
            "  RECURSOS HUMANOS: Mão de Obra Temporária; Salários e Encargos.\n"
            "  SERVIÇOS OPERACIONAIS: Frete e Transporte; Colheita Terceirizada; Secagem e Armazenagem; Pulverização e Aplicação.\n"
            "  INFRAESTRUTURA E UTILIDADES: Energia Elétrica; Arrendamento de Terras; Construções e Reformas; Materiais de Construção.\n"
            "  ADMINISTRATIVAS: Honorários (Contábeis/Advocatícios/Agronômicos); Despesas Bancárias e Financeiras.\n"
            "  SEGUROS E PROTEÇÃO: Seguro Agrícola; Seguro de Ativos (Máquinas/Veículos); Seguro Prestamista.\n"
            "  IMPOSTOS E TAXAS: ITR, IPTU, IPVA, INCRA-CCIR.\n"
            "  INVESTIMENTOS: Aquisição de Máquinas e Implementos; Veículos; Imóveis; Infraestrutura Rural.\n"
            "- Não adicione texto explicativo."
        )

        # Tentar enviar para Gemini com retry
        last_err = None
        for attempt in range(3):
            try:
                response = model.generate_content([
                    prompt,
                    {"mime_type": mime_type, "data": file_content}
                ])
                break
            except Exception as gemini_error:
                last_err = gemini_error
                # Detecta quota 429 e retorna imediatamente com orientação
                msg = str(gemini_error)
                if '429' in msg or 'Quota exceeded' in msg or 'quota' in msg.lower():
                    retry_after = _parse_retry_seconds(msg)
                    return {
                        "success": False,
                        "error": "Limite de cota do Gemini excedido (429)",
                        "details": msg,
                        "retry_after_seconds": retry_after
                    }
                # backoff exponencial: 0.5s, 1s, 2s
                time.sleep(0.5 * (2 ** attempt))
        else:
            # todas as tentativas falharam
            return {
                "success": False,
                "error": "Serviço de extração temporariamente indisponível",
                "details": str(last_err),
                "suggestion": "Tente novamente em alguns segundos ou verifique a sua GEMINI_API_KEY"
            }

        # Processar resposta
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Parse do JSON
        resultado_json, parse_err = try_parse_json_loose(response_text)
        if resultado_json is None:
            logger.error(f"Falha ao parsear JSON do Gemini. Detalhes: {parse_err}. Trecho: {response_text[:300]}")
            return {
                "success": False,
                "error": "Resposta do Gemini não é um JSON válido",
                "details": parse_err,
                "raw_response": response_text[:1000]
            }

        # Processar e normalizar dados
        resultado_processado = ensure_required_shape(resultado_json, raw_json_text=response_text)
        
        # Salvar no cache
        _cache_set(file_hash, resultado_processado)
        
        return {
            "success": True, 
            "message": "Dados extraídos com sucesso", 
            "resultado": resultado_processado
        }

    except Exception as general_error:
        logger.error(f"ERRO GERAL na extração: {general_error}")
        return {
            "success": False,
            "error": "Erro interno do servidor", 
            "details": str(general_error)
        }