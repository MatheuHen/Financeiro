import os
import math
from dotenv import load_dotenv
from django.db.models import Sum
from .models import Pessoas, Classificacao, MovimentoContas, ParcelasContas

# LLM providers (optional)
try:
    import google.generativeai as genai  # Gemini
except Exception:
    genai = None

try:
    import openai  # OpenAI (legacy API)
except Exception:
    openai = None

load_dotenv()


def consultar_com_rag(pergunta: str, tipo_rag: str = "simples"):
    dados_banco = _dados_banco()

    if tipo_rag == "embeddings":
        resultado = _processar_consulta_embeddings(pergunta, dados_banco)
    else:
        resultado = _processar_consulta_simples(pergunta, dados_banco)

    resposta_llm = _llm_generate_response(pergunta, resultado)

    return {
        "resposta": resposta_llm,
        "fontes": ", ".join({item.get("tipo", "dado") for item in resultado}) or "banco",
        "confianca": _calcular_confianca(pergunta, resultado)
    }


def _processar_consulta_simples(pergunta, dados_banco):
    palavras = _extrair_palavras_chave(pergunta)
    resultados = []
    for dado in dados_banco:
        texto = " ".join(str(v) for v in dado.values()).lower()
        if any(p in texto for p in palavras):
            resultados.append(dado)
    return resultados


def _processar_consulta_embeddings(pergunta, dados_banco):
    emb_pergunta = _gerar_embedding(pergunta)
    resultados = []
    for dado in dados_banco:
        texto = " ".join(str(v) for v in dado.values())
        emb_texto = _gerar_embedding(texto)
        sim = _similaridade(emb_pergunta, emb_texto)
        if sim >= 0.35:
            dado_com_sim = dict(dado)
            dado_com_sim["similaridade"] = round(sim, 2)
            resultados.append(dado_com_sim)
    return sorted(resultados, key=lambda x: x.get("similaridade", 0), reverse=True)


def _extrair_palavras_chave(pergunta):
    base = pergunta.lower()
    especiais = ["fornecedor", "cliente", "movimento", "parcela", "nota", "total", "valor", "cnpj", "cpf"]
    palavras = {p for p in base.replace("?", "").split() if len(p) > 2}
    palavras.update({e for e in especiais if e in base})
    return palavras


def _gerar_embedding(texto):
    texto = texto.lower()
    tokens = [t for t in texto.replace("/", " ").replace("-", " ").split() if t]
    vetor = {}
    for t in tokens:
        vetor[t] = vetor.get(t, 0) + 1
    norma = math.sqrt(sum(v * v for v in vetor.values())) or 1.0
    return {k: v / norma for k, v in vetor.items()}


def _similaridade(e1, e2):
    comum = set(e1.keys()) & set(e2.keys())
    return sum(e1[k] * e2[k] for k in comum)


def _gerar_resposta_contextual(pergunta, resultados):
    if not resultados:
        return (
            "Analisei os dados disponíveis e não encontrei informações diretas "
            "para responder sua pergunta. Tente especificar nomes, tipos (fornecedor, cliente, movimento) "
            "ou termos como valor total, data, CNPJ/CPF."
        )

    partes = []
    for r in resultados[:5]:
        if r.get("tipo") == "fornecedor":
            partes.append(f"Fornecedor: {r.get('nome')} (CNPJ {r.get('cnpj')}) – total {r.get('valor_total')}")
        elif r.get("tipo") == "cliente":
            partes.append(f"Cliente: {r.get('nome')} (CPF {r.get('cpf')}) – total {r.get('valor_total')}")
        elif r.get("tipo") == "movimento":
            partes.append(f"NF {r.get('numero_nota')} – {r.get('fornecedor')} – valor {r.get('valor_total')}")
        elif r.get("tipo") == "parcela":
            partes.append(f"Parcela {r.get('numero')} da NF {r.get('nota_fiscal')} – {r.get('status')} – valor {r.get('valor')}")
        else:
            partes.append(str(r))

    return (
        "Com base na sua pergunta, sintetizei os principais pontos: "
        + "; ".join(partes)
        + ". Caso precise, posso detalhar valores, datas e documentos citados."
    )


def _llm_generate_response(pergunta: str, resultados: list) -> str:
    """
    Usa uma LLM (Gemini ou OpenAI) para sintetizar resposta com base nos resultados.
    Fallback para resposta contextual heurística quando não houver LLM configurada.
    """
    if not resultados:
        return _gerar_resposta_contextual(pergunta, resultados)

    # Preparar contexto compacto
    contexto = []
    for r in resultados[:6]:
        if r.get("tipo") == "fornecedor":
            contexto.append(f"Fornecedor: {r.get('nome')} | CNPJ: {r.get('cnpj')} | Total: {r.get('valor_total')}")
        elif r.get("tipo") == "cliente":
            contexto.append(f"Cliente: {r.get('nome')} | CPF: {r.get('cpf')} | Total: {r.get('valor_total')}")
        elif r.get("tipo") == "movimento":
            contexto.append(f"NF: {r.get('numero_nota')} | Fornecedor: {r.get('fornecedor')} | Valor: {r.get('valor_total')} | Emissao: {r.get('data_emissao')}")
        elif r.get("tipo") == "parcela":
            contexto.append(f"Parcela: {r.get('numero')} | NF: {r.get('nota_fiscal')} | Status: {r.get('status')} | Valor: {r.get('valor')}")
        else:
            contexto.append(str(r))

    prompt = (
        "Você é um assistente financeiro. Com base na pergunta do usuário e nos registros "
        "fornecidos, sintetize uma resposta clara e objetiva, mencionando valores e entidades "
        "relevantes quando possível. Evite inventar dados não presentes nos registros.\n\n"
        f"Pergunta: {pergunta}\n\nRegistros relevantes:\n- " + "\n- ".join(contexto)
    )

    # Tentar Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if genai and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(prompt)
            texto = getattr(resp, "text", None)
            if texto and texto.strip():
                return texto.strip()
        except Exception:
            pass

    # Tentar OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai and openai_key:
        try:
            openai.api_key = openai_key
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente financeiro."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            texto = completion.choices[0].message.get("content")
            if texto and texto.strip():
                return texto.strip()
        except Exception:
            pass

    # Fallback
    return _gerar_resposta_contextual(pergunta, resultados)


def _calcular_confianca(pergunta, resultados):
    if not resultados:
        return 42
    base = 60 + min(40, len(resultados) * 6)
    return base


def _dados_banco():
    dados = []
    for p in Pessoas.objects.filter(ativo=True, tipo='FORNECEDOR')[:100]:
        total = MovimentoContas.objects.filter(fornecedor=p).aggregate(total=Sum('valor_total')).get('total') or 0
        dados.append({
            "tipo": "fornecedor",
            "nome": p.nome,
            "cnpj": p.documento,
            "valor_total": float(total)
        })
    for c in Pessoas.objects.filter(ativo=True, tipo='FATURADO')[:100]:
        total = MovimentoContas.objects.filter(faturado=c).aggregate(total=Sum('valor_total')).get('total') or 0
        dados.append({
            "tipo": "cliente",
            "nome": c.nome,
            "cpf": c.documento,
            "valor_total": float(total)
        })
    for m in MovimentoContas.objects.select_related('fornecedor','faturado','classificacao').all()[:200]:
        dados.append({
            "tipo": "movimento",
            "numero_nota": m.numero_nf or "",
            "valor_total": float(m.valor_total),
            "data_emissao": m.data_emissao.isoformat() if m.data_emissao else "",
            "fornecedor": m.fornecedor.nome if m.fornecedor else "",
            "classificacao": m.classificacao.descricao if m.classificacao else ""
        })
    for p in ParcelasContas.objects.select_related('movimento').all()[:200]:
        dados.append({
            "tipo": "parcela",
            "numero": p.numero_parcela,
            "valor": float(p.valor_parcela),
            "data_vencimento": p.data_vencimento.isoformat() if p.data_vencimento else "",
            "status": "Ativa" if p.ativo else "Inativa",
            "nota_fiscal": p.movimento.numero_nf if p.movimento else ""
        })
    return dados
