from django import forms
from jsonschema.exceptions import ValidationError
from .models import Usuario, Area, TipoDocumento
from .models import DocumentoVencido
from django.forms import ModelForm
from .models import ControlePonto
from .models import DocumentoExistenteAuditoria
from .models import RelatorioGerencial
from .models import DocumentoExistente
from .models import Empresa, Regional, Unidade, Cargo, Situacao, SistemaPonto, \
    GrupoDocumento
from .models import Colaborador
from django.forms import DateInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission

class PasswordResetForm(forms.Form):
    email = forms.EmailField()


class ImportarDadosForm(forms.Form):

    """
    Formulário para importar dados de um arquivo CSV.

    Atributos:
        arquivo_CSV (FileField): Campo para selecionar o arquivo CSV a ser importado.
    """
    arquivo_csv = forms.FileField(label='Selecione o arquivo CSV', required=True)


class PesquisaFuncionarioForm(forms.Form):
    """
    Formulário para pesquisa de funcionários.

    Atributos:
        regio (CharField): campo para inserir a região
        regional (CharField): Campo para inserir a regional do funcionário.
        unidade (CharField): Campo para inserir a unidade do funcionário.
        cpf (CharField): Campo para inserir o CPF do funcionário.
        nome_funcionario (CharField): Campo para inserir o nome do funcionário.
        matricula (CharField): Campo para inserir a matrícula do funcionário.
        situacao (ChoiceField): Campo para selecionar a situação do funcionário.
        admissao (DateField): Campo para inserir a data de admissão do funcionário.
        desligamento (DateField): Campo para inserir a data de desligamento do funcionário.
    """
    empresa = forms.ModelChoiceField(queryset=Empresa.objects.all(), required=False)
    regional = forms.ModelChoiceField(queryset=Regional.objects.all(), required=False)
    unidade = forms.ModelChoiceField(queryset=Unidade.objects.all(), required=False)
    cpf = forms.CharField(max_length=14, required=False)
    nome = forms.CharField(max_length=255, required=False)
    matricula = forms.CharField(max_length=20, required=False)
    cargo = forms.ModelChoiceField(queryset=Cargo.objects.all(), required=False)
    status = forms.ModelChoiceField(queryset=Situacao.objects.all(), required=False)
    admissao = forms.DateField(required=False)
    desligamento = forms.DateField(required=False)

class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nome', 'codigo']

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        if not nome:
            raise ValidationError('Nome é obrigatório.')
        if len(nome) > 255:
            raise ValidationError('Nome deve ter no máximo 255 caracteres.')
        return nome

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if Area.objects.filter(codigo=codigo).exists():
            raise ValidationError('Código já cadastrado.')
        return codigo


class GrupoDocumentoForm(forms.ModelForm):
    class Meta:
        model = GrupoDocumento
        fields = ['codigo', 'nome', 'area']

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if GrupoDocumento.objects.filter(codigo=codigo).exists():
            raise ValidationError('Código já cadastrado.')
        return codigo

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        if not nome:
            raise ValidationError('Nome é obrigatório.')
        if len(nome) > 255:
            raise ValidationError('Nome deve ter no máximo 255 caracteres.')
        return nome

    def clean_area_id(self):
        area_id = self.cleaned_data['area']
        if not Area.objects.filter(pk=area_id).exists():
            raise ValidationError('Área não existe.')
        return area_id


class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['id', 'codigo', 'nome', 'pcd', 'obrigatorio', 'valor_legal', 'verifica_assinatura', 'auditoria',
                  'validade', 'tipo_validade', 'exibe_relatorio', 'lista_situacao', 'prioridade']

        def clean_codigo(self):
            codigo = self.cleaned_data['codigo']
            if TipoDocumento.objects.filter(codigo=codigo).exists():
                raise ValidationError('Código já cadastrado.')
            return codigo


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nome']


class RegionalForm(forms.ModelForm):
    class Meta:
        model = Regional
        fields = ['nome', 'empresa']


class UnidadeForm(forms.ModelForm):
    class Meta:
        model = Unidade
        fields = ['nome', 'regional']


class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome']


class SituacaoForm(forms.ModelForm):
    class Meta:
        model = Situacao
        fields = ['nome']


class SistemaPontoForm(forms.ModelForm):
    class Meta:
        model = SistemaPonto
        fields = ['nome']

class ImportarUsuariosForm(forms.Form):
    """
    Formulário para importar usuários a partir de um arquivo.

    Atributos:
        arquivo_excel (FileField): Campo para selecionar o arquivo a ser importado.
    """
    arquivo_excel = forms.FileField()


class RelatoriosPendentesForm(forms.Form):
    """
    Formulário para gerar relatórios pendentes.

    Atributos:
        regional (CharField): Campo para inserir a regional do relatório.
        unidade (CharField): Campo para inserir a unidade do relatório.
        nome (CharField): Campo para inserir o nome do colaborador no relatório.
        matricula (CharField): Campo para inserir a matrícula do colaborador no relatório.
        cpf (CharField): Campo para inserir o CPF do colaborador no relatório.
        cargo (CharField): Campo para inserir o cargo do colaborador no relatório.
        admissao (DateField): Campo para inserir a data de admissão do colaborador no relatório.
        desligamento (DateField): Campo para inserir a data de desligamento do colaborador no relatório.
        situacao (ChoiceField): Campo para selecionar a situação do colaborador no relatório.
        tipo_documento (CharField): Campo para inserir o tipo de documento no relatório.
"""
    empresa = forms.ModelChoiceField(queryset=Empresa.objects.all(), required=False, label='Empresa')
    regional = forms.ModelChoiceField(queryset=Regional.objects.all(), required=False, label='Regional')
    unidade = forms.ModelChoiceField(queryset=Unidade.objects.all(), required=False, label='Unidade')
    nome_colaborador = forms.ModelChoiceField(queryset=Colaborador.objects.all(), required=False,
                                                  label='Nome do Colaborador')
    matricula = forms.CharField(max_length=20, required=False, label='Matrícula')
    cpf = forms.CharField(max_length=14, required=False, label='CPF')
    cargo = forms.ModelChoiceField(queryset=Cargo.objects.all(), required=False, label='Cargo')
    admissao = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False, label='Admissão')
    desligamento = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False, label='Desligamento')
    situacao = forms.ChoiceField(choices=[('', '----------'), ('ativo', 'Ativo'), ('inativo', 'Inativo')],
                                     required=False, label='Situação')
    tipo_documento = forms.ModelChoiceField(queryset=TipoDocumento.objects.all(), required=False,
                                                label='Tipo de Documento')


class DocumentoExistenteForm(ModelForm):
    """
    Formulário para pesquisa de documentos existentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoExistente).
        fields (list): Lista de campos que serão exibidos no formulário.
    """

    model = DocumentoExistente
    fields = [
        "empresa",
        "regional",
        "unidade",
        "colaborador",
        "matricula",
        "cpf",
        "cargo",
        "data_admissao_inicial",
        "data_admissao_final",
        "situacao",
        "tipo_documento",
        "numero_documento",
        "data_documento",
    ]


class DocumentoVencidoForm(ModelForm):
    """
    Formulário para pesquisa de documentos vencidos.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoVencido).
        fields (list): Lista de campos que serão exibidos no formulário.
    """

    model = DocumentoVencido
    fields = [
        "empresa",
        "regional",
        "unidade",
        "nome_colaborador",
        "matricula",
        "cpf",
        "cargo",
        "data_admissao_inicial",
        "data_admissao_final",
        "mes",
        "ano",
        "tipo_documento",
    ]



class ControlePontoForm(ModelForm):
    """
    Formulário para pesquisa de pontos.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (ControlePonto).
        fields (list): Lista de campos que serão exibidos no formulário.
    """

    model = ControlePonto
    fields = [
        "empresa",
        "regional",
        "unidade",
        "nome_colaborador",
        "matricula",
        "data",
        "hora_entrada",
        "hora_saida",
        "justificativa",
    ]


class DocumentoExistenteAuditoriaForm(ModelForm):
    """
    Formulário para pesquisa de documentos existentes de auditorias.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoExistenteAuditoria).
        fields (list): Lista de campos que serão exibidos no formulário.
    """

    model = DocumentoExistenteAuditoria
    fields = [
        "numero",
        "data",
        "tipo",
        "titulo",
        "descricao",
    ]


class RelatorioGerencialForm(ModelForm):
    """
    Formulário para pesquisa de relatórios gerenciais.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (RelatorioGerencial).
        fields (list): Lista de campos que serão exibidos no formulário.
    """

    model = RelatorioGerencial
    fields = [
        "titulo",
        "descricao",
        "data_criacao",
        "data_atualizacao",
    ]

class UserPermissionForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),  # Inicialmente vazio, vamos sobrescrever no __init__
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Usuario
        fields = ['permissions']

    def __init__(self, *args, **kwargs):
        super(UserPermissionForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].queryset = Permission.objects.all()


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('email', 'username', 'password', 'telefone', 'is_active')


