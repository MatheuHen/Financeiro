from django.contrib import admin
from .models import Pessoas, Classificacao, MovimentoContas, ParcelasContas


@admin.register(Pessoas)
class PessoasAdmin(admin.ModelAdmin):
    list_display = ('nome', 'documento', 'tipo', 'ativo', 'created_at')
    list_filter = ('tipo', 'ativo', 'created_at')
    search_fields = ('nome', 'documento')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'documento', 'tipo')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )


@admin.register(Classificacao)
class ClassificacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'ativo', 'created_at')
    list_filter = ('tipo', 'ativo', 'created_at')
    search_fields = ('descricao',)
    ordering = ('descricao',)


@admin.register(MovimentoContas)
class MovimentoContasAdmin(admin.ModelAdmin):
    list_display = ('numero_nf', 'fornecedor', 'faturado', 'valor_total', 'data_emissao', 'ativo')
    list_filter = ('classificacao', 'ativo', 'data_emissao', 'created_at')
    search_fields = ('numero_nf', 'serie_nf', 'fornecedor__nome', 'faturado__nome')
    ordering = ('-data_emissao', '-created_at')
    
    fieldsets = (
        ('Nota Fiscal', {
            'fields': ('numero_nf', 'serie_nf', 'data_emissao')
        }),
        ('Partes Envolvidas', {
            'fields': ('fornecedor', 'faturado', 'classificacao')
        }),
        ('Valores', {
            'fields': ('valor_total', 'quantidade_parcelas')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ParcelasContas)
class ParcelasContasAdmin(admin.ModelAdmin):
    list_display = ('movimento', 'numero_parcela', 'valor_parcela', 'data_vencimento', 'ativo')
    list_filter = ('ativo', 'data_vencimento', 'created_at')
    search_fields = ('movimento__numero_nf', 'movimento__fornecedor__nome')
    ordering = ('-data_vencimento', 'numero_parcela')
    
    fieldsets = (
        ('Parcela', {
            'fields': ('movimento', 'numero_parcela', 'valor_parcela', 'data_vencimento')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')