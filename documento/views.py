import pandas as pd
from django.db.models import Q
from django.utils.decorators import method_decorator
from jsonschema import ValidationError
from openpyxl.utils import datetime
from .forms import ImportarUsuariosForm, PesquisaFuncionarioForm
import secrets
from .models import (Area, CartaoPontoInexistente, Regional, Unidade,
                     Cargo, TipoDocumentoCargo, Empresa)
from .models import DocumentoVencido, ColaboradorTipoDocumento
from django.views.generic import DetailView
from .models import ControlePonto
from django.views.generic import ListView
from .models import PendenteASO
from .models import DocumentoAuditoria
from .models import DocumentoExistenteAuditoria
from .models import RelatorioGerencial
from .models import DocumentoExistente
from .models import ImportUsuarioXLSX  # Importe o modelo ImportUsuarioXLSX
from .forms import PasswordResetForm
from .forms import ImportarDadosForm
from .queries import importar_dados, ServicoPendenteASO, ObterDocumentosPendentes, CarregarASOAtivo, CarregarASOInativo, \
    calcular_porcentagens_documentos_obrigatorios_ativos, calcular_porcentagens_documentos_obrigatorios_inativos, \
    ServicoPonto, calcular_porcentagens_ponto_ativos, calcular_porcentagens_ponto_inativos, \
    calcular_porcentagens_obrigatorios_unidade_ativos, DocumentoVencidoService, ServicoValidadeDocumento, \
    ServicoDocumentoAuditoria, calcular_porcentagens_obrigatorios_unidade_inativos, documentos_a_vencer, \
    DocumentoPendenciaQuery
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
import json
import requests
from django.views.decorators.csrf import csrf_exempt
from .models import GrupoDocumento
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetDoneView
from django.contrib.auth.views import LogoutView
from .models import DocumentoPendente
from .forms import RelatoriosPendentesForm
from .models import Situacao
from django.http import JsonResponse
from django.views import View
from django.db.models import Count
from .models import Hyperlinkpdf, Colaborador, TipoDocumento
from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .models import Usuario

#  ********* VIEWS para MENUS SUPERIORES  ************
# VIEW que INICIA o PROJETO

def index(request):
    """
    View para renderizar a página inicial.

    Args:
        request. Objeto HttpRequest contendo os dados da requisição.

    Returns:
        HttpResponse: Resposta HTTP renderizando a página 'documento/.html'.
    """
    return render(request, 'documento/tela_login.html')

@login_required
def dossie(request):
    return render(request, 'documento/dossie.html')

@login_required
def relatorios(request):
    return render(request, 'documento/relatorios.html')


@login_required
def configuracao(request):
    return render(request, 'documento/configuracao.html')

@login_required
def dashboard(request):
    return render(request, 'documento/dashboard.html')

@login_required
def tela_login(request):
    return render(request, 'documento/tela_login.html')

#  ************  Views Para Telas Referente a aba DOSSIE ***********

class PesquisaDossieView(DetailView):
    model = Colaborador
    template_name = 'documento/dossie.html'
    context_object_name = 'colaborador'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['empresa'] = Empresa.objects.all()
        return context

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PesquisaFuncionarioForm(instance=self.object)

        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = PesquisaFuncionarioForm(request.POST, instance=self.object)
        if form.is_valid():
            query = {}
            for field in form.fields:
                value = form.cleaned_data[field]
                if value:
                    query[field] = value

            # Adicionando filtro de região
            if 'empresa' in query:
                empresa_id = query.pop('empresa')
                query['regional__empresa_id'] = empresa_id

            resultados = Colaborador.objects.filter(**query)
            serialized_resultados = [{'nome': resultado.nome, 'cpf': resultado.cpf} for resultado in resultados]
            return JsonResponse(serialized_resultados, safe=False)
        return self.render_to_response(self.get_context_data(form=form))


class CarregarEmpresaView(View):
    def get(self, request, *args, **kwargs):
        empresas = Empresa.objects.all()
        serialized_empresas = [{'id': empresa.id, 'nome': empresa.nome} for empresa in empresas]
        return JsonResponse(serialized_empresas, safe=False)


class CarregarRegionalView(View):
    def get(self, request, *args, **kwargs):
        regionais = Regional.objects.all()  # Corrigido para 'regionais' ao invés de 'regional'
        serialized_regionais = [{'id': regional.id, 'nome': regional.nome} for regional in regionais]
        return JsonResponse(serialized_regionais, safe=False)  # Corrigido para 'serialized_regionais'


class CarregarUnidadesView(View):
    def get(self, request, *args, **kwargs):
        unidades = Unidade.objects.all()
        # print(f"as unidades: {unidades}")
        serialized_unidades = [{'id': unidade.id, 'nome': unidade.nome} for unidade in
                               unidades]  # Corrigido para 'unidade'
        return JsonResponse(serialized_unidades, safe=False)


class CarregarDadosView(View):
    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related(
            'empresa', 'regional', 'unidade'
        ).all()

        serialized_colaboradores2 = []
        for colaborador in colaboradores:
            serialized_colaborador = {
                'id': colaborador.id,
                'nome': colaborador.nome,
                'empresa': colaborador.empresa.nome,
                'regional': colaborador.regional.nome,
                'unidade': colaborador.unidade.nome
            }
            serialized_colaboradores2.append(serialized_colaborador)

        return JsonResponse(serialized_colaboradores2, safe=False)


class CarregarColaboradorView(View):
    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related('empresa', 'regional', 'unidade').all().values(
            'id', 'nome', 'matricula', 'cpf', 'admissao', 'desligamento',
            'empresa__nome', 'regional__nome', 'unidade__nome'
        )

        serialized_colaboradores = [
            {
                'id': colaborador['id'],
                'nome': colaborador['nome'],
                'matricula': colaborador['matricula'],
                'cpf': colaborador['cpf'],
                'admissao': colaborador['admissao'].strftime('%d/%m/%Y') if colaborador['admissao'] else '',
                'desligamento': colaborador['desligamento'].strftime('%d/%m/%Y') if colaborador['desligamento'] else '',
                'empresa': colaborador['empresa__nome'],
                'regional': colaborador['regional__nome'],
                'unidade': colaborador['unidade__nome']
            }
            for colaborador in colaboradores
        ]

        return JsonResponse(serialized_colaboradores, safe=False)


class CarregarCargoView(View):
    def get(self, request, *args, **kwargs):
        cargos = Cargo.objects.all()
        serialized_cargos = [{'id': cargo.id, 'nome': cargo.nome} for cargo in cargos]
        return JsonResponse(serialized_cargos, safe=False)


class CarregarSituacoesView(View):
    def get(self, request, *args, **kwargs):
        situacoes = Situacao.objects.all()
        serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

        return JsonResponse(serialized_situacoes, safe=False)


class ListarResultadoDossieView(View):
    """
    Exibe uma lista com todos os resultados dos dossiês dos colaboradores.
    """

    def get(self, request, *args, **kwargs):
        colaboradores = Colaborador.objects.select_related('status', 'empresa', 'regional', 'unidade', 'cargo').all()
        situacoes = Situacao.objects.all()

        serialized_colaboradores = []
        for colaborador in colaboradores:
            serialized_colaborador = {
                'nome': colaborador.nome,
                'cpf': colaborador.cpf,
                'matricula': colaborador.matricula,
                'situacao': colaborador.status.nome,
                'cargo': colaborador.cargo.nome if colaborador.cargo else '',  # Adicionando o campo cargo
                'admissao': colaborador.admissao.strftime('%d/%m/%Y') if colaborador.admissao else '',
                'desligamento': colaborador.desligamento.strftime('%d/%m/%Y') if colaborador.desligamento else '',
                'empresa': colaborador.empresa.nome if colaborador.empresa else '',
                'regional': colaborador.regional.nome if colaborador.regional else '',
                'unidade': colaborador.unidade.nome if colaborador.unidade else '',
            }
            serialized_colaboradores.append(serialized_colaborador)

        serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

        data = {
            'situacoes': serialized_situacoes,
            'colaboradores': serialized_colaboradores
        }

        return JsonResponse(data, safe=False)

    def post(self, request, *args, **kwargs):
        form = PesquisaFuncionarioForm(request.POST)
        if form.is_valid():
            query = {field: value for field, value in form.cleaned_data.items() if value}

            colaboradores = Colaborador.objects.select_related('status', 'empresa', 'regional', 'unidade',
                                                               'cargo').filter(**query)
            situacoes = Situacao.objects.filter(**query)

            serialized_colaboradores = []
            for colaborador in colaboradores:
                serialized_colaborador = {
                    'nome': colaborador.nome,
                    'cpf': colaborador.cpf,
                    'matricula': colaborador.matricula,
                    'situacao': colaborador.status.nome,
                    'cargo': colaborador.cargo.nome if colaborador.cargo else '',  # Adicionando o campo cargo
                    'admissao': colaborador.admissao.strftime('%d/%m/%Y') if colaborador.admissao else '',
                    'desligamento': colaborador.desligamento.strftime('%d/%m/%Y') if colaborador.desligamento else '',
                    'empresa': colaborador.empresa.nome if colaborador.empresa else '',
                    'regional': colaborador.regional.nome if colaborador.regional else '',
                    'unidade': colaborador.unidade.nome if colaborador.unidade else '',
                }
                serialized_colaboradores.append(serialized_colaborador)

            serialized_situacoes = [{'id': situacao.id, 'nome': situacao.nome} for situacao in situacoes]

            return JsonResponse({'resultados': serialized_colaboradores, 'situacoes': serialized_situacoes}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)

def dados_pessoais(request):
    # Lógica da view, se necessário
    return render(request, 'documento/dados_pessoais.html')


def visualizar_documentos(request):
    # Obter todos os documentos da tabela Hyperlinkpdf
    documentos = Hyperlinkpdf.objects.all()

    # Preparar contexto para o template
    contexto = {
        'documentos': documentos,
        'campos': [field.name for field in Hyperlinkpdf._meta.get_fields()],  # Obter todos os nomes dos campos do modelo
    }

    # Renderizar o template HTML
    return render(request, 'documento/dados_pessoais.html', contexto)


def get_hyperlinkpdf_data(request):
    hyperlinkpdf_data = []
    hyperlinkpdf_objects = Hyperlinkpdf.objects.all()

    for hyperlinkpdf_obj in hyperlinkpdf_objects:
        data = {
            'id': hyperlinkpdf_obj.id,
            'data_upload': hyperlinkpdf_obj.data_upload,
            'caminho': hyperlinkpdf_obj.caminho,
            'documento': hyperlinkpdf_obj.documento.nome,  # Supondo que 'nome' seja um campo relevante do modelo TipoDocumento
            'matricula': hyperlinkpdf_obj.matricula,
            'cpf': hyperlinkpdf_obj.cpf,
            'nome_arquivo': hyperlinkpdf_obj.nome_arquivo,
            'dta_documento': hyperlinkpdf_obj.dta_documento,
            'codigo_documento': hyperlinkpdf_obj.codigo_documento,
        }
        hyperlinkpdf_data.append(data)

    return JsonResponse({'hyperlinkpdf_data': hyperlinkpdf_data})


"""def get_documentos_info(request):
    tipos_documentos = TipoDocumento.objects.all().select_related('grupo_documento', 'hiperlink_documento')
    data = []

    for tipo in tipos_documentos:
        documentos = Hyperlinkpdf.objects.filter(documento=tipo).select_related('colaborador', 'documento')
        documentos_data = [{
            'documento_nome': doc.documento.nome if doc.documento else 'Documento não especificado',
            'colaborador_nome': doc.colaborador.nome if doc.colaborador else 'N/A',
            'colaborador_id': doc.colaborador.id if doc.colaborador else 'N/A',
            'caminho': doc.caminho,
            'cpf': doc.cpf,
            'matricula': doc.matricula
        } for doc in documentos]

        data.append({
            'tipo_documento_id': tipo.id,
            'codigo': tipo.codigo,
            'nome': tipo.nome,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else 'N/A',
            'pcd': tipo.pcd,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'verifica_assinatura': tipo.verifica_assinatura,
            'auditoria': tipo.auditoria,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao,
            'prioridade': tipo.prioridade,
            'hiperlink_documento_id': tipo.hiperlink_documento.id if tipo.hiperlink_documento else 'N/A',
            'documentos': documentos_data
        })

    return JsonResponse(data, safe=False)"""

def get_documentos_info(request):
    # Recuperando todos os tipos de documentos e ordenando pelo campo 'codigo'
    tipos_documentos = TipoDocumento.objects.all().select_related('grupo_documento', 'hiperlink_documento').order_by('codigo')

    data = []

    for tipo in tipos_documentos:
        documentos = Hyperlinkpdf.objects.filter(documento=tipo).select_related('colaborador', 'documento')
        documentos_data = [{
            'documento_nome': doc.documento.nome if doc.documento else 'Documento não especificado',
            'colaborador_nome': doc.colaborador.nome if doc.colaborador else 'N/A',
            'colaborador_id': doc.colaborador.id if doc.colaborador else 'N/A',
            'caminho': doc.caminho,
            'cpf': doc.cpf,
            'matricula': doc.matricula
        } for doc in documentos]

        data.append({
            'tipo_documento_id': tipo.id,
            'codigo': tipo.codigo,
            'nome': tipo.nome,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else 'N/A',
            'pcd': tipo.pcd,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'verifica_assinatura': tipo.verifica_assinatura,
            'auditoria': tipo.auditoria,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao,
            'prioridade': tipo.prioridade,
            'hiperlink_documento_id': tipo.hiperlink_documento.id if tipo.hiperlink_documento else 'N/A',
            'documentos': documentos_data
        })

    return JsonResponse(data, safe=False)


# *************  Views Para Telas Referente ao DASHBOARD **************

class TotalColaboradoresView(View):
    def get(self, request):
        # Conta o total de colaboradores ativos
        total_ativos = Colaborador.objects.filter(status__nome='Ativo').count()

        # Conta o total de colaboradores inativos
        total_inativos = Colaborador.objects.filter(status__nome='Inativo').count()

        # Formata os números para incluir o separador de milhares
        formatted_total_ativos = f"{total_ativos:,}".replace(',', '.')
        formatted_total_inativos = f"{total_inativos:,}".replace(',', '.')

        # Prepara os dados para o JSON de resposta
        data = {
            'total_ativos': formatted_total_ativos,
            'total_inativos': formatted_total_inativos
        }

        return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
class ASOPercentualAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = CarregarASOAtivo.calcular_porcentagens_aso_admissional()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class ASOPercentualInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = CarregarASOInativo.calcular_porcentagens_aso_demissional()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentosObrigatoriosAtivosView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_documentos_obrigatorios_ativos()
        return JsonResponse(percentuais)

@method_decorator(csrf_exempt, name='dispatch')
class DocumentosObrigatoriosInativosView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_documentos_obrigatorios_inativos()
        return JsonResponse(percentuais)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentosPontoAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_ponto_ativos()
        return JsonResponse(percentuais)

@method_decorator(csrf_exempt, name='dispatch')
class DocumentosPontoInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_ponto_inativos()
        return JsonResponse(percentuais)

@method_decorator(csrf_exempt, name='dispatch')
class ObrigatoriosUnidadesAtivoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_obrigatorios_unidade_ativos()
        return JsonResponse(percentuais, safe=False)  # Adicione safe=False aqui

@method_decorator(csrf_exempt, name='dispatch')
class ObrigatoriosUnidadesInativoView(View):
    def get(self, request, *args, **kwargs):
        percentuais = calcular_porcentagens_obrigatorios_unidade_inativos()
        return JsonResponse(percentuais, safe=False)  # Adicione safe=False aqui

@method_decorator(require_GET, name='dispatch')
class AtualizarDocumentosPendentesView(View):
    def get(self, request, *args, **kwargs):
        ObterDocumentosPendentes.atualizar_tabela_documentos_pendentes()
        return JsonResponse({'status': 'Atualização concluída com sucesso!'})


class ObrigatoriosPorUnidadeAtivo(View):
    def get(self, request):
        # Considerando que o modelo possui os campos corretos conforme a imagem e o modelo fornecidos anteriormente
        documentos_obrigatorios = (
            DocumentoPendente.objects
            .filter(obrigatorio=True, desligamento__isnull=True)  # Filtra apenas colaboradores ativos
            .select_related('unidade', 'tipo_documento', 'nome', 'unidade__regional', 'cargo')
            .values(
                'unidade__nome',
                'regional__nome',
                'tipo_documento__nome',
                'nome__nome',
                'nome__matricula',
                'nome__cpf',
                'cargo__nome',
                'admissao'
            )
            .annotate(quantidade=Count('id'))
            .order_by('unidade__nome', 'tipo_documento__nome')
        )

        obrigatorios_por_unidade = {}
        for documento in documentos_obrigatorios:
            unidade_nome = documento['unidade__nome']
            tipo_documento_nome = documento['tipo_documento__nome']

            if unidade_nome not in obrigatorios_por_unidade:
                obrigatorios_por_unidade[unidade_nome] = {
                    'regional': documento['regional__nome'],
                    'documentos': {},
                }

            if tipo_documento_nome not in obrigatorios_por_unidade[unidade_nome]['documentos']:
                obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome] = {
                    'quantidade': 0,
                    'colaboradores': []
                }


            documento_info = obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome]
            documento_info['quantidade'] += documento['quantidade']
            documento_info['colaboradores'].append({
                'cargo': documento['cargo__nome'],
                'nome': documento['nome__nome'],
                'matricula': documento['nome__matricula'],
                'cpf': documento['nome__cpf'],
                'admissao': documento['admissao']
            })

        # Adicionando a contagem total de pendências
        for unidade_info in obrigatorios_por_unidade.values():
            total_pendentes = sum(doc_info['quantidade'] for doc_info in unidade_info['documentos'].values())
            unidade_info['total_pendentes'] = total_pendentes
        lista_unidades = [
            {
                'regional': info['regional'],
                'unidade': unidade,
                'total_pendentes': info['total_pendentes'],
                'documentos': [
                    {
                        'tipo_documento': doc_tipo,
                        'quantidade': doc_info['quantidade'],
                        'colaboradores': doc_info['colaboradores']
                    }
                    for doc_tipo, doc_info in info['documentos'].items()
                ]
            }
            for unidade, info in obrigatorios_por_unidade.items()
        ]

        return JsonResponse(lista_unidades, safe=False)

class ObrigatoriosPorUnidadeInativo(View):
    def get(self, request):
        documentos_obrigatorios = (
            DocumentoPendente.objects
            .filter(obrigatorio=True, desligamento__isnull=False)
            .select_related('unidade', 'tipo_documento', 'nome', 'unidade__regional', 'cargo')
            .values(
                'unidade__nome',
                'unidade__regional__nome',
                'tipo_documento__nome',
                'nome__nome',
                'nome__matricula',
                'nome__cpf',
                'cargo__nome',
                'admissao',
                'desligamento'  # Certifique-se de que 'desligamento' é o nome correto do campo
            )
            .annotate(quantidade=Count('id'))
            .order_by('unidade__nome', 'tipo_documento__nome')
        )
        obrigatorios_por_unidade = {}
        for documento in documentos_obrigatorios:
            unidade_nome = documento['unidade__nome']
            tipo_documento_nome = documento['tipo_documento__nome']

            if unidade_nome not in obrigatorios_por_unidade:
                obrigatorios_por_unidade[unidade_nome] = {
                    'regional': documento['unidade__regional__nome'],
                    'documentos': {},
                }

            if tipo_documento_nome not in obrigatorios_por_unidade[unidade_nome]['documentos']:
                obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome] = {
                    'quantidade': 0,
                    'colaboradores': []
                }

            documento_info = obrigatorios_por_unidade[unidade_nome]['documentos'][tipo_documento_nome]
            documento_info['quantidade'] += documento['quantidade']
            documento_info['colaboradores'].append({
                'unidade': unidade_nome,  # Adicionar o nome da unidade
                'cargo': documento['cargo__nome'],
                'nome': documento['nome__nome'],
                'matricula': documento['nome__matricula'],
                'cpf': documento['nome__cpf'],
                'admissao': documento['admissao'].strftime('%Y-%m-%d') if documento['admissao'] else None,
                'desligamento': documento['desligamento'].strftime('%Y-%m-%d') if documento['desligamento'] else None
            })

        for unidade_info in obrigatorios_por_unidade.values():
            unidade_info['total_pendentes'] = sum(doc_info['quantidade'] for doc_info in unidade_info['documentos'].values())

        lista_unidades = [
            {
                'regional': info['regional'],
                'unidade': unidade,
                'total_pendentes': info['total_pendentes'],
                'documentos': [
                    {
                        'tipo_documento': doc_tipo,
                        'quantidade': doc_info['quantidade'],
                        'colaboradores': doc_info['colaboradores']
                    }
                    for doc_tipo, doc_info in info['documentos'].items()
                ]
            }
            for unidade, info in obrigatorios_por_unidade.items()
        ]
        return JsonResponse(lista_unidades, safe=False)


class DocumentosExistentesView(ListView):
    model = Hyperlinkpdf
    paginate_by = 100  # Ajuste conforme necessário para o volume de dados
    template_name = 'documento/relatorios.html'  # Insira o caminho para o seu template

    def get_queryset(self):
        queryset = super().get_queryset()

        empresa = self.request.GET.get('empresa')
        regional = self.request.GET.get('regional')
        unidade = self.request.GET.get('unidade')
        nome = self.request.GET.get('nome')
        matricula = self.request.GET.get('matricula')
        cpf = self.request.GET.get('cpf')
        cargo = self.request.GET.get('cargo')
        admissao = self.request.GET.get('admissao')
        desligamento = self.request.GET.get('admissao')

        # Filtrar por campos de texto
        if empresa:
            queryset = queryset.filter(empresa__nome__icontains=empresa)
        if regional:
            queryset = queryset.filter(regional__nome__icontains=regional)
        if unidade:
            queryset = queryset.filter(unidade__nome__icontains=unidade)
        if nome:
            queryset = queryset.filter(colaborador__nome__icontains=nome)
        if matricula:
            queryset = queryset.filter(matricula__icontains=matricula)
        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)
        if cargo:
            queryset = queryset.filter(cargo__nome__icontains=cargo)

        # Filtrar por datas de admissão
        if admissao:
            try:
                admissao_inicio_date = datetime.datetime.strptime(admissao, '%Y-%m-%d').date()
                queryset = queryset.filter(colaborador__admissao__gte=admissao_inicio_date)
            except ValueError:
                raise ValidationError("Formato de data de admissão inicial inválido.")
        if desligamento:
            try:
                desligamento = datetime.datetime.strptime(desligamento, '%Y-%m-%d').date()
                queryset = queryset.filter(colaborador__admissao__lte=desligamento)
            except ValueError:
                raise ValidationError("Formato de data de admissão final inválido.")

        return queryset


@method_decorator(csrf_exempt, name='dispatch')
class CarregarDocumentosVencidosView(View):
    def get(self, request, *args, **kwargs):
        documentos = DocumentoVencidoService.copiar_documentos_relevantes()
        return JsonResponse(documentos, safe=False)

def listar_documentos_vencidos(request):
    documentos_vencidos = ServicoValidadeDocumento.documentos_vencidos()
    # data = [{'id': doc.id, 'matricula': doc.matricula, 'data_vencimento': doc.dta_documento} for doc in documentos_vencidos]
    return JsonResponse(documentos_vencidos, safe=False)

def listar_documentos_a_vencer(request):
    documentos_a_vencer = documentos_a_vencer()
    return JsonResponse(documentos_a_vencer, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class CarregarDocumentosAuditoriaView(View):
    def get(self, request, *args, **kwargs):
        documentos = ServicoDocumentoAuditoria.carregar_documentos_auditoria()
        return JsonResponse(documentos, safe=False)

# ************* Views que carregam os dados dos relatórios ************

class CarregarRelatorioPendenteView(View):
    def get(self, request, situacao=None, *args, **kwargs):
        # Filtrando documentos com base na situação passada na URL, se fornecida
        if situacao:
            pendentes = DocumentoPendente.objects.select_related(
                'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_documento'
            ).filter(situacao=situacao)
        else:
            pendentes = DocumentoPendente.objects.select_related(
                'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_documento'
            ).all()  # Se a situação não for fornecida, retornar todos os documentos pendentes

        serialized_pendentes = []
        for pendente in pendentes:
            serialized_pendente = {
                'id': pendente.id,
                'nome': pendente.nome.nome,  # assumindo que Colaborador tem um campo 'nome'
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,  # assumindo que Cargo tem um campo 'nome'
                'admissao': pendente.admissao.strftime('%d/%m/%Y') if pendente.admissao else '',
                'desligamento': pendente.desligamento.strftime('%d/%m/%Y') if pendente.desligamento else '',
                'situacao': pendente.situacao,
                'tipo_documento': pendente.tipo_documento.nome,  # Verifique se este campo está sendo acessado corretamente
                'obrigatorio': pendente.obrigatorio
            }
            serialized_pendentes.append(serialized_pendente)

        return JsonResponse(serialized_pendentes, safe=False)


class CarregarRelatorioExistenteView(View):
    def get(self, request, *args, **kwargs):
        # Consulta otimizada com prefetch_related para carregar todos os dados relacionados
        pendentes = Hyperlinkpdf.objects.select_related(
            'empresa', 'regional', 'unidade', 'cargo', 'documento'
        ).prefetch_related(
            'colaborador__status'  # Corrigido para refletir o relacionamento correto
        )

        data = {'Ativo': [], 'Inativo': [], 'Afastado': []}
        for pendente in pendentes:
            situacao = pendente.colaborador.status.nome  # Acessando o nome da situação através do colaborador
            pendente_data = {
                # 'id': pendente.id,
                'nome': pendente.colaborador.nome,
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome,
                'regional': pendente.regional.nome,
                'unidade': pendente.unidade.nome,
                'cargo': pendente.cargo.nome,
                'admissao': pendente.colaborador.admissao.strftime('%d/%m/%Y') if pendente.colaborador.admissao else '',
                'desligamento': pendente.colaborador.desligamento.strftime('%d/%m/%Y') if pendente.colaborador.desligamento else '',
                'situacao': situacao,  # Situação ao invés de status
                'documento': pendente.documento.nome,
                'obrigatorio': pendente.documento.obrigatorio
            }
            if situacao in data:
                data[situacao].append(pendente_data)

        return JsonResponse(data, safe=False)


class CarregarRelatorioPendenteASOView(View):
    def get(self, request, *args, **kwargs):
        pendentes = PendenteASO.objects.select_related(
            'empresa', 'regional', 'unidade', 'nome', 'cargo', 'tipo_aso', 'status'
        )
        serialized_pendentes = []
        for pendente in pendentes:
            serialized_pendente = {
                'id': pendente.id,
                'nome': pendente.nome.nome if pendente.nome else 'N/A',
                'matricula': pendente.matricula,
                'cpf': pendente.cpf,
                'empresa': pendente.empresa.nome if pendente.empresa else 'N/A',
                'regional': pendente.regional.nome if pendente.regional else 'N/A',
                'unidade': pendente.unidade.nome if pendente.unidade else 'N/A',
                'cargo': pendente.cargo.nome if pendente.cargo else 'N/A',
                'admissao': pendente.admissao.strftime('%d/%m/%Y') if pendente.admissao else 'N/A',
                'desligamento': pendente.desligamento.strftime('%d/%m/%Y') if pendente.desligamento else 'N/A',
                'status': pendente.status.nome if pendente.status else 'N/A',
                'tipo_documento': pendente.tipo_aso.nome if pendente.tipo_aso else 'N/A',
                'aso_existente': 'Sim' if pendente.aso_admissional_existente else 'Não'
            }
            serialized_pendentes.append(serialized_pendente)

        return JsonResponse(serialized_pendentes, safe=False)

class ListarCartaoPontoInexistenteView(View):
    def get(self, request, *args, **kwargs):

        cartoes = CartaoPontoInexistente.objects.select_related(
            'empresa', 'regional', 'unidade', 'colaborador', 'status'
        ).all()
        serialized_cartoes = []
        for cartao in cartoes:
            serialized_cartao = {
                'id': cartao.id,
                'empresa': cartao.empresa.nome if cartao.empresa else 'N/A',
                'regional': cartao.regional.nome if cartao.regional else 'N/A',
                'unidade': cartao.unidade.nome if cartao.unidade else 'N/A',
                'colaborador': cartao.colaborador.nome if cartao.colaborador else 'N/A',
                'matricula': cartao.colaborador.matricula if cartao.colaborador else 'N/A',  # Adicionando a matrícula do colaborador
                'data': cartao.data.strftime('%d/%m/%Y') if cartao.data else 'N/A',
                'existente': 'Sim' if cartao.existente else 'Não',
                'status': cartao.status.nome if cartao.status else 'N/A'
            }
            serialized_cartoes.append(serialized_cartao)

        return JsonResponse(serialized_cartoes, safe=False)

def buscar_pendencias(request):
    data_escolhida = request.GET.get('data', None)
    if data_escolhida:
        resultado = DocumentoPendenciaQuery.buscar_pendencias_por_data(data_escolhida)
        return JsonResponse(resultado)
    else:
        return JsonResponse({'error': 'Data não especificada'}, status=400)
# ***************       Views que apresentam o html do relatório ++++++++++++++++++++++++


class DocumentosPendentesAtivosPorUnidadeView(View):
    def get(self, request):
        # A parte original do seu método get fica intacta aqui
        dados_resumo = []
        documentos_por_unidade = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_desligamento_isnull=True
        ).values('unidade__nome').annotate(total_pendentes=Count('id')).order_by('unidade')
        for doc_unidade in documentos_por_unidade:
            dados_resumo.append({
                'unidade': doc_unidade['unidade__nome'],
                'documentos_pendentes': doc_unidade['total_pendentes']
            })
        response_data = {'dados_resumo': dados_resumo}
        return JsonResponse(response_data, safe=False)


class DocumentosPendentesInativosPorUnidadeView(View):
    def get(self, request):

        # Preparar os dados de resumo por unidade
        dados_resumo = []

        documentos_por_unidade = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_desligamento_isnull=False  # Considerar apenas colaboradores inativos
        ).values('unidade__nome').annotate(total_pendentes=Count('id')).order_by('unidade')

        # Processar cada unidade e o seu total de documentos pendentes
        for doc_unidade in documentos_por_unidade:
            dados_resumo.append({
                'unidade': doc_unidade['unidade__nome'],
                'documentos_pendentes': doc_unidade['total_pendentes']
            })

        response_data = {'dados_resumo': dados_resumo}
        return JsonResponse(response_data, safe=False)

    def documentos_pendentes_por_unidade(self, request, unidade_nome):
        # Este método pode ser chamado de outra view ou URL que passe 'unidade_nome' como parâmetro
        documentos_pendentes = DocumentoPendente.objects.filter(
            obrigatorio=True,
            nome_unidade_nome=unidade_nome,
            nome_desligamento_isnull=False
        ).values('tipo_documento_nome', 'nomenome', 'nome_matricula').distinct()
        dados = list(documentos_pendentes)
        return JsonResponse({'dados': dados})



class RelatorioPendenteView(View):
    def get(self, request):
        form = RelatoriosPendentesForm()
        return render(request, 'documento/relatorios.html', {'form': form})

    def post(self, request):
        form = RelatoriosPendentesForm(request.POST)
        if form.is_valid():

            # Mapeando o nome do formulário para o nome do campo do modelo
            query = {}
            for field, value in form.cleaned_data.items():
                if value:
                    if field == 'nome':
                        query['nome'] = value
                    else:
                        query[field] = value

            documentos = DocumentoPendente.objects.filter(**query)

            return render(request, 'documento/relatorios.html', {
                'form': form,
                'documentos_pendentes': documentos
            })

        return render(request, 'documento/relatorios.html', {'form': form})


class DocumentosExistentesAtivosView(View):
    def get(self, request, unidade_nome, status):
        # Filtrar colaboradores com base no status (ativos/inativos)
        if status == 'ativos':
            colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=True)
        # elif status == 'inativos':
            # colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=False)
        else:
            return JsonResponse({'erro': 'Status inválido'}, status=400)

        # Obter CPFs e/ou matrículas dos colaboradores filtrados
        cpf_matricula_filtrados = colaboradores_filtro.values_list('cpf', 'matricula')

        # Construir uma lista de Q objects para busca no modelo Hyperlinkpdf
        q_objects = Q()
        for cpf, matricula in cpf_matricula_filtrados:
            q_objects |= (Q(cpf=cpf) & Q(matricula=matricula))

        # Filtrar documentos existentes que correspondam aos CPFs e/ou matrículas dos colaboradores
        documentos = Hyperlinkpdf.objects.filter(
            q_objects,
            colaborador__unidade__nome=unidade_nome  # Ajuste esse campo conforme a relação no seu modelo
        ).values('categoria').annotate(total=Count('id')).order_by('categoria')

        dados_resumo = [{'categoria': doc['categoria'], 'total': doc['total']} for doc in documentos]

        return JsonResponse({'dados_resumo': dados_resumo})


class DocumentosExistentesInativosView(View):
    def get(self, request, unidade_nome, status):
        # Filtrar colaboradores inativos
        if status == 'inativos':
            colaboradores_filtro = Colaborador.objects.filter(desligamento__isnull=False)
        else:
            return JsonResponse({'erro': 'Status inválido'}, status=400)

        # Obter CPFs e/ou matrículas dos colaboradores filtrados
        cpf_matricula_filtrados = colaboradores_filtro.values_list('cpf', 'matricula')

        if not cpf_matricula_filtrados:
            return JsonResponse({'dados_resumo': []})

        # Construir uma lista de Q objects para busca no modelo Hyperlinkpdf
        q_objects = Q()
        for cpf, matricula in cpf_matricula_filtrados:
            q_objects |= (Q(cpf=cpf) & Q(matricula=matricula))

        # Filtrar documentos existentes que correspondam aos CPFs e/ou matrículas dos colaboradores
        documentos = Hyperlinkpdf.objects.filter(
            q_objects,
            colaborador__unidade__nome=unidade_nome
        ).values('categoria').annotate(total=Count('id')).order_by('categoria')

        dados_resumo = [{'categoria': doc['categoria'], 'total': doc['total']} for doc in documentos]

        return JsonResponse({'dados_resumo': dados_resumo})


class DocumentoExistenteListView(ListView):
    """
    Exibe a lista de documentos existentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoExistente).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoExistente
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_existentes"

    def get_queryset(self, request):
        """
        Filtra os documentos existentes por regional, unidade, colaborador, matrícula, CPF, cargo, data de admissão, situação, tipo de documento, número do documento e data do documento.

        Argumentos:
            request: O objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos existentes.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        colaborador = request.GET.get("colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        situacao = request.GET.get("situacao")
        tipo_documento = request.GET.get("tipo_documento")
        numero_documento = request.GET.get("numero_documento")
        data_documento = request.GET.get("data_documento")

        if regional:
            queryset = queryset.filter(regional__icontains=regional)

        if unidade:
            queryset = queryset.filter(unidade__icontains=unidade)

        if colaborador:
            queryset = queryset.filter(colaborador__icontains=colaborador)

        if matricula:
            queryset = queryset.filter(matricula__icontains=matricula)

        if cpf:
            queryset = queryset.filter(cpf__icontains=cpf)

        if cargo:
            queryset = queryset.filter(cargo__icontains=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if situacao:
            queryset = queryset.filter(situacao__icontains=situacao)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento__icontains=tipo_documento)

        if numero_documento:
            queryset = queryset.filter(numero_documento__icontains=numero_documento)

        if data_documento:
            queryset = queryset.filter(data_documento__gte=data_documento)

        return queryset


class PendenteASOListView(ListView):
    """
    Exibe a lista de pendências ASO.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (PendenteASO).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = PendenteASO
    template_name = "documento/relatorios.html"
    context_object_name = "pendentes_aso"

    def get_queryset(self, request):
        """
        Filtra as pendências ASO por regional, unidade, nome do colaborador, matrícula, título, descrição, data de criação, data limite, status e prioridade.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com as pendências ASO.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        titulo = request.GET.get("titulo")
        descricao = request.GET.get("descricao")
        data_criacao = request.GET.get("data_criacao")
        status = request.GET.get("status")
        prioridade = request.GET.get("prioridade")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)

        if data_criacao:
            queryset = queryset.filter(data_criacao__gte=data_criacao)

@method_decorator(csrf_exempt, name='dispatch')
class AtualizarASOView(View):
    def get(self, request, *args, **kwargs):
        parametro = request.GET.get('parametro')

        if parametro:
            # Realiza alguma lógica com base no parâmetro
            resposta = f"Recebido o parâmetro {parametro}"
            return JsonResponse({"status": resposta}, status=200)
        else:
            # Retorna uma mensagem dizendo que o método GET não é suportado
            return JsonResponse({"status": "Método GET não suportado"}, status=405)

    def post(self, request, *args, **kwargs):
        def iniciar_atualizacao():
            ServicoPendenteASO.inicializar_pendencias()

        def realizar_atualizacao():
            ServicoPendenteASO.atualizar_pendencias()

        iniciar_atualizacao()
        realizar_atualizacao()

        return JsonResponse({"status": "Atualização iniciada"}, status=202)

@method_decorator(csrf_exempt, name='dispatch')
class AtualizarCartaoPontoView(View):
    def get(self, request, *args, **kwargs):
        parametro = request.GET.get('parametro')

        if parametro:
            # Realiza alguma lógica com base no parâmetro
            resposta = f"Recebido o parâmetro {parametro}"
            return JsonResponse({"status": resposta}, status=200)
        else:
            # Retorna uma mensagem dizendo que o método GET não é suportado
            return JsonResponse({"status": "Método GET não suportado"}, status=405)

    def post(self, request, *args, **kwargs):
        def iniciar_atualizacao():
            ServicoPonto.inicializar_pendencias()

        def realizar_atualizacao():
            ServicoPonto.atualizar_pendencias()


        iniciar_atualizacao()
        realizar_atualizacao()

        return JsonResponse({"status": "Atualização iniciada"}, status=202)

class CartaoPontoInexistenteListView(ListView):
    """
    Exibe a lista de cartões de ponto inexistentes.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (CartaoPontoInexistente).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = CartaoPontoInexistente
    template_name = "documento/relatorios.html"
    context_object_name = "cartoes_ponto_inexistentes"

    def get_queryset(self, request):
        """
        Filtra os cartões de ponto inexistentes por data, regional, unidade, nome do colaborador e situação.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os cartões de ponto inexistentes.
        """

        queryset = super().get_queryset(request)

        data = request.GET.get("data")
        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        situacao = request.GET.get("situacao")

        if data:
            queryset = queryset.filter(data=data)

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if situacao:
            queryset = queryset.filter(situacao=situacao)

        return queryset


class DocumentoVencidoListView(ListView):
    """
    Exibe a lista de documentos vencidos.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoVencido).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoVencido
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_vencidos"

    def get_queryset(self, request):
        """
        Filtra os documentos vencidos por regional, unidade, nome do colaborador, matrícula, CPF, cargo, data de admissão inicial,
        data de admissão final, mês, ano e tipo de documento.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos vencidos.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        mes = request.GET.get("mes")
        ano = request.GET.get("ano")
        tipo_documento = request.GET.get("tipo_documento")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if cpf:
            queryset = queryset.filter(cpf=cpf)

        if cargo:
            queryset = queryset.filter(cargo=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if mes:
            queryset = queryset.filter(mes=mes)

        if ano:
            queryset = queryset.filter(ano=ano)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        return queryset


class DocumentoAVencerListView(ListView):
    """
    Exibe a lista de documentos a vencer.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoAVencer).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoVencido
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_a_vencer"

    def get_queryset(self, request):
        """
        Filtra os documentos a vencer por regional, unidade, nome do colaborador, matrícula, CPF, cargo, data de admissão inicial, data de admissão final, dias de antecedência e tipo de documento.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos a vencer.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome_colaborador")
        matricula = request.GET.get("matricula")
        cpf = request.GET.get("cpf")
        cargo = request.GET.get("cargo")
        data_admissao_inicial = request.GET.get("data_admissao_inicial")
        data_admissao_final = request.GET.get("data_admissao_final")
        dias_antecedencia = request.GET.get("dias_antecedencia")
        tipo_documento = request.GET.get("tipo_documento")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if cpf:
            queryset = queryset.filter(cpf=cpf)

        if cargo:
            queryset = queryset.filter(cargo=cargo)

        if data_admissao_inicial:
            queryset = queryset.filter(data_admissao_inicial__gte=data_admissao_inicial)

        if data_admissao_final:
            queryset = queryset.filter(data_admissao_final__lte=data_admissao_final)

        if dias_antecedencia:
            queryset = queryset.filter(dias_antecedencia=dias_antecedencia)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        return queryset


class DocumentoAuditoriaListView(ListView):
    """
    Exibe a lista de documentos de auditoria.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoAuditoria).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoAuditoria
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_auditoria"

    def get_queryset(self, request):
        """
        Filtra os documentos de auditoria por número, data, tipo, título e descrição.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos de auditoria.
        """

        queryset = super().get_queryset(request)

        numero = request.GET.get("numero")
        data = request.GET.get("data")
        tipo = request.GET.get("tipo")
        titulo = request.GET.get("titulo")
        descricao = request.GET.get("descricao")

        if numero:
            queryset = queryset.filter(numero__icontains=numero)

        if data:
            queryset = queryset.filter(data__gte=data)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)

        return queryset


class DocumentoExistenteAuditoriaListView(ListView):
    """
    Exibe a lista de documentos existentes de auditorias.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (DocumentoExistenteAuditoria).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = DocumentoExistenteAuditoria
    template_name = "documento/relatorios.html"
    context_object_name = "documentos_existentes_auditoria"

    def get_queryset(self, request):
        """
        Filtra os documentos existentes de auditorias por número, data, tipo, título e descrição.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os documentos existentes de auditorias.
        """

        queryset = super().get_queryset(request)

        numero = request.GET.get("numero")
        data = request.GET.get("data")
        tipo = request.GET.get("tipo")
        titulo = request.GET.get("titulo")
        descricao = request.GET.get("descricao")

        if numero:
            queryset = queryset.filter(numero__icontains=numero)

        if data:
            queryset = queryset.filter(data__gte=data)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)

        return queryset


class RelatorioGerencialListView(ListView):
    """
    Exibe a lista de relatórios gerenciais.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (RelatorioGerencial).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = RelatorioGerencial
    template_name = "documento/relatorios.html"
    context_object_name = "relatorios_gerenciais"

    def get_queryset(self, request):
        """
        Filtra os relatórios gerenciais por título, descrição, data de criação e data de atualização.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os relatórios gerenciais.
        """

        queryset = super().get_queryset(request)

        titulo = request.GET.get("titulo")
        descricao = request.GET.get("descricao")
        data_criacao = request.GET.get("data_criacao")
        data_atualizacao = request.GET.get("data_atualizacao")

        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)

        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)

        if data_criacao:
            queryset = queryset.filter(data_criacao__gte=data_criacao)

        if data_atualizacao:
            queryset = queryset.filter(data_atualizacao__lte=data_atualizacao)

        return queryset




class ControlePontoListView(ListView):
    """
    Exibe a lista de pontos do colaborador.

    Atributos:
        model (Model): Modelo que será usado para carregar os dados (ControlePonto).
        template_name (str): Caminho para o template HTML que será usado para renderizar a view.
        context_object_name (str): Nome do objeto que será passado para o template.

    Métodos:
        get_queryset (request): Retorna um QuerySet que será usado para carregar os dados.
    """

    model = ControlePonto
    template_name = "documento/relatorios.html"
    context_object_name = "pontos"

    def get_queryset(self, request):
        """
        Filtra os pontos por regional, unidade, nome do colaborador, matrícula, data, hora de entrada, hora de saída e justificativa.

        Argumentos:
            request: Objeto HttpRequest que contém informações sobre a requisição.

        Retorno:
            QuerySet: QuerySet filtrado com os pontos.
        """

        queryset = super().get_queryset(request)

        regional = request.GET.get("regional")
        unidade = request.GET.get("unidade")
        nome_colaborador = request.GET.get("nome")
        matricula = request.GET.get("matricula")
        data = request.GET.get("data")
        hora_entrada = request.GET.get("hora_entrada")
        hora_saida = request.GET.get("hora_saida")
        justificativa = request.GET.get("justificativa")

        if regional:
            queryset = queryset.filter(regional=regional)

        if unidade:
            queryset = queryset.filter(unidade=unidade)

        if nome_colaborador:
            queryset = queryset.filter(nome_colaborador__icontains=nome_colaborador)

        if matricula:
            queryset = queryset.filter(matricula=matricula)

        if data:
            queryset = queryset.filter(data=data)

        if hora_entrada:
            queryset = queryset.filter(hora_entrada__gte=hora_entrada)

        if hora_saida:
            queryset = queryset.filter(hora_saida__lte=hora_saida)

        if justificativa:
            queryset = queryset.filter(justificativa__icontains=justificativa)

        return queryset


# ********** Views para a aba de Configurações**********


@csrf_exempt
def cadastrar_tipodocumento(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Se os dados recebidos contiverem uma chave "excluir", indica que é uma solicitação de exclusão
            if 'excluir' in data:
                tipo_documento_id = data.get('id')
                tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)
                tipo_documento.delete()
                return HttpResponse(status=204)  # Resposta de sucesso sem conteúdo
            else:
                # Verificar se é uma solicitação de edição
                if 'id' in data:
                    tipo_documento_id = data.get('id')
                    tipo_documento = TipoDocumento.objects.get(id=tipo_documento_id)

                    # Restante do código para editar o tipo de documento

                    # Atualizar os campos do tipo de documento com os novos valores
                    tipo_documento.codigo = data.get('codigo')
                    tipo_documento.nome = data.get('nome')
                    tipo_documento.grupo_documento_id = data.get('grupo_id')
                    tipo_documento.pcd = sim_nao_to_boolean(data.get('pcd'))
                    tipo_documento.valor_legal = sim_nao_to_boolean(data.get('valor_legal'))
                    tipo_documento.verifica_assinatura = sim_nao_to_boolean(data.get('verifica_assinatura'))
                    tipo_documento.auditoria = data.get('auditoria')
                    tipo_documento.validade = data.get('validade')
                    tipo_documento.tipo_validade = data.get('tipo_validade')
                    tipo_documento.exibe_relatorio = sim_nao_to_boolean(data.get('exibe_relatorio'))
                    tipo_documento.lista_situacao = data.get('lista_situacao')
                    tipo_documento.prioridade = data.get('prioridade')
                    tipo_documento.save()

                    return JsonResponse({'status': 'success', 'message': 'Tipo de documento editado com sucesso'})
                else:
                    # Restante do código para criar um novo tipo de documento
                    # Função para converter valores "sim" e "nao" em True e False
                    def sim_nao_to_boolean(value):
                        return value.lower() == 'sim'

                    codigo = data.get('codigo')
                    nome = data.get('nome')
                    grupo_id = data.get('grupo_id')
                    pcd = sim_nao_to_boolean(data.get('pcd'))
                    valor_legal = sim_nao_to_boolean(data.get('valor_legal'))
                    verifica_assinatura = sim_nao_to_boolean(data.get('verifica_assinatura'))
                    auditoria = data.get('auditoria')
                    validade = data.get('validade')
                    tipo_validade = data.get('tipo_validade')
                    exibe_relatorio = sim_nao_to_boolean(data.get('exibe_relatorio'))
                    lista_situacao = data.get('lista_situacao')
                    prioridade = data.get('prioridade')
                    cargos_selecionados = data.get('cargos_selecionados')

                    tipo_documento = TipoDocumento.objects.create(
                        codigo=codigo,
                        nome=nome,
                        grupo_documento_id=grupo_id,
                        pcd=pcd,
                        valor_legal=valor_legal,
                        verifica_assinatura=verifica_assinatura,
                        auditoria=auditoria,
                        validade=validade,
                        tipo_validade=tipo_validade,
                        exibe_relatorio=exibe_relatorio,
                        lista_situacao=lista_situacao,
                        prioridade=prioridade
                    )

                    # Adicionar os cargos selecionados ao TipoDocumento
                    for cargo_id in cargos_selecionados:
                        cargo = Cargo.objects.get(id=int(cargo_id))
                        tipo_documento.cargo = cargo
                        tipo_documento.obrigatorio = True
                        tipo_documento.save()

                        # Construir URL completa para inserir_tipodocumento_cargo
                        url_cargo = request.build_absolute_uri(reverse('inserir_tipodocumento_cargo'))

                        # Enviar IDs para inserir_tipodocumento_cargo
                        response_cargo = requests.post(
                            url_cargo,
                            data={'cargo_id': cargo_id, 'tipodocumento_id': tipo_documento.id}
                        )


                    # Adicione os IDs dos cargos selecionados aos dados enviados na solicitação POST
                    url_colaborador = request.build_absolute_uri(reverse('inserir_tipodocumento_colaborador'))
                    for cargo_id in cargos_selecionados:
                        response_colaborador = requests.post(
                            url_colaborador,
                            data={'tipodocumento_id': tipo_documento.id, 'cargo_id': cargo_id}
                        )

                    return JsonResponse({'status': 'success', 'message': 'Tipo de documento criado com sucesso'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        # Se a solicitação for do tipo GET, retornar os tipos de documento existentes
        tipos_documento = TipoDocumento.objects.all().order_by('codigo')
        data = [{
            'id': tipo.id,
            'codigo': tipo.codigo,
            'grupo_documento': tipo.grupo_documento.nome if tipo.grupo_documento else '',
            'nome': tipo.nome,
            'obrigatorio': tipo.obrigatorio,
            'valor_legal': tipo.valor_legal,
            'validade': tipo.validade,
            'tipo_validade': tipo.tipo_validade,
            'verifica_assinatura': tipo.verifica_assinatura,
            'exibe_relatorio': tipo.exibe_relatorio,
            'lista_situacao': tipo.lista_situacao
        } for tipo in tipos_documento]
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def inserir_tipodocumento_cargo(request):
    if request.method == 'POST':
        cargo_id = request.POST.get('cargo_id')
        tipodocumento_id = request.POST.get('tipodocumento_id')

        try:
            cargo = Cargo.objects.get(pk=cargo_id)
            tipodocumento = TipoDocumento.objects.get(pk=tipodocumento_id)

            # Verifica se já existe uma relação com esses IDs
            if TipoDocumentoCargo.objects.filter(cargo=cargo, tipo_documento=tipodocumento).exists():
                return JsonResponse({'message': 'Essa relação já existe.'}, status=400)

            # Corrigindo o problema aqui:
            nova_relacao = TipoDocumentoCargo(cargo=cargo, tipo_documento=tipodocumento)
            nova_relacao.save()

            return JsonResponse({'message': 'Relação inserida com sucesso.'}, status=201)
        except Cargo.DoesNotExist:
            return JsonResponse({'message': 'Cargo não encontrado.'}, status=404)
        except TipoDocumento.DoesNotExist:
            return JsonResponse({'message': 'Tipo de documento não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Método não permitido.'}, status=405)

@csrf_exempt
def inserir_tipodocumento_colaborador(request):
    if request.method == 'POST':
        tipodocumento_id = request.POST.get('tipodocumento_id')
        cargo_id = request.POST.get('cargo_id')

        try:
            tipodocumento = TipoDocumento.objects.get(pk=tipodocumento_id)
            cargo = Cargo.objects.get(pk=cargo_id)

            # Buscar colaboradores com o mesmo cargo
            colaboradores = Colaborador.objects.filter(cargo=cargo)

            # Salvar relação entre tipo de documento e colaborador
            for colaborador in colaboradores:
                colaborador_tipodocumento = ColaboradorTipoDocumento.objects.create(
                    tipo_documento=tipodocumento,
                    colaborador=colaborador
                )
                colaborador_tipodocumento.save()

            return JsonResponse({'message': 'Relações inseridas com sucesso.'}, status=201)
        except TipoDocumento.DoesNotExist:
            return JsonResponse({'message': 'Tipo de documento não encontrado.'}, status=404)
        except Cargo.DoesNotExist:
            return JsonResponse({'message': 'Cargo não encontrado.'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return JsonResponse({'message': 'Método não permitido.'}, status=405)


@csrf_exempt
def cadastrar_grupo_documento(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        grupo_documento_id = data.get('id')
        if grupo_documento_id:
            # Verifica se a solicitação é para editar ou excluir um grupo de documento
            try:
                grupo_documento = get_object_or_404(GrupoDocumento, pk=grupo_documento_id)
                if 'excluir' in data and data['excluir']:
                    grupo_documento.delete()
                    return JsonResponse({'status': 'success', 'message': 'Grupo de documento excluído com sucesso'})
                else:
                    # Atualiza apenas os campos de interesse (nome e código)
                    grupo_documento.nome = data.get('nome', grupo_documento.nome)
                    grupo_documento.codigo = data.get('codigo', grupo_documento.codigo)
                    grupo_documento.save()
                    return JsonResponse({'status': 'success', 'message': 'Grupo de documento editado com sucesso'})
            except Exception as e:
                # print("Erro ao editar/excluir grupo de documento:", e)  # Adicionando log para o erro
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            # Adicionar um novo grupo de documento
            nome = data.get('nome')
            codigo = data.get('codigo')
            area_id = data.get('area_id')  # Obtendo o campo 'area_id'

            if not nome or not codigo or not area_id:
                return JsonResponse({'status': 'error', 'message': 'Nome, código e área são obrigatórios'}, status=400)
            try:
                novo_grupo_documento = GrupoDocumento.objects.create(nome=nome, codigo=codigo, area_id=area_id)
                return JsonResponse({'status': 'success', 'message': 'Grupo de documento criado com sucesso'})
            except Exception as e:
               #  print("Erro ao criar novo grupo de documento:", e)  # Adicionando log para o erro
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        # Consultando todos os grupos de documentos no banco de dados
        # Correto uso do order_by aqui para ordenar os resultados quando todos os objetos estão sendo listados
        grupo_documentos = GrupoDocumento.objects.all().order_by('codigo').values('id', 'nome', 'codigo', 'area_id')
        grupo_documentos_list = list(grupo_documentos)
        return JsonResponse({'grupo_documentos': grupo_documentos_list})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)


@csrf_exempt
def cadastrar_area(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

        except json.JSONDecodeError as e:

            return JsonResponse({'status': 'error', 'message': 'Dados inválidos'}, status=400)

        area_id = data.get('id')
        if area_id:
            try:
                area = get_object_or_404(Area, pk=area_id)
                if 'excluir' in data and data['excluir']:
                    area.delete()
                    return JsonResponse({'status': 'success', 'message': 'Área excluída com sucesso'})
                else:
                    area.codigo = data.get('codigo', area.codigo)
                    area.nome = data.get('nome', area.nome)
                    area.save()
                    return JsonResponse({'status': 'success', 'message': 'Área editada com sucesso'})
            except Exception as e:

                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            codigo = data.get('codigo')
            nome = data.get('nome')
            if not codigo or not nome:
                return JsonResponse({'status': 'error', 'message': 'Código e nome são obrigatórios'}, status=400)
            try:
                nova_area = Area.objects.create(codigo=codigo, nome=nome)
                return JsonResponse({'status': 'success', 'message': 'Área criada com sucesso'})
            except Exception as e:

                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    elif request.method == 'GET':
        areas = Area.objects.all().values('id', 'codigo', 'nome')
        areas_list = list(areas)
        return JsonResponse({'areas': areas_list})
    else:

        return JsonResponse({'status': 'error', 'message': 'Método não permitido'}, status=405)



class ImportarDadosView(View):
    template_name = 'documento/import_xlsx.html'

    def get(self, request):
        form = ImportarDadosForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ImportarDadosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo_csv = form.cleaned_data.get('arquivo_csv')
            sucesso, mensagem = importar_dados(arquivo_csv)
            if sucesso:
                messages.success(request, "Dados importados com sucesso.")
            else:
                messages.error(request, mensagem)
            # return redirect('alguma_url_de_sucesso')
        else:
            messages.error(request, "Erro no formulário.")
        return render(request, self.template_name, {'form': form})

def importar_usuarios(request):
    if request.method == 'POST':
        form = ImportarUsuariosForm(request.POST, request.FILES)
        if form.is_valid():
            arquivo_excel = request.FILES['arquivo_excel']
            try:
                df = pd.read_excel(arquivo_excel, engine='openpyxl')

                for index, row in df.iterrows():
                    senha_aleatoria = secrets.token_urlsafe(12)  # Gera senha aleatória
                    # Crie um objeto ImportUsuarioXLSX com os dados do DataFrame
                    ImportUsuarioXLSX.objects.create(
                        nome=row['usuario'],
                        login=row['Login'],
                        regional=row['Regional'],
                        unidade=row['Unidade'],
                        ativo=row['Ativo'],
                        senha=senha_aleatoria,
                    )

                messages.success(request, 'Usuários importados com sucesso.')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao importar os usuários: {str(e)}')
            return redirect('importar_usuarios')
    else:
        form = ImportarUsuariosForm()

    return render(request, 'documento/import_usuario.html', {'form': form})


def criar_funcionario(request):
    form = PesquisaFuncionarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('documento/configuracao.html')


def lista_funcionarios(request):
    funcionarios = Colaborador.objects.all()
    return render(request, 'documento/configuracao.html', {'funcionarios': funcionarios})


# ******* 'Login', autenticação com Banco de dados, Logut e criação de 'login' ***********
# @login_required
@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request: object) -> object:
        # Obter os dados de login do corpo da requisição POST
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Autenticar o usuário
        user = authenticate(request, username=username, password=password)


        if user is not None:
            # Se as credenciais forem válidas, faça o login
            login(request, user)
            return redirect('dashboard')
            # return JsonResponse({'message': 'Login bem-sucedido'})
        else:
            # Se as credenciais forem inválidas, retorne uma resposta de erro
            return JsonResponse({'error': 'Credenciais inválidas'}, status=400)

class AuthenticationViews(View):
    def forgot_password(request):
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                form.save(
                    request=request,
                    from_email='from@example.com',
                    email_template_name='documento/tela_login.html',
                    subject_template_name='documento/password_reset_subject.txt',
                    html_email_template_name='documento/password_reset_email.html',
                )
                return redirect('password_reset_done')
        else:
            form = PasswordResetForm()
        return render(request, 'documento/tela_login.html', {'form': form})

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'documento/tela_login.html'


class CustomLogoutView(LogoutView):
    template_name = 'documento/tela_login.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        request.session['user_logged_out'] = True
        return response


class CheckUserLoggedOutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.session.get('user_logged_out'):
            # Se o usuário tentar acessar uma página protegida após ter saído, redirecione para o login
            del request.session['user_logged_out']  # Remova o sinalizador
            return redirect(reverse('login'))

        response = self.get_response(request)
        return response


def cadastro_login(request):
    if request.method == 'POST':
        # Coletar dados do formulário
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_superuser = request.POST.get('is_superuser') == 'on'

        # Verificar se o usuário já existe
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, 'Este nome de usuário já está em uso.')
            return redirect('cadastro_login')

        if is_superuser and not request.user.is_superuser:
            messages.error(request, 'Você não tem permissão para criar um superusuário.')
            return redirect('cadastro_login')

        if is_superuser:
            user = Usuario.objects.create_superuser(username=username, email=email, password=password)
        else:
            user = Usuario.objects.create_user(username=username, email=email, password=password)

        # Verificar se o usuário foi criado com sucesso
        if user:
            messages.success(request, 'Usuário criado com sucesso!')
            # Se desejar, pode fazer login automaticamente após o cadastro
            # login(request, user)
            return redirect('login')  # Redirecionar para a página de login
        else:
            messages.error(request, 'Houve um problema ao criar o usuário. Por favor, tente novamente.')

    # Se o método for GET ou se houver algum erro, renderizar o formulário de cadastro
    return render(request, 'documento/configuracao.html', {})

