from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Classificacao


class Command(BaseCommand):
    help = 'Configura dados iniciais do sistema'

    def handle(self, *args, **options):
        self.stdout.write('Configurando dados iniciais...')
        
        # Criar classificações padrão
        classificacoes = [
            'INSUMOS AGRÍCOLAS',
            'MANUTENÇÃO E OPERAÇÃO',
            'RECURSOS HUMANOS',
            'SERVIÇOS OPERACIONAIS',
            'INFRAESTRUTURA E UTILIDADES',
            'ADMINISTRATIVAS',
            'SEGUROS E PROTEÇÃO',
            'IMPOSTOS E TAXAS',
            'INVESTIMENTOS'
        ]
        
        for desc in classificacoes:
            classificacao, created = Classificacao.objects.get_or_create(
                descricao=desc,
                defaults={'tipo': 'DESPESA'}
            )
            if created:
                self.stdout.write(f'✓ Classificação criada: {desc}')
            else:
                self.stdout.write(f'- Classificação já existe: {desc}')
        
        # Criar superusuário se não existir
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@financeiro.com',
                password='admin123'
            )
            self.stdout.write('✓ Superusuário criado: admin/admin123')
        else:
            self.stdout.write('- Superusuário já existe')
        
        self.stdout.write(
            self.style.SUCCESS('Configuração inicial concluída!')
        )