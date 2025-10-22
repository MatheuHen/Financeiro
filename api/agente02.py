"""
Agente 02 - IA de Manipulação do Banco de Dados
Responsável por consultar, verificar e criar registros no banco de dados
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.db import transaction
from django.utils.dateparse import parse_date
from .models import Pessoas, Classificacao, MovimentoContas, ParcelasContas

# Configura logging
logger = logging.getLogger(__name__)


def consultar_fornecedor(nome, cnpj):
    """
    Consulta se um fornecedor existe na tabela Pessoas
    
    Args:
        nome (str): Nome do fornecedor
        cnpj (str): CNPJ do fornecedor
        
    Returns:
        tuple: (existe: bool, pessoa_id: int ou None)
    """
    try:
        if not cnpj or not cnpj.strip():
            return False, None
            
        # Limpar CNPJ (remover pontos, barras e hífens)
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()
        
        # Buscar por CNPJ exato primeiro
        pessoa = Pessoas.objects.filter(
            documento__icontains=cnpj_limpo,
            tipo='FORNECEDOR',
            ativo=True
        ).first()
        
        if pessoa:
            logger.info(f"Fornecedor encontrado: {pessoa.nome} (ID: {pessoa.id})")
            return True, pessoa.id
            
        # Se não encontrou por CNPJ, tentar por nome
        if nome and nome.strip():
            pessoa = Pessoas.objects.filter(
                nome__icontains=nome.strip(),
                tipo='FORNECEDOR',
                ativo=True
            ).first()
            
            if pessoa:
                logger.info(f"Fornecedor encontrado por nome: {pessoa.nome} (ID: {pessoa.id})")
                return True, pessoa.id
        
        logger.info(f"Fornecedor não encontrado: {nome} - {cnpj}")
        return False, None
        
    except Exception as e:
        logger.error(f"Erro ao consultar fornecedor: {e}")
        return False, None


def consultar_faturado(nome, cpf):
    """
    Consulta se um faturado existe na tabela Pessoas
    
    Args:
        nome (str): Nome do faturado
        cpf (str): CPF do faturado
        
    Returns:
        tuple: (existe: bool, pessoa_id: int ou None)
    """
    try:
        if not cpf or not cpf.strip():
            return False, None
            
        # Limpar CPF (remover pontos e hífens)
        cpf_limpo = cpf.replace('.', '').replace('-', '').strip()
        
        # Buscar por CPF exato primeiro
        pessoa = Pessoas.objects.filter(
            documento__icontains=cpf_limpo,
            tipo='FATURADO',
            ativo=True
        ).first()
        
        if pessoa:
            logger.info(f"Faturado encontrado: {pessoa.nome} (ID: {pessoa.id})")
            return True, pessoa.id
            
        # Se não encontrou por CPF, tentar por nome
        if nome and nome.strip():
            pessoa = Pessoas.objects.filter(
                nome__icontains=nome.strip(),
                tipo='FATURADO',
                ativo=True
            ).first()
            
            if pessoa:
                logger.info(f"Faturado encontrado por nome: {pessoa.nome} (ID: {pessoa.id})")
                return True, pessoa.id
        
        logger.info(f"Faturado não encontrado: {nome} - {cpf}")
        return False, None
        
    except Exception as e:
        logger.error(f"Erro ao consultar faturado: {e}")
        return False, None


def consultar_despesa(descricao):
    """
    Consulta se uma classificação de despesa existe
    
    Args:
        descricao (str): Descrição da classificação
        
    Returns:
        tuple: (existe: bool, classificacao_id: int ou None)
    """
    try:
        if not descricao or not descricao.strip():
            return False, None
            
        # Buscar por descrição exata
        classificacao = Classificacao.objects.filter(
            descricao__iexact=descricao.strip(),
            tipo='DESPESA',
            ativo=True
        ).first()
        
        if classificacao:
            logger.info(f"Classificação encontrada: {classificacao.descricao} (ID: {classificacao.id})")
            return True, classificacao.id
            
        logger.info(f"Classificação não encontrada: {descricao}")
        return False, None
        
    except Exception as e:
        logger.error(f"Erro ao consultar classificação: {e}")
        return False, None


def criar_fornecedor(nome, cnpj):
    """
    Cria um novo fornecedor na tabela Pessoas
    
    Args:
        nome (str): Nome do fornecedor
        cnpj (str): CNPJ do fornecedor
        
    Returns:
        int: pessoa_id criado ou None se erro
    """
    try:
        if not nome or not nome.strip():
            logger.error("Nome do fornecedor é obrigatório")
            return None
            
        # Limpar CNPJ
        cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '').strip() if cnpj else ''
        
        pessoa = Pessoas.objects.create(
            nome=nome.strip(),
            documento=cnpj_limpo,
            tipo='FORNECEDOR',
            ativo=True
        )
        
        logger.info(f"Fornecedor criado: {pessoa.nome} (ID: {pessoa.id})")
        return pessoa.id
        
    except Exception as e:
        logger.error(f"Erro ao criar fornecedor: {e}")
        return None


def criar_faturado(nome, cpf):
    """
    Cria um novo faturado na tabela Pessoas
    
    Args:
        nome (str): Nome do faturado
        cpf (str): CPF do faturado
        
    Returns:
        int: pessoa_id criado ou None se erro
    """
    try:
        if not nome or not nome.strip():
            logger.error("Nome do faturado é obrigatório")
            return None
            
        # Limpar CPF
        cpf_limpo = cpf.replace('.', '').replace('-', '').strip() if cpf else ''
        
        pessoa = Pessoas.objects.create(
            nome=nome.strip(),
            documento=cpf_limpo,
            tipo='FATURADO',
            ativo=True
        )
        
        logger.info(f"Faturado criado: {pessoa.nome} (ID: {pessoa.id})")
        return pessoa.id
        
    except Exception as e:
        logger.error(f"Erro ao criar faturado: {e}")
        return None


def criar_despesa(descricao):
    """
    Cria uma nova classificação de despesa
    
    Args:
        descricao (str): Descrição da classificação
        
    Returns:
        int: classificacao_id criado ou None se erro
    """
    try:
        if not descricao or not descricao.strip():
            logger.error("Descrição da classificação é obrigatória")
            return None
            
        classificacao = Classificacao.objects.create(
            descricao=descricao.strip(),
            tipo='DESPESA',
            ativo=True
        )
        
        logger.info(f"Classificação criada: {classificacao.descricao} (ID: {classificacao.id})")
        return classificacao.id
        
    except Exception as e:
        logger.error(f"Erro ao criar classificação: {e}")
        return None


def registrar_movimento(fornecedor_id, faturado_id, classificacao_id, dados_nf):
    """
    Cria um novo movimento na tabela MovimentoContas
    
    Args:
        fornecedor_id (int): ID do fornecedor
        faturado_id (int): ID do faturado
        classificacao_id (int): ID da classificação
        dados_nf (dict): Dados da nota fiscal
        
    Returns:
        int: movimento_id criado ou None se erro
    """
    try:
        # Validar IDs
        if not all([fornecedor_id, faturado_id, classificacao_id]):
            logger.error("IDs de fornecedor, faturado e classificação são obrigatórios")
            return None
            
        # Buscar objetos
        try:
            fornecedor = Pessoas.objects.get(id=fornecedor_id, tipo='FORNECEDOR', ativo=True)
            faturado = Pessoas.objects.get(id=faturado_id, tipo='FATURADO', ativo=True)
            classificacao = Classificacao.objects.get(id=classificacao_id, tipo='DESPESA', ativo=True)
        except Pessoas.DoesNotExist:
            logger.error("Fornecedor ou faturado não encontrado")
            return None
        except Classificacao.DoesNotExist:
            logger.error("Classificação não encontrada")
            return None
            
        # Extrair dados da NF
        numero_nf = dados_nf.get('numero', '')
        serie_nf = dados_nf.get('serie', '')
        data_emissao_str = dados_nf.get('data_emissao', '')
        valor_total_str = dados_nf.get('valor_total', '0')
        parcelas = dados_nf.get('parcelas', [])
        
        # Converter data de emissão
        data_emissao = None
        if data_emissao_str:
            try:
                # Tentar formatos comuns
                if '/' in data_emissao_str:
                    # Formato DD/MM/YYYY
                    parts = data_emissao_str.split('/')
                    if len(parts) == 3:
                        data_emissao = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                else:
                    data_emissao = parse_date(data_emissao_str)
            except (ValueError, IndexError):
                logger.warning(f"Não foi possível converter data: {data_emissao_str}")
                
        # Converter valor total
        try:
            valor_total = Decimal(str(valor_total_str).replace(',', '.'))
        except (ValueError, TypeError):
            logger.warning(f"Valor total inválido: {valor_total_str}, usando 0")
            valor_total = Decimal('0')
            
        # Quantidade de parcelas
        quantidade_parcelas = len(parcelas) if parcelas else 1
        
        movimento = MovimentoContas.objects.create(
            fornecedor=fornecedor,
            faturado=faturado,
            classificacao=classificacao,
            numero_nf=numero_nf,
            serie_nf=serie_nf,
            data_emissao=data_emissao,
            valor_total=valor_total,
            quantidade_parcelas=quantidade_parcelas,
            ativo=True
        )
        
        logger.info(f"Movimento criado: NF {numero_nf} (ID: {movimento.id})")
        return movimento.id
        
    except Exception as e:
        logger.error(f"Erro ao registrar movimento: {e}")
        return None


def criar_parcelas(movimento_id, lista_parcelas):
    """
    Cria as parcelas na tabela ParcelasContas
    
    Args:
        movimento_id (int): ID do movimento
        lista_parcelas (list): Lista de parcelas
        
    Returns:
        list: lista de parcela_ids criados
    """
    try:
        if not movimento_id:
            logger.error("ID do movimento é obrigatório")
            return []
            
        # Buscar movimento
        try:
            movimento = MovimentoContas.objects.get(id=movimento_id, ativo=True)
        except MovimentoContas.DoesNotExist:
            logger.error("Movimento não encontrado")
            return []
            
        if not lista_parcelas:
            logger.warning("Lista de parcelas vazia")
            return []
            
        parcelas_ids = []
        
        for parcela_data in lista_parcelas:
            try:
                numero_parcela = parcela_data.get('numero', 1)
                data_vencimento_str = parcela_data.get('data_vencimento', '')
                valor_parcela_str = parcela_data.get('valor', '0')
                
                # Converter data de vencimento
                data_vencimento = None
                if data_vencimento_str:
                    try:
                        if '/' in data_vencimento_str:
                            # Formato DD/MM/YYYY
                            parts = data_vencimento_str.split('/')
                            if len(parts) == 3:
                                data_vencimento = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                        else:
                            data_vencimento = parse_date(data_vencimento_str)
                    except (ValueError, IndexError):
                        logger.warning(f"Data de vencimento inválida: {data_vencimento_str}")
                        
                # Se não tem data de vencimento, usar data de emissão + 30 dias
                if not data_vencimento:
                    if movimento.data_emissao:
                        data_vencimento = movimento.data_emissao + timedelta(days=30)
                    else:
                        data_vencimento = datetime.now().date() + timedelta(days=30)
                        
                # Converter valor da parcela
                try:
                    valor_parcela = Decimal(str(valor_parcela_str).replace(',', '.'))
                except (ValueError, TypeError):
                    logger.warning(f"Valor da parcela inválido: {valor_parcela_str}, usando valor do movimento")
                    valor_parcela = movimento.valor_total / len(lista_parcelas)
                    
                parcela = ParcelasContas.objects.create(
                    movimento=movimento,
                    numero_parcela=numero_parcela,
                    data_vencimento=data_vencimento,
                    valor_parcela=valor_parcela,
                    ativo=True
                )
                
                parcelas_ids.append(parcela.id)
                logger.info(f"Parcela criada: {numero_parcela}/{len(lista_parcelas)} - R$ {valor_parcela} (ID: {parcela.id})")
                
            except Exception as e:
                logger.error(f"Erro ao criar parcela {numero_parcela}: {e}")
                continue
                
        return parcelas_ids
        
    except Exception as e:
        logger.error(f"Erro ao criar parcelas: {e}")
        return []


@transaction.atomic
def processar_nfe_completo(dados_extraidos):
    """
    Função principal que orquestra todo o processo:
    1. Consulta fornecedor, faturado e despesa
    2. Cria registros que não existem
    3. Registra movimento e parcelas
    4. Retorna resultado completo para exibição
    
    Args:
        dados_extraidos (dict): Dados extraídos da NFe pelo Agente 01
        
    Returns:
        dict: Resultado completo do processamento
    """
    try:
        logger.info("=== INICIANDO PROCESSAMENTO COMPLETO NFE ===")
        
        # Extrair dados
        fornecedor_data = dados_extraidos.get('fornecedor', {})
        faturado_data = dados_extraidos.get('faturado', {})
        nf_data = dados_extraidos.get('nota_fiscal', {})
        
        nome_fornecedor = fornecedor_data.get('razao_social', '')
        cnpj_fornecedor = fornecedor_data.get('cnpj', '')
        nome_faturado = faturado_data.get('nome', '')
        cpf_faturado = faturado_data.get('cpf', '')
        classificacao_despesa = nf_data.get('classificacao_despesa', '')
        
        # 1. Consultar fornecedor
        fornecedor_existe, fornecedor_id = consultar_fornecedor(nome_fornecedor, cnpj_fornecedor)
        
        # 2. Consultar faturado
        faturado_existe, faturado_id = consultar_faturado(nome_faturado, cpf_faturado)
        
        # 3. Consultar classificação de despesa
        despesa_existe, despesa_id = consultar_despesa(classificacao_despesa)
        
        # Resultado das consultas
        consultas = {
            "fornecedor": {
                "nome": nome_fornecedor,
                "documento": cnpj_fornecedor,
                "existe": fornecedor_existe,
                "id": fornecedor_id
            },
            "faturado": {
                "nome": nome_faturado,
                "documento": cpf_faturado,
                "existe": faturado_existe,
                "id": faturado_id
            },
            "despesa": {
                "descricao": classificacao_despesa,
                "existe": despesa_existe,
                "id": despesa_id
            }
        }
        
        # 4. Criar registros que não existem
        registros_criados = {
            "fornecedor_criado": False,
            "faturado_criado": False,
            "despesa_criada": False,
            "movimento_criado": False,
            "parcelas_criadas": 0
        }
        
        # Criar fornecedor se não existe
        if not fornecedor_existe:
            fornecedor_id = criar_fornecedor(nome_fornecedor, cnpj_fornecedor)
            if fornecedor_id:
                registros_criados["fornecedor_criado"] = True
                registros_criados["fornecedor_id"] = fornecedor_id
                consultas["fornecedor"]["id"] = fornecedor_id
                consultas["fornecedor"]["existe"] = True
                
        # Criar faturado se não existe
        if not faturado_existe:
            faturado_id = criar_faturado(nome_faturado, cpf_faturado)
            if faturado_id:
                registros_criados["faturado_criado"] = True
                registros_criados["faturado_id"] = faturado_id
                consultas["faturado"]["id"] = faturado_id
                consultas["faturado"]["existe"] = True
                
        # Criar classificação se não existe
        if not despesa_existe:
            despesa_id = criar_despesa(classificacao_despesa)
            if despesa_id:
                registros_criados["despesa_criada"] = True
                registros_criados["despesa_id"] = despesa_id
                consultas["despesa"]["id"] = despesa_id
                consultas["despesa"]["existe"] = True
                
        # 5. Registrar movimento se temos todos os IDs
        movimento_id = None
        parcelas_ids = []
        mensagem_erro = None
        
        if not fornecedor_id:
            mensagem_erro = "Não foi possível identificar ou criar o fornecedor. Verifique se os dados do fornecedor estão legíveis na NFe."
        elif not faturado_id:
            mensagem_erro = "Não foi possível identificar ou criar o faturado. Verifique se os dados do destinatário estão legíveis na NFe."
        elif not despesa_id:
            mensagem_erro = "Não foi possível identificar a classificação da despesa."
        else:
            movimento_id = registrar_movimento(fornecedor_id, faturado_id, despesa_id, nf_data)
            if movimento_id:
                registros_criados["movimento_criado"] = True
                registros_criados["movimento_id"] = movimento_id
                
                # 6. Criar parcelas
                parcelas_data = nf_data.get('parcelas', [])
                if parcelas_data:
                    parcelas_ids = criar_parcelas(movimento_id, parcelas_data)
                    registros_criados["parcelas_criadas"] = len(parcelas_ids)
                    registros_criados["parcelas_ids"] = parcelas_ids
            else:
                mensagem_erro = "Erro ao criar o movimento financeiro. Verifique os dados da nota fiscal."
                    
        # Resultado final
        resultado = {
            "consultas": consultas,
            "registros_criados": registros_criados,
            "mensagem_sucesso": "Registro lançado com sucesso." if movimento_id else mensagem_erro
        }
        
        logger.info("=== PROCESSAMENTO COMPLETO NFE FINALIZADO ===")
        return resultado
        
    except Exception as e:
        logger.error(f"Erro no processamento completo: {e}")
        return {
            "consultas": {},
            "registros_criados": {},
            "mensagem_erro": f"Erro no processamento: {str(e)}"
        }