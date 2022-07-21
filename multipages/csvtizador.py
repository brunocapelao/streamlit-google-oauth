import streamlit as st
import pandas as pd
import base64
from datetime import datetime, date, time, timedelta
from decimal import Decimal


def decimal_from_value(value):
    return Decimal(value)


siglas = ['reit', 'cmmd', 'cbb', 'bond', 'ag', 'bbda']

# @st.cache


def app():

    def get_table_download_link_csv(df, name):
        #csv = df.to_csv(index=False)
        csv = df.to_csv(index=False).encode()
        #b64 = base64.b64encode(csv.encode()).decode()
        b64 = base64.b64encode(csv).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{name}" target="_blank">Download {name}</a>'
        return href

    st.title('CSVtizador - V1')
    st.subheader('Gambiarra que FUNCIONA!')

    process_selectbox = st.sidebar.selectbox(
        "Qual processo?",
        ("Resgates", "Rebalanceamento", "Aplicacoes", "Conferir BBAPI x Cotizador")
    )

    if process_selectbox == 'Resgates':
        st.header('Resgates')
        st.markdown('''
        **Baixar os arquivos CSV e fazer o upload nos campos:**

        **Saques.csv** -> https://metabase.backoffice.byebnk.com/question/161-bbapi-saques-confirmados

        **Saldos.csv** -> https://metabase.backoffice.byebnk.com/question/157-cotizador-saldo-cotista-por-fundo

        ''')
        inicio = st.date_input("Data Inicial", datetime.now())
        inicio = datetime.combine(inicio, time.min)
        inicio = inicio.replace(hour=16) - timedelta(days=1)
        final = st.date_input("Data Final", datetime.now())
        final = datetime.combine(final, time.min)
        final = final.replace(hour=16)

        descotizar = st.date_input("Data de descotizacao", datetime.now())
        saques_file = st.file_uploader("Saques.csv")
        saldos_file = st.file_uploader("Saldos.csv")

        if saldos_file and saques_file is not None:
            siglas = ['reit', 'cmmd', 'cbb', 'bond', 'ag', 'bbda']
            saldos = pd.read_csv(saldos_file, dtype={'documento': str})
            saques = pd.read_csv(saques_file, dtype={'documento': str})

            for s in siglas:
                saldos[s + '_p'] = saldos[s] / (saldos[siglas].sum(axis=1))

            saques = saques[(saques.solicitado_em >= inicio.isoformat(timespec='microseconds')) &
                            (saques.solicitado_em <= final.isoformat(timespec='microseconds'))]

            saques = saques.merge(saldos, how='left', on='documento')
            saques.drop('nome_y', inplace=True, axis=1)
            saques.rename(columns={'nome_x': 'nome'}, inplace=True)
            saques = saques[saques[siglas].sum(axis=1) > 0]

            for i in saques[saques['valor_usd'] > 0].index:
                for s in siglas:
                    saques[s].iloc[i] = saques.iloc[i]['valor_usd'] * \
                        saques.iloc[i][s + '_p']

            for s in siglas:
                if saques[saques[s] > 0].empty:
                    continue
                arquivo_saques = pd.DataFrame()
                arquivo_saques['name'] = saques[saques[s] > 0]['nome']
                arquivo_saques['email'] = saques[saques[s] > 0]['email']
                arquivo_saques['documento'] = saques[saques[s]
                                                     > 0]['documento']
                arquivo_saques['data_resgate'] = descotizar.strftime(
                    '%Y-%m-%d')
                arquivo_saques['valor_resgate'] = saques[saques[s] > 0][s]
                arquivo_saques['lancamento_caixa'] = ''
                arquivo_saques = arquivo_saques.where(
                    pd.notnull(arquivo_saques), '')
                st.markdown(get_table_download_link_csv(arquivo_saques,
                            f'saques_{s}.csv'), unsafe_allow_html=True)

            st.markdown(get_table_download_link_csv(
                saques, f'saques_consolidado.csv'), unsafe_allow_html=True)

    if process_selectbox == 'Aplicacoes':
        st.header('Aplicacoes')
        st.subheader('Nao esqueca o rebalanceamento antes!')
        st.markdown('''
        **Baixar os arquivos CSV e fazer o upload no sistema:**

        **Aloccacoes.csv** -> https://metabase.backoffice.byebnk.com/question/136-bbapi-alocacoes-dos-clientes

        **Acam.csv** -> Baixar ACAM

        ''')

        alocacoes_file = st.file_uploader("Alocacoes.csv")
        acam_file = st.file_uploader("Acam.csv")

        if alocacoes_file and acam_file is not None:
            alocacoes = pd.read_csv(alocacoes_file, dtype={'documento': str})
            acam = pd.read_csv(acam_file, dtype={'CPF': str})
            acam = acam.rename(
                columns={'CPF': 'documento', 'Valor da M/E': 'Valor'})
            aplicacoes = pd.DataFrame()
            aplicacoes = acam[['Data Transação', 'documento', 'NOME', 'Valor']].merge(alocacoes, on='documento')
            aplicacoes['reit'] = aplicacoes['Valor'] * aplicacoes['reit'] / 100
            aplicacoes['cmmd'] = aplicacoes['Valor'] * aplicacoes['cmmd'] / 100
            aplicacoes['cbb'] = aplicacoes['Valor'] * aplicacoes['cbb'] / 100
            aplicacoes['bond'] = aplicacoes['Valor'] * aplicacoes['bond'] / 100
            aplicacoes['ag'] = aplicacoes['Valor'] * aplicacoes['ag'] / 100
            aplicacoes['bbda'] = aplicacoes['Valor'] * aplicacoes['bbda'] / 100

            for s in siglas:
                lancamentos_caixa = pd.DataFrame()
                if aplicacoes[aplicacoes[s] > 0].empty:
                    continue
                lancamentos_caixa['data'] = aplicacoes[aplicacoes[s]
                                                       > 0]['Data Transação']
                lancamentos_caixa['tipo'] = 'e'
                lancamentos_caixa['valor'] = aplicacoes[aplicacoes[s] > 0][s]
                lancamentos_caixa['historico_caixa'] = aplicacoes[aplicacoes[s] > 0]['nome']
                lancamentos_caixa = lancamentos_caixa.where(
                    pd.notnull(lancamentos_caixa), '')
                st.markdown(get_table_download_link_csv(
                    lancamentos_caixa, f'lancamentos_caixa_{s}.csv'), unsafe_allow_html=True)
            st.markdown(get_table_download_link_csv(
                aplicacoes, f'lancamentos_caixa_consolidado.csv'), unsafe_allow_html=True)

            st.header('Conciliação de caixa')
            st.markdown('''
            **Baixar os arquivos CSV do cotizador e fazer o upload:**

            **Lancamentos.csv** -> Baixar do cotizador
            ''')
            data = st.date_input("Data da aplicacao", datetime.now())
            lancamentos_file = st.file_uploader("Lancamentos.csv")

            if lancamentos_file is not None:
                lancamentos = pd.read_csv(lancamentos_file)
                lancamentos = lancamentos.rename(columns={'historico': 'nome'})
                lancamentos = lancamentos.merge(alocacoes, on='nome')
                arquivo_apliacoes = pd.DataFrame()
                arquivo_apliacoes['livro'] = lancamentos['livro']
                arquivo_apliacoes['name'] = lancamentos['nome']
                arquivo_apliacoes['email'] = lancamentos['email']
                arquivo_apliacoes['documento'] = lancamentos['documento'].astype(
                    str)
                arquivo_apliacoes['data_aplicacao'] = data.strftime('%Y-%m-%d')
                arquivo_apliacoes['valor_aplicacao'] = lancamentos['valor']
                arquivo_apliacoes['lancamento_caixa'] = lancamentos['id']
                st.success('Parabens! Voce brilhou!')
                for l in arquivo_apliacoes.livro.unique():
                    st.markdown(get_table_download_link_csv(arquivo_apliacoes[arquivo_apliacoes.livro == l].drop(
                        'livro', axis=1), f'aplicacoes_{l}.csv'), unsafe_allow_html=True)

    if process_selectbox == 'Conferir BBAPI x Cotizador':
        st.header('Conferir BBAPI x Cotizador')
        st.markdown('''
        **Baixar os arquivos CSV e fazer o upload no sistema:**

        **BBAPI.csv** -> https://metabase.backoffice.byebnk.com/question/143-bbapi-saldos-clientes

        **Cotizador.csv** -> https://metabase.backoffice.byebnk.com/question/137-cotizador-saldos-cotistas

        ''')

        bbapi_file = st.file_uploader("BBAPI.csv")
        cotizador_file = st.file_uploader("Cotizador.csv")

        if bbapi_file and cotizador_file is not None:
            cotizador = pd.read_csv(cotizador_file, dtype={'documento': str})
            bbapi = pd.read_csv(bbapi_file, dtype={'documento': str})
            comp = bbapi.merge(cotizador, how='outer', on='documento')
            comp['saldo_cotizador'][comp['saldo_cotizador'].isna()] = 0
            comp['diff'] = comp['saldo_cotizador'] - comp['saldo_bbapi']
            comp_err = comp[(comp['diff'] > 0.0001) | (comp['diff'] < -0.0001)]
            if comp_err.empty:
                st.success(
                    'Tudo certo! Pode pagar uma cerveja para o Matheus!')
                st.balloons()
            else:
                st.warning('Foram identificados erros!')
                st.write(comp_err['diff'].describe())
                st.markdown(get_table_download_link_csv(
                    comp_err, 'error.csv'), unsafe_allow_html=True)
