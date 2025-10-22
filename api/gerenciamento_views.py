from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
import json
from .models import Pessoas, Classificacao, MovimentoContas, ParcelasContas

def menu_principal(request):
    """Exibe o menu principal do sistema"""
    return render(request, 'menu_principal.html')

def gerenciar_cadastros(request):
    """Exibe o painel principal de gerenciamento"""
    return render(request, 'gerenciar_cadastros.html')

def listar_pessoas(request):
    """API para listar pessoas com filtros e paginação"""
    # Filtros
    search = request.GET.get('search', '')
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    page = int(request.GET.get('page', 1))
    
    # Query base
    queryset = Pessoas.objects.all()
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(nome__icontains=search) | Q(documento__icontains=search)
        )
    
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    if status:
        ativo = status.lower() == 'true'
        queryset = queryset.filter(ativo=ativo)
    
    # Ordenação
    queryset = queryset.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(queryset, 20)  # 20 itens por página
    page_obj = paginator.get_page(page)
    
    # Serializar dados
    pessoas = []
    for pessoa in page_obj:
        pessoas.append({
            'id': pessoa.id,
            'nome': pessoa.nome,
            'documento': pessoa.documento,
            'tipo': pessoa.tipo,
            'ativo': pessoa.ativo,
            'created_at': pessoa.created_at.isoformat(),
        })
    
    return JsonResponse({
        'pessoas': pessoas,
        'total': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
    })

@csrf_exempt
@require_http_methods(["PUT"])
def atualizar_pessoa(request, pessoa_id):
    """API para atualizar dados de uma pessoa"""
    try:
        pessoa = get_object_or_404(Pessoas, id=pessoa_id)
        
        # Verificar se está ativa (só permite editar se ativa)
        if not pessoa.ativo:
            return JsonResponse({
                'error': 'Não é possível editar registros inativos.'
            }, status=400)
        
        # Parse dos dados
        dados = json.loads(request.body)
        
        # Validações
        if not dados.get('nome'):
            return JsonResponse({'error': 'Nome é obrigatório.'}, status=400)
        
        if not dados.get('documento'):
            return JsonResponse({'error': 'Documento é obrigatório.'}, status=400)
        
        # Verificar documento único
        documento_existente = Pessoas.objects.filter(
            documento=dados['documento'],
            tipo=dados['tipo']
        ).exclude(id=pessoa_id).first()
        
        if documento_existente:
            return JsonResponse({
                'error': 'Documento já cadastrado para este tipo de pessoa.'
            }, status=400)
        
        # Atualizar dados
        pessoa.nome = dados['nome']
        pessoa.documento = dados['documento']
        pessoa.tipo = dados['tipo']
        pessoa.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PATCH"])
def alterar_status_pessoa(request, pessoa_id):
    """API para ativar/inativar uma pessoa"""
    try:
        pessoa = get_object_or_404(Pessoas, id=pessoa_id)
        dados = json.loads(request.body)
        
        pessoa.ativo = dados.get('ativo', True)
        pessoa.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def listar_classificacoes(request):
    """API para listar classificações com filtros e paginação"""
    # Filtros
    search = request.GET.get('search', '')
    tipo = request.GET.get('tipo', '')
    status = request.GET.get('status', '')
    page = int(request.GET.get('page', 1))
    
    # Query base
    queryset = Classificacao.objects.all()
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(descricao__icontains=search)
    
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    if status:
        ativo = status.lower() == 'true'
        queryset = queryset.filter(ativo=ativo)
    
    # Ordenação
    queryset = queryset.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page)
    
    # Serializar dados
    classificacoes = []
    for classificacao in page_obj:
        classificacoes.append({
            'id': classificacao.id,
            'descricao': classificacao.descricao,
            'tipo': classificacao.tipo,
            'ativo': classificacao.ativo,
            'created_at': classificacao.created_at.isoformat(),
        })
    
    return JsonResponse({
        'classificacoes': classificacoes,
        'total': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
    })

@csrf_exempt
@require_http_methods(["PUT"])
def atualizar_classificacao(request, classificacao_id):
    """API para atualizar dados de uma classificação"""
    try:
        classificacao = get_object_or_404(Classificacao, id=classificacao_id)
        
        # Verificar se está ativa
        if not classificacao.ativo:
            return JsonResponse({
                'error': 'Não é possível editar registros inativos.'
            }, status=400)
        
        # Parse dos dados
        dados = json.loads(request.body)
        
        # Validações
        if not dados.get('descricao'):
            return JsonResponse({'error': 'Descrição é obrigatória.'}, status=400)
        
        # Atualizar dados
        classificacao.descricao = dados['descricao']
        classificacao.tipo = dados['tipo']
        classificacao.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PATCH"])
def alterar_status_classificacao(request, classificacao_id):
    """API para ativar/inativar uma classificação"""
    try:
        classificacao = get_object_or_404(Classificacao, id=classificacao_id)
        dados = json.loads(request.body)
        
        classificacao.ativo = dados.get('ativo', True)
        classificacao.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def listar_movimentos(request):
    """API para listar movimentos com filtros e paginação"""
    # Filtros
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    
    # Query base
    queryset = MovimentoContas.objects.select_related('fornecedor', 'faturado', 'classificacao').all()
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(numero_nf__icontains=search) | 
            Q(fornecedor__nome__icontains=search) |
            Q(faturado__nome__icontains=search)
        )
    
    # Ordenação
    queryset = queryset.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page)
    
    # Serializar dados
    movimentos = []
    for movimento in page_obj:
        movimentos.append({
            'id': movimento.id,
            'numero_nf': movimento.numero_nf,
            'serie_nf': movimento.serie_nf,
            'data_emissao': movimento.data_emissao.isoformat() if movimento.data_emissao else None,
            'valor_total': str(movimento.valor_total),
            'fornecedor': movimento.fornecedor.nome if movimento.fornecedor else None,
            'faturado': movimento.faturado.nome if movimento.faturado else None,
            'classificacao': movimento.classificacao.descricao if movimento.classificacao else None,
            'quantidade_parcelas': movimento.quantidade_parcelas,
            'ativo': movimento.ativo,
            'created_at': movimento.created_at.isoformat(),
        })
    
    return JsonResponse({
        'movimentos': movimentos,
        'total': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
    })

def listar_parcelas(request):
    """API para listar parcelas com filtros e paginação"""
    # Filtros
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    
    # Query base
    queryset = ParcelasContas.objects.select_related('movimento').all()
    
    # Aplicar filtros
    if search:
        queryset = queryset.filter(
            Q(movimento__numero_nf__icontains=search)
        )
    
    # Ordenação
    queryset = queryset.order_by('-created_at')
    
    # Paginação
    paginator = Paginator(queryset, 20)
    page_obj = paginator.get_page(page)
    
    # Serializar dados
    parcelas = []
    for parcela in page_obj:
        parcelas.append({
            'id': parcela.id,
            'movimento_id': parcela.movimento.id,
            'numero_nf': parcela.movimento.numero_nf,
            'numero_parcela': parcela.numero_parcela,
            'data_vencimento': parcela.data_vencimento.isoformat() if parcela.data_vencimento else None,
            'valor_parcela': str(parcela.valor_parcela),
            'ativo': parcela.ativo,
            'created_at': parcela.created_at.isoformat(),
        })
    
    return JsonResponse({
        'parcelas': parcelas,
        'total': paginator.count,
        'page': page,
        'total_pages': paginator.num_pages,
    })

@csrf_exempt
@require_http_methods(["PUT"])
def atualizar_parcela(request, parcela_id):
    """API para atualizar dados de uma parcela"""
    try:
        parcela = get_object_or_404(ParcelasContas, id=parcela_id)
        
        # Verificar se está ativa
        if not parcela.ativo:
            return JsonResponse({
                'error': 'Não é possível editar registros inativos.'
            }, status=400)
        
        # Parse dos dados
        dados = json.loads(request.body)
        
        # Validações
        if not dados.get('data_vencimento'):
            return JsonResponse({'error': 'Data de vencimento é obrigatória.'}, status=400)
        
        if not dados.get('valor_parcela'):
            return JsonResponse({'error': 'Valor da parcela é obrigatório.'}, status=400)
        
        # Atualizar dados
        from datetime import datetime
        parcela.data_vencimento = datetime.fromisoformat(dados['data_vencimento']).date()
        parcela.valor_parcela = dados['valor_parcela']
        parcela.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)