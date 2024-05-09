from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import PasswordResetDoneView
from .views import (LoginView, visualizar_documentos, TotalColaboradoresView, get_documentos_info,
                    AtualizarDocumentosPendentesView, DocumentosExistentesAtivosView,
                    ObrigatoriosPorUnidadeAtivo, ObrigatoriosPorUnidadeInativo, AtualizarASOView,
                    ASOPercentualAtivoView, AtualizarCartaoPontoView, DocumentosPontoAtivoView,
                    DocumentosPontoInativoView, domingos_feriados_existente,
                    CarregarRelatorioPendenteView, CarregarRelatorioExistenteView, CarregarRelatorioPendenteASOView,
                    ListarCartaoPontoInexistenteView, CarregarDocumentosVencidosView, ObrigatoriosUnidadesInativoView,
                    ASOPercentualInativoView, DocumentosObrigatoriosAtivosView, DocumentosObrigatoriosInativosView,
                    ObrigatoriosUnidadesAtivoView, ListarDocumentosVencidosView, ListarDocumentosaVencerView,
                    get_hyperlinkpdf_data, DocumentosPendentesAtivosPorUnidadeView,
                    DocumentosPendentesInativosPorUnidadeView, DocumentoExistenteListView, buscar_pendencias)
from .views import (
    dashboard, index, importar_usuarios, gerenciar_colaborador, gerenciar_empresa, gerenciar_regional, gerenciar_unidade, gerenciar_usuario,
    CarregarDadosView, PesquisaDossieView, ListarResultadoDossieView, CarregarEmpresaView, CarregarCargoView,
    CarregarRegionalView, CarregarUnidadesView, CarregarSituacoesView, CarregarColaboradorView, dados_pessoais,
    cadastrar_area, cadastrar_grupo_documento, dossie, inserir_tipodocumento_cargo,
    relatorios, configuracao, tela_login, inserir_tipodocumento_colaborador, RelatorioPendenteView,
    DocumentosExistentesView, DocumentoVencidoListView, DocumentoAVencerListView,
    PendenteASOListView, RelatorioGerencialListView, criar_funcionario,
    lista_funcionarios, cadastrar_tipodocumento, AuthenticationViews, ImportarDadosView, CustomLogoutView)



urlpatterns = [
    # Urls tela inicial e Login
    path('index/', index, name='index'),
    path('login_login/', LoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    # path('logar/', CustomLogoutView.as_view(), name='logar'),
    path('forgot_password/', AuthenticationViews.as_view, name='forgot_password'),
    path('password_reset_done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('documento/importar_dados/', ImportarDadosView.as_view(), name='importar-dados'),


    # Urls tela DOSSIE
    path('dossie/<int:pk>/', PesquisaDossieView.as_view(), name='detalhe_dossie'),
    path('carregar_empresa/', CarregarEmpresaView.as_view(), name='carregar_empresa'),
    path('carregar_regionais/', CarregarRegionalView.as_view(), name='carregar_regionais'),
    path('carregar_unidades/', CarregarUnidadesView.as_view(), name='carregar_unidades'),
    path('carregar_colaborador/', CarregarColaboradorView.as_view(), name='carregar_colaborador'),
    path('carregar_cargos/', CarregarCargoView.as_view(), name='carregar_cargos'),
    path('carregar_situacoes/', CarregarSituacoesView.as_view(), name='carregar_situacoes'),
    path('dossie/<int:pk>/resultados/', ListarResultadoDossieView.as_view(), name='listar_resultado_dossie'),
    path('dados-pessoais/', dados_pessoais, name='dados_pessoais'),
    path('api/carregar_dados/', CarregarDadosView.as_view(), name='carregar_dados'),
    path('visualizar_documentos/', visualizar_documentos, name='visualizar_documentos'),
    path('atualizar-documentos-pendentes/', AtualizarDocumentosPendentesView.as_view(), name='atualizar_documentos_pendentes'),
    path('hyperlinkpdf/', get_hyperlinkpdf_data, name='hyperlinkpdf'),
    path('get_documentos_info/', get_documentos_info, name='get_documentos_info'),



    # URLS tela DASHBOARD
    path('aso_percentual_ativo/', ASOPercentualAtivoView.as_view(), name='aso_percentual_ativo'),
    path('aso/percentual-inativo/', ASOPercentualInativoView.as_view(), name='aso_percentual_inativo'),
    path('documentos/obrigatorios-ativos/', DocumentosObrigatoriosAtivosView.as_view(),
         name='documentos_obrigatorios_ativos'),
    path('documentos/obrigatorios-inativos/', DocumentosObrigatoriosInativosView.as_view(),
         name='documentos_obrigatorios_inativos'),
    path('documentos/ponto-ativos/', DocumentosPontoAtivoView.as_view(), name='documentos_ponto_ativos'),
    path('documentos/ponto-inativos/', DocumentosPontoInativoView.as_view(), name='documentos_ponto_inativos'),

    path('obr_unidade_ativo_inativos/', ObrigatoriosUnidadesAtivoView.as_view(), name='obr_unidade_ativo_inativos'),
    path('obr_unidade_ativo_inativos/', ObrigatoriosUnidadesInativoView.as_view(), name='obr_unidade_ativo_inativos'),

    path('get_documentos_info/', get_documentos_info, name='get_documentos_info'),

    path('carregar-relatorio-pendente/<str:situacao>/', CarregarRelatorioPendenteView.as_view(), name='carregar_relatorio_pendente'),
    path('relatorio-pendente/', CarregarRelatorioPendenteView.as_view(), name='carregar_relatorio_pendente_sem_situacao'),

    path('relatorio_existente_todo/<str:status>/', CarregarRelatorioExistenteView.as_view(), name='relatorio_existente_todos'),
    path('relatorio_existente_todo/', CarregarRelatorioExistenteView.as_view(), name='relatorio_existente_todos_sem_situacao'),

    path('relatorio/asos/', CarregarRelatorioPendenteASOView.as_view(), name='carregar_relatorio_pendente_asos'),
    path('listar-cartoes/', ListarCartaoPontoInexistenteView.as_view(), name='listar_cartoes_ponto_inexistentes'),


    path('documentos_vencidos/', CarregarDocumentosVencidosView.as_view(), name='documentos_vencidos'),
    path('lista_documentos_vencidos/', ListarDocumentosVencidosView.as_view(), name='lista_vencidos'),
    path('lista_a_vence/', ListarDocumentosaVencerView.as_view(), name='lista_a_vencer'),
    # path('documentos_auditoria/', CarregarDocumentosAuditoriaView.as_view(), name='documentos_auditorias'),
    path('documentos_existentes/', DocumentosExistentesView.as_view(), name='documentos_existentes'),
    path('atualizar-documentos-pendentes/', AtualizarDocumentosPendentesView.as_view(), name='atualizar_documentos_pendentes'),
    path('pendente_aso/', AtualizarASOView.as_view(), name='atualizar-aso'),
    path('atualizar_controle_ponto/', AtualizarCartaoPontoView.as_view(), name="atualizar_controle_ponto"),



    # Urls tela Relatorios
    path('doc_pendentes_unidade_ativo/', DocumentosPendentesAtivosPorUnidadeView.as_view(),
         name='doc_pendentes_unidade_ativo'),
    path('obrigatorios-por-unidade/', ObrigatoriosPorUnidadeAtivo.as_view(), name='obrigatorios_por_unidade'),
    path('doc_pendentes_unidade_inativo/', DocumentosPendentesInativosPorUnidadeView.as_view(),
         name='doc_pendentes_unidade_inativo'),
    path('doc_existentes_unidades/<str:unidade_nome>/<str:status>/', DocumentosExistentesAtivosView.as_view(),
         name='doc_existentes_unidades_ativos'),
    path('relatorio_pendente/', RelatorioPendenteView.as_view(), name='relatorio_pendente'),
    path('documentos_existentes/', DocumentoExistenteListView.as_view(), name='documentos_existentes'),
    path("documentos_vencidos/", DocumentoVencidoListView.as_view(), name="documentos_vencidos"),
    path("documentos_a_vencer/", DocumentoAVencerListView.as_view(), name="documentos_a_vencer"),
    # path("controle_ponto/", ControlePontoListView.as_view(), name="controle_ponto"),
    path("pendentes_aso/", PendenteASOListView.as_view(), name="pendentes_aso"),
    # path("documentos_existentes_auditoria/", DocumentoExistenteAuditoriaListView.as_view(), name="documentos_existentes_auditoria"),
    path("relatorios_gerenciais/", RelatorioGerencialListView.as_view(), name="relatorios_gerenciais"),
    path('total_colaboradores/', TotalColaboradoresView.as_view(), name='total_colaboradores'),
    path('obrigatorios-inativos-unidade/', ObrigatoriosPorUnidadeInativo.as_view(), name='obrigatorios_inativos_unid'),

    path('pesquisa-documentos/', domingos_feriados_existente, name='domingos_feriados'),

    path('pendencias/', buscar_pendencias, name='buscar_pendencias'),


    # Urls Tela Configurações
    path('importar_dados/', ImportarDadosView.as_view(), name='importar_dados'),
    path('importar-usuarios/', importar_usuarios, name='importar_usuarios'),
    path('criar-funcionario/', criar_funcionario, name='criar_funcionario'),
    path('lista-funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('listar_resultados_dossie/', ListarResultadoDossieView.as_view(), name='listar_resultados_dossie'),
    path('cadastrar_area/', cadastrar_area, name='cadastrar_area'),
    path('cadastrar_grupo_documento/', cadastrar_grupo_documento, name='cadastrar_grupo_documento'),
    path('cadastrar_tipodocumento/', cadastrar_tipodocumento, name='cadastrar_tipodocumento'),
    path('inserir_tipodocumento_cargo/', inserir_tipodocumento_cargo, name='inserir_tipodocumento_cargo'),
    path('inserir_tipodocumento_colaborador/', inserir_tipodocumento_colaborador, name='inserir_tipodocumento_colaborador'),
    path('cadastro_colaborador/', gerenciar_colaborador, name='cadastrar_colaboradores'),
    path('cadastro_empresa/', gerenciar_empresa, name='cadastrar_empresas'),
    path('cadastro_regional/', gerenciar_regional, name='cadastrar_regionais'),
    path('cadastro_uniade/', gerenciar_unidade, name='cadsatrar_unidades'),
    path('cadastro_usuario/', gerenciar_usuario, name='cadastro_usuarios'),

    path('dossie/', dossie, name='dossie'),
    path('relatorios/', relatorios, name='relatorios'),
    path('configuracao/', configuracao, name='configuracao'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', tela_login, name='tela_login'),

]

# No final do seu arquivo urls.py
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

