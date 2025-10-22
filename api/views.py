import os
import json
import logging
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
    Verifica se a API está funcionando e se o Gemini está configurado
    """
    try:
        # Verifica se chave existe
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return Response({
                "status": "ERROR",
                "message": "GEMINI_API_KEY não configurada",
                "gemini_configured": False
            })
        
        return Response({
            "status": "OK",
            "message": "API funcionando - Agentes 01 e 02 integrados",
            "gemini_configured": True,
            "agentes": {
                "agente01": "Extração de dados NFe",
                "agente02": "Processamento banco de dados"
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
    
    return Response({
        "message": "Exemplo do formato JSON de saída completo (Agente 01 + Agente 02)",
        "exemplo": exemplo_completo
    })
