from django.db import models
from django.utils import timezone


class Pessoas(models.Model):
    """
    Modelo para armazenar dados de pessoas (fornecedores e faturados)
    """
    TIPO_CHOICES = [
        ('FORNECEDOR', 'Fornecedor'),
        ('FATURADO', 'Faturado'),
    ]
    
    nome = models.CharField(max_length=255, verbose_name="Nome")
    documento = models.CharField(max_length=20, verbose_name="CPF/CNPJ")  # CPF ou CNPJ
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        db_table = 'api_pessoas'
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        indexes = [
            models.Index(fields=['documento']),
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.documento})"


class Classificacao(models.Model):
    """
    Modelo para classificação de despesas e receitas
    """
    TIPO_CHOICES = [
        ('DESPESA', 'Despesa'),
        ('RECEITA', 'Receita'),
    ]
    
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        db_table = 'api_classificacao'
        verbose_name = 'Classificação'
        verbose_name_plural = 'Classificações'
        indexes = [
            models.Index(fields=['descricao']),
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"{self.descricao} ({self.tipo})"


class MovimentoContas(models.Model):
    """
    Modelo para movimentos financeiros (notas fiscais)
    """
    fornecedor = models.ForeignKey(
        Pessoas, 
        on_delete=models.PROTECT, 
        related_name='movimentos_fornecedor',
        verbose_name="Fornecedor"
    )
    faturado = models.ForeignKey(
        Pessoas, 
        on_delete=models.PROTECT, 
        related_name='movimentos_faturado',
        verbose_name="Faturado"
    )
    classificacao = models.ForeignKey(
        Classificacao, 
        on_delete=models.PROTECT,
        verbose_name="Classificação"
    )
    numero_nf = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número NF")
    serie_nf = models.CharField(max_length=10, blank=True, null=True, verbose_name="Série NF")
    data_emissao = models.DateField(blank=True, null=True, verbose_name="Data Emissão")
    valor_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor Total")
    quantidade_parcelas = models.IntegerField(default=1, verbose_name="Quantidade Parcelas")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        db_table = 'api_movimentocontas'
        verbose_name = 'Movimento de Contas'
        verbose_name_plural = 'Movimentos de Contas'
        indexes = [
            models.Index(fields=['fornecedor']),
            models.Index(fields=['faturado']),
            models.Index(fields=['classificacao']),
            models.Index(fields=['data_emissao']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"NF {self.numero_nf} - {self.fornecedor.nome} - R$ {self.valor_total}"


class ParcelasContas(models.Model):
    """
    Modelo para parcelas dos movimentos financeiros
    """
    movimento = models.ForeignKey(
        MovimentoContas, 
        on_delete=models.CASCADE, 
        related_name='parcelas',
        verbose_name="Movimento"
    )
    numero_parcela = models.IntegerField(verbose_name="Número da Parcela")
    data_vencimento = models.DateField(verbose_name="Data Vencimento")
    valor_parcela = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor da Parcela")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        db_table = 'api_parcelascontas'
        verbose_name = 'Parcela de Contas'
        verbose_name_plural = 'Parcelas de Contas'
        indexes = [
            models.Index(fields=['movimento']),
            models.Index(fields=['data_vencimento']),
            models.Index(fields=['numero_parcela']),
            models.Index(fields=['ativo']),
        ]
    
    def __str__(self):
        return f"Parcela {self.numero_parcela}/{self.movimento.quantidade_parcelas} - R$ {self.valor_parcela}"