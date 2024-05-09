# queries.py
import re
import csv
import codecs
from datetime import datetime, timezone
from django.db import transaction
from logger import logger
from setuptools import logging

from documento.models import Empresa, Regional, Unidade, Cargo, Situacao, CartaoPontoInexistente, DocumentoVencido
from documento.utils import validar_dados_csv, validar_cabecalho_csv
from .models import Colaborador, Hyperlinkpdf, DocumentoPendente, TipoDocumento, PendenteASO
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta  # Importe timedelta diretamente
import logging


def importar_dados(arquivo_csv):
    try:
        leitor_csv = csv.DictReader(codecs.iterdecode(arquivo_csv, 'utf-8-sig'), delimiter=';')
        if not leitor_csv.fieldnames or not validar_cabecalho_csv(leitor_csv.fieldnames):
            return False, "Problema no cabeçalho do CSV"

        cache_empresas = {}
        cache_regionais = {}
        cache_unidades = {}
        cache_cargos = {}
        cache_situacoes = {}

        bloco = []  # Lista para armazenar linhas a serem processadas
        for i, linha in enumerate(leitor_csv, start=1):
            if not validar_dados_csv(linha, leitor_csv.fieldnames):
                print(f"Linha {i} inválida e será ignorada.")
                continue

            bloco.append(linha)
            if len(bloco) == 1000:  # Processa em blocos de 1000
                processar_bloco(bloco, cache_empresas, cache_regionais, cache_unidades, cache_cargos, cache_situacoes,
                                i)
                bloco = []  # Reseta o bloco após o processamento

        if bloco:  # Processa qualquer linha restante
            processar_bloco(bloco, cache_empresas, cache_regionais, cache_unidades, cache_cargos, cache_situacoes, i)

        return True, "Dados importados com sucesso."
    except Exception as e:
        return False, f"Erro ao importar dados: {str(e)}"


logger = logging.getLogger(__name__)


def processar_bloco(bloco, cache_empresas, cache_regionais, cache_unidades, cache_cargos, cache_situacoes, start_index):
    with transaction.atomic():  # Inicia uma transação
        for index, linha in enumerate(bloco, start=start_index):
            sid = transaction.savepoint()  # Cria um ponto de salvamento
            try:
                logger.debug(f"Processando linha {index}: {linha}")
                empresa, _ = Empresa.objects.get_or_create(nome=linha['EMPRESA'])
                regional, _ = Regional.objects.get_or_create(nome=linha['REGIONAL'], empresa=empresa)
                unidade, _ = Unidade.objects.get_or_create(nome=linha['UNIDADE'], regional=regional)
                cargo, _ = Cargo.objects.get_or_create(nome=linha['CARGO'], unidade=unidade)
                situacao, _ = Situacao.objects.get_or_create(nome=linha['STATUS'], cargo=cargo)

                colaborador, created = Colaborador.objects.get_or_create(
                    unidade=unidade,
                    matricula=linha['MATRICULA'],
                    defaults={
                        'nome': linha['NOME'],
                        'cpf': linha['CPF'],
                        'cargo': cargo,
                        'status': situacao,
                        'admissao': converter_data(linha['ADMISSAO'], index),
                        'desligamento': converter_data(linha['DESLIGAMENTO'], index),
                        'email': linha['EMAIL'],
                        'pcd': linha.get('PCD', False)
                    }
                )

                if not created:
                    colaborador.save()

                logger.info(f"Processado: {index} - {colaborador.matricula}")
            except Exception as e:
                logger.error(f"Erro ao processar a linha {index}: {e}")
                transaction.savepoint_rollback(sid)  # Reverte para o ponto de salvamento
            else:
                transaction.savepoint_commit(sid)  # Commit do ponto de salvamento se tudo correu bem


def converter_data(data_str, linha):
    if data_str.strip():
        data_limpa = re.sub(r"[^0-9/]", "", data_str.strip())
        try:
            return datetime.strptime(data_str, '%d/%m/%Y').date()
        except ValueError:
            logger.error(f"Data inválida na linha {linha}: {data_str}")
            return None


class ObterDocumentosPendentes:
    @staticmethod
    def calcular_documentos_pendentes():

        # colaboradores_ativos = Colaborador.objects.filter(desligamento__isnull=True)  esse pega ativos e afastados
        colaboradores_ativos = Colaborador.objects.filter(desligamento__isnull=True)

        tipos_de_documentos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True)
        documentos_a_atualizar = []

        for colaborador in colaboradores_ativos:
            for tipo_documento in tipos_de_documentos_obrigatorios:
                documento_pendente, created = DocumentoPendente.objects.get_or_create(
                    nome=colaborador,
                    tipo_documento=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'situacao': colaborador.status.nome,
                        'obrigatorio': tipo_documento.obrigatorio
                    }
                )
                if not created:
                    documentos_a_atualizar.append(documento_pendente)

    @staticmethod
    def atualizar_tabela_documentos_pendentes():
        ObterDocumentosPendentes.calcular_documentos_pendentes()


class ServicoPendenteASO:
    @staticmethod
    def inicializar_pendencias():

        colaboradores = Colaborador.objects.all()
        # Filtra apenas os tipos de documentos que correspondem aos IDs dos ASOs
        tipos_de_documentos_aso = TipoDocumento.objects.filter(codigo__in=[401, 402, 403])

        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_aso:
                documentos = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id)

                documento_existe = documentos.exists()

                pendencia, created = PendenteASO.objects.update_or_create(
                    nome=colaborador,
                    tipo_aso=tipo_documento,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'matricula': colaborador.matricula,
                        'cpf': colaborador.cpf,
                        'cargo': colaborador.cargo,
                        'admissao': colaborador.admissao,
                        'desligamento': colaborador.desligamento,
                        'status': colaborador.status,
                        'aso_admissional_existente': True if tipo_documento.nome == "ASO Admissional" and documento_existe else False,
                        'aso_demissional_existente': True if tipo_documento.nome == "ASO Demissional" and documento_existe else False,
                        'aso_periodico_existente': True if tipo_documento.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False,
                    }
                )

    @staticmethod
    def atualizar_pendencias():
        pendencias = PendenteASO.objects.all()
        for pendencia in pendencias:
            documentos = Hyperlinkpdf.objects.filter(nome=pendencia.nome, tipo_documento=pendencia.tipo_aso)
            documento_existe = documentos.exists()

            # Atualiza campos booleanos de acordo com a existência dos documentos
            pendencia.aso_admissional_existente = True if pendencia.tipo_aso.nome == "ASO Admissional" and documento_existe else False
            pendencia.aso_demissional_existente = True if pendencia.tipo_aso.nome == "ASO Demissional" and documento_existe else False
            pendencia.aso_periodico_existente = True if pendencia.tipo_aso.nome == "ASO Periódico/ Retorno ao Trabalho" and documento_existe else False

            pendencia.save()


class CarregarASOAtivo:
    @staticmethod
    def calcular_porcentagens_aso_admissional():
        total_asos = PendenteASO.objects.filter(tipo_aso__codigo=401).count()
        if total_asos == 0:
            return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

        asos_existentes = PendenteASO.objects.filter(tipo_aso__codigo=401, aso_admissional_existente=True).count()
        percentual_existente = (asos_existentes / total_asos) * 100
        percentual_pendente = 100 - percentual_existente

        return {
            "Existente": f"{percentual_existente:.0f}%",
            "Pendente": f"{percentual_pendente:.0f}%"
        }


class CarregarASOInativo:
    @staticmethod
    def calcular_porcentagens_aso_demissional():
        total_asos = PendenteASO.objects.filter(tipo_aso__codigo=402).count()
        if total_asos == 0:
            return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

        asos_existentes = PendenteASO.objects.filter(tipo_aso__codigo=402, aso_demissional_existente=True).count()
        percentual_existente = (asos_existentes / total_asos) * 100
        percentual_pendente = 100 - percentual_existente

        return {
            "Existente": f"{percentual_existente:.0f}%",
            "Pendente": f"{percentual_pendente:.0f}%"
        }


def calcular_porcentagens_documentos_obrigatorios_ativos():
    # Total de tipos de documentos obrigatórios
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

    # Total de documentos obrigatórios que existem para colaboradores ativos
    documentos_existentes = Hyperlinkpdf.objects.filter(
        documento__obrigatorio=True,
        colaborador__status__nome='ativo'  # Usa o campo correto de Situacao
    ).distinct('documento').count()  # Considera cada tipo de documento uma única vez por colaborador ativo

    if total_tipos_obrigatorios == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    # Cálculo de porcentagem
    percentual_existente = (documentos_existentes / total_tipos_obrigatorios) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }


def calcular_porcentagens_documentos_obrigatorios_inativos():
    # Total de tipos de documentos obrigatórios
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

    # Total de documentos obrigatórios que existem para colaboradores ativos
    documentos_existentes = Hyperlinkpdf.objects.filter(
        documento__obrigatorio=True,
        colaborador__status__nome='inativo'  # Usa o campo correto de Situacao
    ).distinct('documento').count()  # Considera cada tipo de documento uma única vez por colaborador ativo

    if total_tipos_obrigatorios == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    # Cálculo de porcentagem
    percentual_existente = (documentos_existentes / total_tipos_obrigatorios) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }


class ServicoPonto:
    @staticmethod
    def inicializar_pendencias():

        colaboradores = Colaborador.objects.all()
        tipos_de_documentos_ponto = TipoDocumento.objects.filter(codigo__in=[601])

        for colaborador in colaboradores:
            for tipo_documento in tipos_de_documentos_ponto:
                documentos = Hyperlinkpdf.objects.filter(colaborador_id=colaborador.id, documento_id=tipo_documento.id)
                documento_existe = documentos.exists()

                pendencia, created = CartaoPontoInexistente.objects.update_or_create(
                    colaborador=colaborador,
                    defaults={
                        'empresa': colaborador.empresa,
                        'regional': colaborador.regional,
                        'unidade': colaborador.unidade,
                        'status': colaborador.status,  # Assumindo que 'status' reflete o status do colaborador
                        'existente': documento_existe,  # Variável booleana indicando se o documento existe
                    }
                )

    @staticmethod
    def atualizar_pendencias():
        pendencias = CartaoPontoInexistente.objects.all()
        for pendencia in pendencias:
            documentos = Hyperlinkpdf.objects.filter(nome=pendencia.nome, tipo_documento=pendencia.ponto)
            documento_existe = documentos.exists()

            # Atualiza campos booleanos de acordo com a existência dos documentos
            pendencia.ponto_existente = True if pendencia.ponto.nome == "Folha de Ponto" and documento_existe else False

            pendencia.save()


def calcular_porcentagens_ponto_ativos():
    # Total de documentos de ponto (considerando código 601 como 'Folha de Ponto')
    total_ponto = TipoDocumento.objects.filter(codigo=601, obrigatorio=True).count()

    # Total de documentos de ponto que existem para colaboradores ativos
    documentos_existentes = Hyperlinkpdf.objects.filter(
        documento__codigo=601,  # Filtra documentos onde o código é 601
        colaborador__status__nome='ativo'  # E o status do colaborador é 'ativo'
    ).distinct('documento').count()  # Considera cada documento uma única vez por colaborador ativo

    if total_ponto == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    # Cálculo de porcentagem
    percentual_existente = (documentos_existentes / total_ponto) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }


def calcular_porcentagens_ponto_inativos():
    # Total de documentos de ponto (considerando código 601 como 'Folha de Ponto')
    total_ponto = TipoDocumento.objects.filter(codigo=601, obrigatorio=True).count()

    # Total de documentos de ponto que existem para colaboradores inativos
    documentos_existentes = Hyperlinkpdf.objects.filter(
        documento__codigo=601,  # Filtra documentos onde o código é 601
        colaborador__status__nome='inativo'  # E o status do colaborador é 'inativo'
    ).distinct('documento').count()  # Considera cada documento uma única vez por colaborador inativo

    if total_ponto == 0:
        return {"Existente": "0%", "Pendente": "0%"}  # Evita divisão por zero

    # Cálculo de porcentagem
    percentual_existente = (documentos_existentes / total_ponto) * 100
    percentual_pendente = 100 - percentual_existente

    return {
        "Existente": f"{percentual_existente:.0f}%",
        "Pendente": f"{percentual_pendente:.0f}%"
    }


def calcular_porcentagens_obrigatorios_unidade_ativos():
    # Contagem total de tipos de documentos obrigatórios
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

    if total_tipos_obrigatorios == 0:
        return []  # Evita divisão por zero

    # Agregação no banco de dados para contar documentos por unidade
    documentos_por_unidade = Hyperlinkpdf.objects.filter(
        documento__obrigatorio=True,
        colaborador__status__nome='ativo'
    ).values('colaborador__unidade__nome').annotate(
        existentes=Count('documento', distinct=True)
    ).order_by('colaborador__unidade__nome')

    porcentagens_por_unidade = []
    for item in documentos_por_unidade:
        unidade_nome = item['colaborador__unidade__nome']
        documentos_existentes = item['existentes']
        percentual_existente = (documentos_existentes / total_tipos_obrigatorios) * 100
        percentual_pendente = 100 - percentual_existente

        porcentagens_por_unidade.append({
            'unidade_nome': unidade_nome,
            'percentual_existente': f"{percentual_existente:.0f}%",
            'percentual_pendente': f"{percentual_pendente:.0f}%"
        })

    return porcentagens_por_unidade


def calcular_porcentagens_obrigatorios_unidade_inativos():
    # Contagem total de tipos de documentos obrigatórios
    total_tipos_obrigatorios = TipoDocumento.objects.filter(obrigatorio=True).count()

    if total_tipos_obrigatorios == 0:
        return []  # Evita divisão por zero

    # Agregação no banco de dados para contar documentos por unidade para colaboradores inativos
    documentos_por_unidade = Hyperlinkpdf.objects.filter(
        documento__obrigatorio=True,
        colaborador__status__nome='inativo'
    ).values('colaborador__unidade__nome').annotate(
        existentes=Count('documento', distinct=True)
    ).order_by('colaborador__unidade__nome')

    porcentagens_por_unidade = []
    for item in documentos_por_unidade:
        unidade_nome = item['colaborador__unidade__nome']
        documentos_existentes = item['existentes']
        percentual_existente = (documentos_existentes / total_tipos_obrigatorios) * 100
        percentual_pendente = 100 - percentual_existente

        porcentagens_por_unidade.append({
            'unidade_nome': unidade_nome,
            'percentual_existente': f"{percentual_existente:.0f}%",
            'percentual_pendente': f"{percentual_pendente:.0f}%"
        })
    return porcentagens_por_unidade


class DocumentoVencidoService:
    @staticmethod
    def copiar_documentos_relevantes():
        documentos_processados = 0

        codigos_relevantes = [401, 403, 501, 502]
        tipos_documentos_relevantes = TipoDocumento.objects.filter(codigo__in=codigos_relevantes)

        for documento in Hyperlinkpdf.objects.filter(documento__in=tipos_documentos_relevantes):
            _, created = DocumentoVencidoService.criar_a_partir_de_hyperlinkpdf(documento)
            if created:
                documentos_processados += 1

        return {'documentos_processados': documentos_processados}

    @staticmethod
    def criar_a_partir_de_hyperlinkpdf(hyperlinkpdf):
        tipo_doc_id = str(hyperlinkpdf.codigo_documento)
        precisa_renovar = tipo_doc_id in ['403', '501', '502']
        novo_documento, created = DocumentoVencido.objects.update_or_create(
            matricula=hyperlinkpdf.matricula,
            tipo_documento=hyperlinkpdf.documento,
            defaults={
                'empresa': hyperlinkpdf.empresa,
                'regional': hyperlinkpdf.regional,
                'unidade': hyperlinkpdf.unidade,
                'colaborador': hyperlinkpdf.colaborador,
                'cpf': hyperlinkpdf.cpf,
                'cargo': hyperlinkpdf.cargo,
                'dta_documento': hyperlinkpdf.dta_documento,
                'precisa_renovar': precisa_renovar
            }
        )
        return novo_documento, created


class ServicoValidadeDocumento:
    @staticmethod
    def documentos_vencidos():
        hoje = timezone.now().date()
        documentos_vencidos = []

        # Usando select_related para pegar as informações do cargo junto com cada colaborador
        documentos = DocumentoVencido.objects.select_related(
            'empresa',
            'regional',
            'unidade',
            'colaborador',
            'colaborador__cargo',  # Esta linha assume que o modelo 'Colaborador' tem uma ForeignKey para 'Cargo'
            'tipo_documento'
        ).all()

        for documento in documentos:
            try:
                validade = int(documento.tipo_documento.validade)
                data_competencia = documento.dta_documento + timedelta(days=validade * 30)
                if data_competencia < hoje:
                    doc_info = {
                        'id': documento.id,
                        'matricula': documento.matricula,
                        'nome': documento.colaborador.nome,
                        'cpf': documento.cpf,
                        'cargo': documento.colaborador.cargo.nome,  # Acessando um atributo específico do objeto Cargo
                        'unidade': documento.colaborador.unidade.nome,
                        'regional': documento.colaborador.unidade.regional.nome,
                        'empresa': documento.colaborador.unidade.regional.empresa.nome,
                        'dta_documento': data_competencia.strftime('%Y-%m-%d')  # Formatar a data para string
                    }
                    documentos_vencidos.append(doc_info)
            except ValueError:
                continue

        return documentos_vencidos


def documentos_a_vencer(documentos):
    hoje = timezone.now().date()
    vencimentos = {'15_dias': [], '30_dias': [], '45_dias': [], '60_dias': [], '70_dias': [], '90_dias': []}

    for documento in documentos:
        try:
            validade = int(documento.tipo_documento.validade)  # Assume validade é em meses
            data_vencimento = documento.dta_documento + timedelta(days=validade * 30)
            dias_para_vencer = (data_vencimento - hoje).days

            if dias_para_vencer <= 15:
                vencimentos['15_dias'].append(documento)
            elif dias_para_vencer <= 30:
                vencimentos['30_dias'].append(documento)
            elif dias_para_vencer <= 45:
                vencimentos['45_dias'].append(documento)
            elif dias_para_vencer <= 60:
                vencimentos['60_dias'].append(documento)
            elif dias_para_vencer <= 70:
                vencimentos['70_dias'].append(documento)
            elif dias_para_vencer <= 90:
                vencimentos['90_dias'].append(documento)

        except Exception as e:
            print(f"Error processing document {documento.id}: {str(e)}")

    # Convertendo objetos DocumentoVencido para dicionários após o loop
    for intervalo in vencimentos:
        vencimentos[intervalo] = [
            {
                'id': doc.id,
                'nome': doc.colaborador.nome,
                'cpf': doc.cpf,
                'cargo': doc.colaborador.cargo.nome if doc.colaborador.cargo else '',
                'unidade': doc.unidade.nome if doc.unidade else '',
                'regional': doc.regional.nome if doc.regional else '',
                'empresa': doc.empresa.nome if doc.empresa else '',
                'admissao': doc.colaborador.admissao.strftime('%Y-%m-%d') if doc.colaborador.admissao else '',
                'desligamento': doc.colaborador.desligamento.strftime('%Y-%m-%d') if doc.colaborador.desligamento else '',
                'data_vencimento': doc.dta_documento.strftime('%Y-%m-%d'),
                'dias_para_vencer': dias_para_vencer
            }
            for doc in vencimentos[intervalo]
        ]

    return vencimentos


class DocumentoPendenciaQuery:
    @staticmethod
    def buscar_pendencias_por_data(data_escolhida):
        # Converter a data escolhida para o formato de data do Python
        data_formatada = datetime.strptime(data_escolhida, '%d/%m/%Y').date()

        # Buscar pendências no modelo DocumentoPendente pela data de upload
        pendencias = DocumentoPendente.objects.filter(data_upload__date=data_formatada)

        # Buscar hyperlinks que foram carregados na data escolhida
        uploads = Hyperlinkpdf.objects.filter(data_upload__date=data_formatada)

        # Combinar os resultados em um dicionário para retorno
        resultado = {
            'pendencias': list(pendencias.values()),
            'uploads': list(uploads.values())
        }

        return resultado
