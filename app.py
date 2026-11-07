import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Titulo da pagina
st.set_page_config(page_title="Avaliação", layout="wide")

# Nomes das colunas (em português)
colunas = [
    "Comprimento_Sepala",
    "Largura_Sepala",
    "Comprimento_Petala",
    "Largura_Petala",
    "Especie",
]
numericas = colunas[:4]


# Importação do Dataset (com cache)
@st.cache_data
def carregar_dados():
    caminho = "./iris/iris.csv"
    # header=None evita perder a 1ª linha caso o arquivo não tenha cabeçalho
    df = pd.read_csv(caminho, header=None, names=colunas)
    # Se a 1ª linha for um cabeçalho de texto, remove
    try:
        float(df.iloc[0, 0])
    except ValueError:
        df = df.iloc[1:].reset_index(drop=True)
    # Garante o tipo numérico e remove linhas totalmente vazias
    for c in numericas:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(how="all")
    return df


df = carregar_dados()

# Relatório de sanidade (calculado na base completa)
qtd_nulos = int(df.isna().sum().sum())
qtd_duplicadas = int(df.duplicated().sum())
df = df.dropna().reset_index(drop=True)  # tratamento: remove linhas com NaN

# ------------------------------------------------------------------
# Titulo
st.title("Painel de Plantas")
st.header("Classe de plantas de íris")
st.markdown(
    "O objetivo é classificar três espécies de flores Iris com base nas medidas "
    "de suas pétalas e sépalas. Ele serve como teste padrão para ensinar e "
    "comparar algoritmos de Machine Learning e análise de dados."
)

# ------------------------------------------------------------------
# BARRA LATERAL: identificação + filtros
st.sidebar.title("Identificação do Dataset")
st.sidebar.markdown(
    "**Dataset:** Iris  \n"
    "**Link:** [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/53/iris)  \n"
    "**Autores do app:** Ester Martins e Bruno Vital  \n"
    "**Objetivo:** analisar estatisticamente as medidas das flores por espécie."
)
st.sidebar.divider()

# Filtro categórico
especie = df["Especie"].unique().tolist()
selecionados = st.sidebar.multiselect("Espécie:", especie, default=especie)

# Filtro numérico
minimo = float(df["Comprimento_Sepala"].min())
maximo = float(df["Comprimento_Sepala"].max())
faixa = st.sidebar.slider(
    "Comprimento da sépala (cm):", minimo, maximo, (minimo, maximo), step=0.1
)

# Aplicando os filtros
df_filtrado = df[
    df["Especie"].isin(selecionados)
    & df["Comprimento_Sepala"].between(faixa[0], faixa[1])
]

# Contador dinâmico
pct = len(df_filtrado) / len(df) * 100
st.sidebar.info(
    f"Exibindo {len(df_filtrado)} de {len(df)} registros ({pct:.1f}%)".replace(".", ",")
)

# Se o filtro zerar os dados, para aqui sem quebrar o script
if df_filtrado.empty:
    st.warning("Nenhum registro com os filtros atuais. Ajuste a barra lateral.")
    st.stop()

# ------------------------------------------------------------------
# ABAS
aba1, aba2, aba3, aba4 = st.tabs(
    ["Dicionário e Amostra", "Univariada e Outliers", "Bivariada e Correlação", "Parecer Analítico"]
)

# ---------------------------- ABA 1 -------------------------------
with aba1:
    st.subheader("Dicionário de dados")
    dicionario = pd.DataFrame(
        {
            "Coluna": colunas,
            "Significado": [
                "Comprimento da sépala",
                "Largura da sépala",
                "Comprimento da pétala",
                "Largura da pétala",
                "Espécie da flor (setosa, versicolor, virginica)",
            ],
            "Unidade": ["cm", "cm", "cm", "cm", "-"],
            "Tipo": ["Numérica contínua"] * 4 + ["Categórica nominal"],
        }
    )
    st.dataframe(dicionario, use_container_width=True, hide_index=True)

    st.subheader("Relatório de sanidade")
    c1, c2 = st.columns(2)
    c1.metric("Valores ausentes (NaN) tratados", qtd_nulos)
    c2.metric("Linhas duplicadas", qtd_duplicadas)

    # Exibindo a amostra com st.dataframe
    n_linhas = st.slider(
        "Quantas linhas exibir?", min_value=3, max_value=len(df_filtrado),
        value=min(5, len(df_filtrado)),
    )
    st.subheader(f"Primeiras {n_linhas} Linhas")
    st.dataframe(df_filtrado.head(n_linhas), use_container_width=True)

# ---------------------------- ABA 2 -------------------------------
with aba2:
    var = st.selectbox("Variável:", numericas)
    serie = df_filtrado[var]

    media = serie.mean()
    mediana = serie.median()
    desvio = serie.std()
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Média", f"{media:.3f}")
    m2.metric("Mediana", f"{mediana:.3f}")
    m3.metric("Desvio Padrão", f"{desvio:.3f}")
    m4.metric("IQR", f"{iqr:.3f}")

    st.subheader("Resumo estatístico")
    st.dataframe(serie.describe().to_frame().T, use_container_width=True)

    # Diagnóstico de assimetria
    dif = media - mediana
    if abs(dif) <= 0.1 * desvio:
        st.success("**Média ≈ Mediana:** distribuição aproximadamente simétrica. A média é adequada.")
    elif dif > 0:
        st.warning("**Média > Mediana:** assimetria positiva (cauda à direita). Prefira a mediana.")
    else:
        st.warning("**Média < Mediana:** assimetria negativa (cauda à esquerda). Prefira a mediana.")

    # Histograma e boxplot
    bins = st.slider("Número de bins:", 5, 50, 15)
    g1, g2 = st.columns(2)
    with g1:
        fig, ax = plt.subplots()
        ax.hist(serie, bins=bins, edgecolor="black")
        ax.axvline(media, color="red", linestyle="--", label="Média")
        ax.axvline(mediana, color="green", label="Mediana")
        ax.set_title("Histograma")
        ax.set_xlabel(f"{var} (cm)")
        ax.set_ylabel("Frequência")
        ax.legend()
        st.pyplot(fig)
    with g2:
        fig, ax = plt.subplots()
        ax.boxplot(serie, vert=False)
        ax.set_title("Boxplot")
        ax.set_xlabel(f"{var} (cm)")
        st.pyplot(fig)

    # Limites de Tukey
    st.subheader("Limites de Tukey (1,5 × IQR)")
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    outliers = serie[(serie < lim_inf) | (serie > lim_sup)]

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Limite inferior", f"{lim_inf:.3f}")
    t2.metric("Limite superior", f"{lim_sup:.3f}")
    t3.metric("Outliers", len(outliers))
    t4.metric("% de outliers", f"{len(outliers) / len(serie) * 100:.1f}%")
    if len(outliers) > 0:
        st.dataframe(df_filtrado.loc[outliers.index], use_container_width=True)

# ---------------------------- ABA 3 -------------------------------
with aba3:
    cx, cy, cc = st.columns(3)
    x = cx.selectbox("Eixo X:", numericas, index=2)
    y = cy.selectbox("Eixo Y:", numericas, index=3)
    colorir = cc.checkbox("Colorir pela espécie", value=True)

    fig, ax = plt.subplots()
    if colorir:
        for esp in df_filtrado["Especie"].unique():
            parte = df_filtrado[df_filtrado["Especie"] == esp]
            ax.scatter(parte[x], parte[y], label=esp, alpha=0.8)
        ax.legend()
    else:
        ax.scatter(df_filtrado[x], df_filtrado[y], alpha=0.8)
    ax.set_xlabel(f"{x} (cm)")
    ax.set_ylabel(f"{y} (cm)")
    ax.set_title(f"{y} × {x}")
    st.pyplot(fig)

    # Coeficiente r de Pearson
    if len(df_filtrado) > 2:
        r = df_filtrado[x].corr(df_filtrado[y])
        if abs(r) >= 0.7:
            classe = "forte"
        elif abs(r) >= 0.4:
            classe = "moderada"
        else:
            classe = "fraca/nula"
        sentido = "positiva" if r > 0 else "negativa"
        st.metric("Coeficiente r de Pearson", f"{r:.3f}")
        st.info(f"Correlação **{classe}** e **{sentido}**.")
    else:
        st.info("Dados insuficientes para calcular r.")

    st.error("**Correlação não implica causalidade.**")

    # Matriz de correlação
    st.subheader("Matriz de correlação")
    corr = df_filtrado[numericas].corr()
    fig, ax = plt.subplots()
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels(numericas, rotation=45, ha="right")
    ax.set_yticklabels(numericas)
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center")
    fig.colorbar(im)
    st.pyplot(fig)
    st.dataframe(corr.round(3), use_container_width=True)

# ---------------------------- ABA 4 -------------------------------
with aba4:
    st.subheader("Parecer analítico da equipe")
    st.markdown(
        """
**(a) Quais variáveis exibem forte assimetria e qual a razão prática?**

Considerando a base completa (150 registros), nenhuma variável tem assimetria forte de fato: o coeficiente de assimetria fica abaixo de 0,35 em valor absoluto em todas. O diagnóstico de média × mediana destaca o **Comprimento da Pétala** (média 3,76 < mediana 4,35, diferença de 0,59 cm) e, em menor grau, a **Largura da Pétala** (1,20 < 1,30). Essa diferença não vem de uma cauda longa, e sim da mistura de espécies: a *setosa* tem pétalas muito menores (média de 1,46 cm) que a *versicolor* (4,26 cm) e a *virginica* (5,55 cm), o que forma dois grupos e puxa a média para um valor que quase nenhuma flor tem. Na prática, a média global das pétalas não representa bem nenhuma espécie. Recomenda-se usar a mediana e, principalmente, analisar as medidas por espécie. As sépalas são aproximadamente simétricas.

**(b) Os outliers decorrem de erros ou refletem comportamentos legítimos do domínio?**

Pelo critério de Tukey (1,5 × IQR), só a **Largura da Sépala** apresenta outliers: 4 registros (2,7%), fora do intervalo de 2,05 a 4,05 cm. Três são da *setosa* (larguras de 4,1, 4,2 e 4,4 cm) e um da *versicolor* (2,0 cm). Esses valores não parecem erros, estão numa faixa possível para uma sépala e são coerentes com a espécie de cada flor. Por isso, tratam-se de variação natural entre indivíduos, e não de falha de medição. A decisão mais adequada é manter os registros e apenas sinalizá-los, já que removê-los eliminaria informação real. Sem uma fonte para conferir as medições originais, não é possível garantir que não houve erro, mas nada nos dados indica isso.

**(c) Quais pares exibem correlação relevante e qual o impacto prático?**

Os pares de variáveis **Comprimento_Petala × Largura_Petala** (r ≈ 0,96) e **Comprimento_Sepala × Comprimento_Petala** (r ≈ 0,87) exibem uma forte correlação linear positiva.  
**Impacto prático:** Existe uma relação de crescimento proporcional direto no desenvolvimento morfológico da flor. Na prática, a dimensão do comprimento da pétala permite prever a sua largura com elevada precisão, demonstrando redundância na recolha de dados e dispensando a necessidade de medição dupla em triagens rápidas.

**(d) Que decisão um gestor poderia tomar a partir dos dados filtrados?**

Com base na separabilidade dos dados e nas correlações identificadas, um gestor pode tomar duas decisões estratégicas:
1. **Otimização da recolha no campo:** Priorizar exclusivamente a medição das **pétalas** (comprimento e largura) nos processos manuais de inspeção, dispensando a medição das sépalas e reduzindo o tempo de triagem por muda.

2. **Automação de triagem por Machine Learning:** Implementar um algoritmo simples de classificação em sistemas automatizados de estufas (por exemplo, definir que qualquer flor com comprimento de pétala $< 2,5 { cm}$ pertence à espécie *setosa*), garantindo alta precisão operacional com baixo custo computacional."""
    )

# Identificação do Dataset
st.divider()
st.caption(
    "Fisher, R. (1936). Iris [Dataset]. UCI Machine Learning Repository. "
    "https://doi.org/10.24432/C56C76"
)
