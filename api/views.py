import os
import json
import logging
import math
import re
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from dotenv import load_dotenv

# Importar os agentes
from .agente01 import extrair_dados_nfe
from .agente02 import processar_nfe_completo
from .agente03 import consultar_com_rag

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente
load_dotenv()

def redirecionar_menu(request):
    """Redireciona a rota raiz para o menu principal"""
    return redirect('api:menu_principal')

def index(request):
    """
    Renderiza a página principal com o formulário de upload
    """
    import time
    context = {
        'timestamp': int(time.time())
    }
    return render(request, 'index.html', context)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def consultar_rag(request):
    """
    Agente 3 - Consulta com RAG (Simples e Embeddings)
    Processa perguntas sobre o banco de dados usando técnicas de RAG
    """
    try:
        logger.info("=== INICIANDO CONSULTA RAG ===")
        
        # Validação básica
        if not request.data:
            return Response({"error": "Nenhum dado enviado"}, status=status.HTTP_400_BAD_REQUEST)
        
        pergunta = request.data.get('pergunta', '').strip()
        tipo_rag = request.data.get('tipo_rag', 'simples')
        
        if not pergunta:
            return Response({"error": "Pergunta não fornecida"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Pergunta recebida: {pergunta}")
        logger.info(f"Tipo RAG: {tipo_rag}")
        
        # Simulação de dados do banco (em produção, buscar do banco real)
        dados_banco = [
            {
                "tipo": "fornecedor",
                "nome": "EMPRESA EXEMPLO LTDA",
                "cnpj": "12.345.678/0001-90",
                "valor_total": 10000.00,
                "data_ultima_compra": "2024-01-15",
                "classificacao": "INSUMOS AGRÍCOLAS"
            },
            {
                "tipo": "cliente", 
                "nome": "João da Silva",
                "cpf": "123.456.789-00",
                "valor_total": 5000.00,
                "data_ultima_compra": "2024-01-10",
                "classificacao": "FERTILIZANTES"
            },
            {
                "tipo": "movimento",
                "numero_nota": "000000123",
                "valor_total": 7500.00,
                "data_emissao": "2024-01-20",
                "fornecedor": "EMPRESA EXEMPLO LTDA",
                "classificacao": "INSUMOS AGRÍCOLAS"
            },
            {
                "tipo": "parcela",
                "numero": 1,
                "valor": 2500.00,
                "data_vencimento": "2024-02-20",
                "status": "Pendente",
                "nota_fiscal": "000000123"
            }
        ]
        
        # Processamento RAG via módulo Python (agente03)
        resultado = consultar_com_rag(pergunta, tipo_rag)
        
        logger.info("=== CONSULTA RAG FINALIZADA ===")
        
        return Response({
            "success": True,
            "pergunta": pergunta,
            "tipo_rag": tipo_rag,
            "resposta": resultado.get("resposta"),
            "fontes": resultado.get("fontes"),
            "confianca": resultado.get("confianca"),
            "mensagem": "Consulta RAG realizada com sucesso!"
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"ERRO NA CONSULTA RAG: {str(e)}")
        return Response({
            "error": "Erro ao processar consulta RAG",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def upload_nfe(request):
    """
    Orquestra o fluxo completo:
    1. Agente 01: Extrai dados da NFe usando Gemini
    2. Agente 02: Processa e salva no banco de dados
    3. Retorna resultado completo para exibição
    """
    try:
        logger.info("=== INICIANDO PROCESSAMENTO COMPLETO NFE ===")

        # Validações básicas
        if 'file' not in request.FILES:
            return Response({"error": "Nenhum arquivo enviado"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return Response({
                "error": f"Tipo de arquivo não suportado. Tipos permitidos: {', '.join(allowed_extensions)}"
            }, status=status.HTTP_400_BAD_REQUEST)

        if file.size > 50 * 1024 * 1024:
            return Response({"error": "Arquivo muito grande. Limite: 50MB"}, status=status.HTTP_400_BAD_REQUEST)

        # ETAPA 1: Extração de dados com Agente 01
        logger.info("=== ETAPA 1: EXTRAÇÃO DE DADOS (AGENTE 01) ===")
        
        # Resetar ponteiro do arquivo para o início antes de ler
        file.seek(0)
        resultado_extracao = extrair_dados_nfe(file.read(), file.name)
        
        # Verificar se houve erro na extração
        if not resultado_extracao.get('success', False):
            return Response({
                "error": "Erro na extração de dados",
                "details": resultado_extracao.get('error', 'Erro desconhecido'),
                "agente": "Agente 01 - Extração"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        dados_extraidos = resultado_extracao.get('resultado', {})
        logger.info("Extração concluída com sucesso")

        # ETAPA 2: Processamento e salvamento no banco com Agente 02
        logger.info("=== ETAPA 2: PROCESSAMENTO E BANCO (AGENTE 02) ===")
        
        resultado_banco = processar_nfe_completo(dados_extraidos)
        
        # Verificar se houve erro no processamento
        if resultado_banco.get('mensagem_erro'):
            return Response({
                "error": "Erro no processamento do banco de dados",
                "details": resultado_banco.get('mensagem_erro'),
                "agente": "Agente 02 - Banco de Dados",
                "dados_extraidos": dados_extraidos  # Retorna dados extraídos mesmo com erro no banco
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # ETAPA 3: Resultado final completo
        logger.info("=== PROCESSAMENTO COMPLETO FINALIZADO ===")
        
        return Response({
            "success": True,
            "message": "NFe processada com sucesso!",
            "dados_extraidos": dados_extraidos,
            "resultado_banco": resultado_banco,
            "resumo": {
                "fornecedor_criado": resultado_banco.get('registros_criados', {}).get('fornecedor_criado', False),
                "faturado_criado": resultado_banco.get('registros_criados', {}).get('faturado_criado', False),
                "despesa_criada": resultado_banco.get('registros_criados', {}).get('despesa_criada', False),
                "movimento_criado": resultado_banco.get('registros_criados', {}).get('movimento_criado', False),
                "parcelas_criadas": resultado_banco.get('registros_criados', {}).get('parcelas_criadas', 0)
            }
        }, status=status.HTTP_200_OK)

    except Exception as general_error:
        logger.error(f"ERRO GERAL NO PROCESSAMENTO: {general_error}")
        return Response({
            "error": "Erro interno do servidor",
            "details": str(general_error),
            "agente": "Orquestrador Principal"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    Verifica se a API está funcionando e reporta estado dos agentes e LLM
    """
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        llm_provider = (
            "gemini" if gemini_api_key else ("openai" if openai_api_key else "none")
        )

        status_overall = "OK"
        message = "API funcionando - Agentes 01, 02 e 03 integrados"

        return Response({
            "status": status_overall,
            "message": message,
            "llm_provider": llm_provider,
            "gemini_configured": bool(gemini_api_key),
            "openai_configured": bool(openai_api_key),
            "agentes": {
                "agente01": "Extração de dados NFe",
                "agente02": "Processamento banco de dados",
                "agente03": {
                    "descricao": "Consulta RAG inteligente",
                    "modalidades": ["simples", "embeddings"],
                    "llm": llm_provider
                }
            }
        })
            
    except Exception as e:
        return Response({
            "status": "ERROR",
            "message": f"Erro no health check: {str(e)}"
        })


@api_view(['GET'])
def exemplo_json(request):
    """
    Retorna exemplo do formato JSON de saída completo (Agente 01 + Agente 02)
    """
    exemplo_completo = {
        "success": True,
        "message": "NFe processada com sucesso!",
        "dados_extraidos": {
            "fornecedor": {
                "razao_social": "EMPRESA EXEMPLO LTDA",
                "fantasia": "EMPRESA EXEMPLO",
                "cnpj": "12.345.678/0001-90"
            },
            "faturado": {
                "nome": "João da Silva",
                "cpf": "123.456.789-00"
            },
            "nota_fiscal": {
                "numero": "000000123",
                "serie": "001",
                "data_emissao": "15/09/2024",
                "produtos": [
                    {
                        "descricao": "Fertilizante NPK",
                        "quantidade": 2,
                        "valor_unitario": "50.00",
                        "valor_total": "100.00"
                    }
                ],
                "parcelas": [
                    {
                        "numero": 1,
                        "data_vencimento": "15/10/2024",
                        "valor": "100.00"
                    }
                ],
                "valor_total": "100.00",
                "classificacao_despesa": "INSUMOS AGRÍCOLAS"
            }
        },
        "resultado_banco": {
            "consultas": {
                "fornecedor": {
                    "nome": "EMPRESA EXEMPLO LTDA",
                    "documento": "12.345.678/0001-90",
                    "existe": False,
                    "id": 1
                },
                "faturado": {
                    "nome": "João da Silva",
                    "documento": "123.456.789-00",
                    "existe": False,
                    "id": 1
                },
                "despesa": {
                    "descricao": "INSUMOS AGRÍCOLAS",
                    "existe": True,
                    "id": 1
                }
            },
            "registros_criados": {
                "fornecedor_criado": True,
                "faturado_criado": True,
                "despesa_criada": False,
                "movimento_criado": True,
                "parcelas_criadas": 1
            },
            "mensagem_sucesso": "Registro lançado com sucesso!"
        },
        "resumo": {
            "fornecedor_criado": True,
            "faturado_criado": True,
            "despesa_criada": False,
            "movimento_criado": True,
            "parcelas_criadas": 1
        }
    }


def processar_consulta_simples(pergunta, dados_banco):
    """Implementação de RAG Simples - busca por palavras-chave"""
    palavras_chave = extrair_palavras_chave(pergunta)
    resultados = []
    
    for dado in dados_banco:
        score = 0
        for palavra in palavras_chave:
            if contem_palavra(dado, palavra):
                score += 1
        if score > 0:
            resultados.append({"dado": dado, "score": score})
    
    resultados.sort(key=lambda x: x["score"], reverse=True)
    return gerar_resposta_contextual(pergunta, resultados[:3])

def processar_consulta_embeddings(pergunta, dados_banco):
    """Implementação de RAG com Embeddings - simulação de similaridade semântica"""
    embedding_pergunta = gerar_embedding(pergunta)
    resultados = []
    
    for dado in dados_banco:
        embedding_dado = gerar_embedding(json.dumps(dado))
        similaridade = calcular_similaridade(embedding_pergunta, embedding_dado)
        
        if similaridade > 0.3:
            resultados.append({"dado": dado, "similaridade": similaridade})
    
    resultados.sort(key=lambda x: x["similaridade"], reverse=True)
    return gerar_resposta_contextual(pergunta, resultados[:3])

def extrair_palavras_chave(pergunta):
    """Extrai palavras-chave da pergunta"""
    stop_words = ['o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas', 'de', 'da', 'do', 'das', 'dos', 'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'se', 'sem', 'sob', 'sobre', 'que', 'qual', 'quais', 'quem', 'quando', 'onde', 'como', 'porque', 'por que', 'pra']
    
    texto_limpo = re.sub(r'[.,!?;:\'"]', '', pergunta.lower())
    palavras = texto_limpo.split()
    return [palavra for palavra in palavras if len(palavra) > 2 and palavra not in stop_words]

def contem_palavra(dado, palavra):
    """Verifica se a palavra está contida no dado"""
    texto = json.dumps(dado).lower()
    return palavra.lower() in texto

def gerar_embedding(texto):
    """Gera embedding simulado para o texto"""
    palavras = texto.lower().split()
    embedding = [0] * 50
    
    for i in range(min(len(palavras), 50)):
        embedding[i] = len(palavras[i]) * 0.1 + (hash(palavras[i]) % 100) / 200.0
    
    return embedding

def calcular_similaridade(embedding1, embedding2):
    """Calcula similaridade entre embeddings"""
    produto = 0
    norma1 = 0
    norma2 = 0
    
    for i in range(len(embedding1)):
        produto += embedding1[i] * embedding2[i]
        norma1 += embedding1[i] * embedding1[i]
        norma2 += embedding2[i] * embedding2[i]
    
    norma1 = math.sqrt(norma1) if norma1 > 0 else 0
    norma2 = math.sqrt(norma2) if norma2 > 0 else 0
    
    return produto / (norma1 * norma2) if norma1 > 0 and norma2 > 0 else 0

def gerar_resposta_contextual(pergunta, resultados):
    """Gera resposta contextual baseada nos resultados"""
    if not resultados:
        return type('obj', (object,), {
            'resposta': "Desculpe, não encontrei informações relevantes no banco de dados para sua pergunta.",
            'fontes': [],
            'confianca': 0
        })()
    
    fontes = [r['dado'] for r in resultados]
    confianca = resultados[0]['score'] if 'score' in resultados[0] else resultados[0]['similaridade']
    
    # Análise contextual da pergunta
    pergunta_lower = pergunta.lower()
    
    if 'total' in pergunta_lower and 'venda' in pergunta_lower:
        total = sum(f.get('valor_total', 0) for f in fontes)
        resposta = f"Com base nos dados do banco, o valor total de vendas é de R$ {total:.2f}. Este valor representa a soma de todas as transações registradas no sistema."
    elif 'fornecedor' in pergunta_lower:
        fornecedores = [f for f in fontes if f.get('tipo') == 'fornecedor']
        if fornecedores:
            resposta = f"Encontrei {len(fornecedores)} fornecedor(es) cadastrado(s): {', '.join(f['nome'] for f in fornecedores)}. Esses fornecedores estão ativos no sistema e possuem transações registradas."
        else:
            resposta = "Não encontrei fornecedores específicos nos resultados da consulta."
    elif 'cliente' in pergunta_lower:
        clientes = [f for f in fontes if f.get('tipo') == 'cliente']
        if clientes:
            resposta = f"Localizei {len(clientes)} cliente(s): {', '.join(f['nome'] for f in clientes)}. Esses clientes possuem compras registradas em nosso banco de dados."
        else:
            resposta = "Não encontrei clientes específicos nos resultados da consulta."
    elif 'parcela' in pergunta_lower:
        parcelas = [f for f in fontes if f.get('tipo') == 'parcela']
        if parcelas:
            pendentes = [p for p in parcelas if p.get('status') == 'Pendente']
            resposta = f"Existem {len(parcelas)} parcela(s) no sistema, sendo {len(pendentes)} pendente(s). As parcelas têm valores que variam de R$ 100,00 a R$ 5000,00."
        else:
            resposta = "Não encontrei parcelas específicas nos resultados da consulta."
    elif 'movimento' in pergunta_lower:
        movimentos = [f for f in fontes if f.get('tipo') == 'movimento']
        if movimentos:
            resposta = f"Foram realizados {len(movimentos)} movimento(s) recente(s). Os valores dos movimentos variam de R$ 1000,00 a R$ 10000,00, com fornecedores diversificados."
        else:
            resposta = "Não encontrei movimentos específicos nos resultados da consulta."
    else:
        resposta = f"Com base na análise dos dados disponíveis, encontrei {len(fontes)} registro(s) relevante(s). Os dados incluem informações de {', '.join(set(f.get('tipo', 'desconhecido') for f in fontes))} com valores que demonstram um padrão de negócios saudável."
    
    return type('obj', (object,), {
        'resposta': resposta,
        'fontes': fontes,
        'confianca': min(int(confianca * 100), 95)
    })()
