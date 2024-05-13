from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

class CommandAdm(BaseCommand):
    help = 'Cria o grupo de administradores e atribui permissões'

    def handle(self, *args, **options):
        grupo_admin = Group.objects.create(name='Administradores')
        permissoes = Permission.objects.filter(codename__in=[
            'add_empresa', 'view_empresa_list', 'add_regional', 'view_regional_list',
            'add_unidade', 'view_unidade_list', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios'
        ])
        grupo_admin.permissions.set(permissoes)
        grupo_admin.save()

        self.stdout.write(self.style.SUCCESS('Grupo de administradores criado e configurado com sucesso.'))

class CommandProducao(BaseCommand):
    help = 'Cria o grupo de Produção e atribui permissões'

    def handle(self, *args, **options):
        grupo_producao = Group.objects.create(name='Producao')
        permissoes = Permission.objects.filter(codename__in=[
            'add_empresa', 'view_empresa_list', 'add_regional', 'view_regional_list',
            'add_unidade', 'view_unidade_list', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios', 'access_configuracao'
        ])
        grupo_producao.permissions.set(permissoes)
        grupo_producao.save()

        self.stdout.write(self.style.SUCCESS('Grupo de Producão criado e configurado com sucesso.'))

class CommandUser(BaseCommand):
    help = 'Cria o grupo de usuários comuns e atribui permissões'

    def handle(self, *args, **options):
        # Criando o grupo de usuários comuns
        grupo_comum = Group.objects.create(name='Usuarios')

        # Definindo as permissões que este grupo terá
        permissoes = Permission.objects.filter(codename__in=[
            'view_empresa_list', 'view_regional_list', 'view_unidade_list',
            'access_tela_login', 'access_dashboard', 'access_dossie',
            'access_dados_pessoais', 'access_relatorios'
        ])

        # Atribuindo as permissões ao grupo
        grupo_comum.permissions.set(permissoes)
        grupo_comum.save()

        self.stdout.write(self.style.SUCCESS('Grupo de usuários comuns criado e configurado com sucesso.'))

class CommandDocAccess(BaseCommand):
    help = 'Cria o grupo de acesso a documentos e atribui permissões'

    def handle(self, *args, **options):
        grupo_documentos = Group.objects.create(name='Acesso a Documentos')
        permissoes = Permission.objects.filter(codename__in=[
            'view_tipodocumento', 'edit_tipodocumento', 'delete_tipodocumento', 'create_tipodocumento',
            'view_grupodocumento', 'edit_grupodocumento', 'delete_grupodocumento', 'create_grupodocumento'
        ])
        grupo_documentos.permissions.set(permissoes)
        grupo_documentos.save()

        self.stdout.write(self.style.SUCCESS('Grupo de acesso a documentos criado e configurado com sucesso.'))
