import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# ADDIZIONALI REGIONALI
# ======================

ALIQUOTE_REGIONALI = {
    "Lazio": [
        (15000, 0.0173),
        (float("inf"), 0.0333)
    ],
    "Provincia Autonoma di Bolzano": [
        (50000, 0.0123),
        (float("inf"), 0.0173)
    ],
    "Provincia Autonoma di Trento": [
        (50000, 0.0123),
        (float("inf"), 0.0173)
    ],
    "Sicilia": [
        (float("inf"), 0.0123)
    ],
    "Puglia": [
        (15000, 0.0133),
        (28000, 0.0143),
        (50000, 0.0163),
        (float("inf"), 0.0185)
    ],
    "Sardegna": [
        (float("inf"), 0.0123)
    ],
    "Calabria": [
        (float("inf"), 0.0173)
    ],
    "Molise": [
        (15000, 0.0203),
        (28000, 0.0223),
        (50000, 0.0363),
        (float("inf"), 0.0363)
    ],
    "Friuli Venezia Giulia": [
        (15000, 0.0070),
        (float("inf"), 0.0123)
    ],
    "Lombardia": [
        (15000, 0.0123),
        (28000, 0.0158),
        (50000, 0.0172),
        (float("inf"), 0.0173)
    ],
    "Liguria": [
        (28000, 0.0123),
        (50000, 0.0318),
        (float("inf"), 0.0323)
    ],
    "Marche": [
        (15000, 0.0123),
        (28000, 0.0153),
        (50000, 0.0170),
        (float("inf"), 0.0173)
    ],
    "Umbria": [
        (15000, 0.0173),
        (28000, 0.0302),
        (50000, 0.0312),
        (float("inf"), 0.0333)
    ],
    "Valle d’Aosta": [
        (float("inf"), 0.0123)
    ],
    "Piemonte": [
        (15000, 0.0162),
        (28000, 0.0213),
        (50000, 0.0275),
        (float("inf"), 0.0333)
    ],
    "Abruzzo": [
        (28000, 0.0167),
        (50000, 0.0287),
        (float("inf"), 0.0333)
    ],
    "Veneto": [
        (float("inf"), 0.0123)
    ],
    "Emilia-Romagna": [
        (15000, 0.0133),
        (28000, 0.0193),
        (50000, 0.0293),
        (float("inf"), 0.0333)
    ],
    "Toscana": [
        (15000, 0.0142),
        (28000, 0.0143),
        (50000, 0.0332),
        (float("inf"), 0.0333)
    ],
    "Basilicata": [
        (float("inf"), 0.0123)
    ],
    "Campania": [
        (15000, 0.0173),
        (28000, 0.0296),
        (50000, 0.0320),
        (float("inf"), 0.0333)
    ]
}


def calcola_addizionale_regionale(regione: str, reddito_imponibile: float) -> float:
    """
    Calcola l'addizionale regionale IRPEF in base alla regione e al reddito imponibile.
    Gestisce automaticamente regioni a 1, 2, 3 o 4 scaglioni.
    """
    if regione not in ALIQUOTE_REGIONALI:
        return 0.0

    scaglioni = ALIQUOTE_REGIONALI[regione]
    imposta = 0.0
    precedente = 0.0

    for soglia, aliquota in scaglioni:
        if reddito_imponibile > soglia:
            imposta += (soglia - precedente) * aliquota
            precedente = soglia
        else:
            imposta += (reddito_imponibile - precedente) * aliquota
            break

    return imposta

# -------------------------
# Funzione per calcolare il netto
# -------------------------
def calcola_dettagli(
    stipendio_lordo, regione, addizionale_comunale_perc, mensilita, tipo_contratto,
    buoni_pasto_giornalieri, giorni_buoni_pasto,
    assicurazione_sanitaria_perc,
    fondo_pensione_val, fondo_pensione_perc,
    contributo_datore_perc,
    giorni_lavoro
):
    # =========================
    # 1. REDDITO IMPONIBILE CONTRIBUTIVO (INPS)
    # =========================
    if tipo_contratto.lower() == "apprendistato":
        reddito_imponibile_contributivo = stipendio_lordo * (1 - 0.0584)
    else:
        reddito_imponibile_contributivo = stipendio_lordo * (1 - 0.0919)

    # =========================
    # 2. FONDO PENSIONE
    # =========================
    if fondo_pensione_val is not None:
        contributo_volontario = fondo_pensione_val
    elif fondo_pensione_perc is not None:
        contributo_volontario = stipendio_lordo * (fondo_pensione_perc / 100)
    else:
        contributo_volontario = 0.0

    contributo_datore = stipendio_lordo * (contributo_datore_perc / 100)
    fondo_pensione_totale = contributo_volontario + contributo_datore

    # =========================
    # 3. ALTRI ONERI DEDUCIBILI
    # =========================
    costo_assicurazione = stipendio_lordo * (assicurazione_sanitaria_perc / 100)

    # =========================
    # 4. REDDITO IMPONIBILE FISCALE
    # =========================
    reddito_imponibile = max(
        0.0,
        reddito_imponibile_contributivo
        - contributo_volontario
        - costo_assicurazione
    )

    irpef = add_reg = add_com = detrazioni = agevolazioni = 0.0

    # =========================
    # 5. CALCOLO TASSE
    # =========================
    if reddito_imponibile < 8500:
        tasse_totali = 0.0
        agevolazioni = reddito_imponibile * 0.071
        stipendio_netto_busta = reddito_imponibile + agevolazioni
    else:
        if reddito_imponibile <= 28000:
            irpef = reddito_imponibile * 0.23
        elif reddito_imponibile <= 50000:
            irpef = (28000 * 0.23) + ((reddito_imponibile - 28000) * 0.33)
        else:
            irpef = (
                (28000 * 0.23)
                + (22000 * 0.35)
                + ((reddito_imponibile - 50000) * 0.43)
            )

        add_reg = calcola_addizionale_regionale(regione, reddito_imponibile)
        add_com = reddito_imponibile * (addizionale_comunale_perc / 100)

        tasse_totali = irpef + add_reg + add_com

        # =========================
        # 6. DETRAZIONI
        # =========================
        if reddito_imponibile <= 15000:
            detrazioni = max(1955, 690) + 1200
        elif reddito_imponibile <= 28000:
            detrazioni = 1910 + 1190 * (28000 - reddito_imponibile) / (28000 - 15000)
        elif reddito_imponibile <= 50000:
            detrazioni = 1910 * (50000 - reddito_imponibile) / (50000 - 28000)

        # =========================
        # 6.1. AGEVOLAZIONI
        # =========================
        # if reddito_imponibile <= 20000:
        #     agevolazioni = reddito_imponibile * 0.048
        # elif reddito_imponibile <= 32000:
        #     agevolazioni = 1000
        # elif reddito_imponibile <= 40000:
        #     agevolazioni = 1000 * (40000 - reddito_imponibile) / (40000 - 32000)

        stipendio_netto_busta = (
            reddito_imponibile - tasse_totali + detrazioni + agevolazioni
        )

    # =========================
    # 7. BUONI PASTO
    # =========================
    buoni_pasto_annui = buoni_pasto_giornalieri * giorni_buoni_pasto
    buoni_pasto_mensili = buoni_pasto_annui / 12

    # =========================
    # 8. NETTI FINALI
    # =========================
    stipendio_netto_totale = stipendio_netto_busta + buoni_pasto_annui
    stipendio_netto_mensile = stipendio_netto_totale / mensilita

    # =========================
    # 9. OUTPUT
    # =========================
    return {
        "Stipendio Lordo": stipendio_lordo,
        "Reddito Imponibile Contributivo": reddito_imponibile_contributivo,
        "Reddito Imponibile Fiscale": reddito_imponibile,
        "Stipendio Netto (senza buoni)": stipendio_netto_busta,
        "Stipendio Netto Totale": stipendio_netto_totale,
        "Stipendio Netto Mensile": stipendio_netto_mensile,
        "Buoni Pasto Annui": buoni_pasto_annui,
        "Buoni Pasto Mensili": buoni_pasto_mensili,
        "IRPEF": irpef,
        "Addizionale Regionale": add_reg,
        "Addizionale Comunale": add_com,
        "Tasse Totali": tasse_totali,
        "Detrazioni": detrazioni,
        "Agevolazioni": agevolazioni,
        "Contributo Volontario Fondo Pensione": contributo_volontario,
        "Contributo Datoriale Fondo Pensione": contributo_datore,
        "Fondo Pensione Totale": fondo_pensione_totale,
        "Costo Assicurazione Sanitaria": costo_assicurazione,
        "Tipo Contratto": tipo_contratto,
        "Regione": regione,
        "Giorni Lavoro": giorni_lavoro,
        "Giorni Buoni Pasto": giorni_buoni_pasto
    }


# -------------------------
# Interfaccia Streamlit
# -------------------------
st.set_page_config(
    page_title="Calcolatore Stipendio Netto",
    page_icon="💶",
    layout="centered"
)

# Titolo
st.markdown(
    "<h1 style='text-align: center;'>💸 Bella la RAL ma in busta che trovo?"
    "<br><small>2026 Edition</small></h1>",
    unsafe_allow_html=True
)
st.write(
    "Inserisci i tuoi dati per stimare il netto in busta paga, i benefit "
    "e i dettagli fiscali in base alla tua situazione."
)

# -------------------------
# Input principali
# -------------------------
col1, col2 = st.columns(2)

lordo_input = col1.number_input(
    "Stipendio Lordo Annuale (€)",
    min_value=1000,
    max_value=200000,
    step=1000,
    value=30000
)

mensilita = col2.number_input(
    "Numero di Mensilità",
    min_value=12,
    max_value=15,
    step=1,
    value=13
)

# -------------------------
# Dati contrattuali
# -------------------------
col1, col2 = st.columns(2)

with col1:
    tipo_contratto = st.selectbox(
        "Tipo di Contratto",
        ["Apprendistato", "Determinato", "Indeterminato"]
    )

with col2:
    giorni_lavoro = st.number_input(
        "Giorni di lavoro dipendente",
        min_value=0,
        max_value=365,
        value=365,
        step=1
    )

col3, col4 = st.columns(2)

with col3:
    regione = st.selectbox(
        "Regione di Residenza",
        [
            "Abruzzo", "Basilicata", "Calabria", "Campania",
            "Emilia-Romagna", "Friuli Venezia Giulia", "Lazio",
            "Liguria", "Lombardia", "Marche", "Molise",
            "Piemonte", "Puglia", "Sardegna", "Sicilia",
            "Toscana", "Provincia Autonoma di Trento",
            "Provincia Autonoma di Bolzano", "Umbria",
            "Valle d’Aosta", "Veneto"
        ]
    )

with col4:
    addizionale_comunale_perc = st.number_input(
        "Addizionale Comunale (%)",
        min_value=0.0,
        max_value=2.0,
        value=0.8,
        step=0.1,
        help="Es. Milano 0.8%"
    )

# -------------------------
# Benefit e contributi
# -------------------------
st.subheader("💼 Benefit e contributi opzionali")

# ---- Buoni pasto (DOPPIA CELLA)
col1, col2 = st.columns(2)

with col1:
    buoni_pasto = st.number_input(
        "Importo buono pasto giornaliero (€)",
        min_value=0.0,
        value=8.0,
        step=0.1
    )

with col2:
    giorni_buoni_pasto = st.number_input(
        "Giorni annuali con buono pasto",
        min_value=0,
        max_value=365,
        value=220,
        step=1
    )

assicurazione_sanitaria_perc = st.number_input(
    "Costo assicurazione sanitaria (% del reddito lordo)",
    min_value=0.0,
    value=0.0,
    step=0.1
)

# -------------------------
# Fondo pensione
# -------------------------
st.markdown("### 🏦 Fondo pensione")

modo_fondo = st.radio(
    "Contributo volontario:",
    ("Importo fisso (€ annuo)", "Percentuale della RAL (%)"),
    horizontal=True
)

if modo_fondo == "Importo fisso (€ annuo)":
    fondo_pensione_val = st.number_input(
        "Importo volontario annuo (€)",
        min_value=0.0,
        value=0.0,
        step=50.0
    )
    fondo_pensione_perc = None
else:
    fondo_pensione_val = None
    fondo_pensione_perc = st.number_input(
        "Percentuale volontaria della RAL (%)",
        min_value=0.0,
        value=2.0,
        step=0.1
    )

contributo_datore_perc = st.number_input(
    "Contributo datoriale (% della RAL)",
    min_value=0.0,
    max_value=10.0,
    value=1.0,
    step=0.1
)

# -------------------------
# Calcolo
# -------------------------
dati = calcola_dettagli(
    lordo_input,
    regione,
    addizionale_comunale_perc,
    mensilita,
    tipo_contratto,
    buoni_pasto,
    giorni_buoni_pasto,
    assicurazione_sanitaria_perc,
    fondo_pensione_val,
    fondo_pensione_perc,
    contributo_datore_perc,
    giorni_lavoro
)

# -------------------------
# Risultati
# -------------------------
st.subheader("📊 Risultati Calcolo")

st.metric(
    "💶 Netto Mensile Totale",
    f"{dati['Stipendio Netto Mensile']:.2f} €"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Netto in busta (mensile)",
    f"{dati['Stipendio Netto (senza buoni)'] / mensilita:.2f} €"
)

col2.metric(
    "Buoni pasto mensili",
    f"{dati['Buoni Pasto Mensili']:.2f} €"
)

col3.metric(
    "Totale benefit + busta",
    f"{(dati['Stipendio Netto (senza buoni)'] / mensilita + dati['Buoni Pasto Mensili']):.2f} €"
)

st.divider()

st.write(f"**Netto annuale in busta:** {dati['Stipendio Netto (senza buoni)']:.2f} €")
st.write(f"**Buoni pasto annui:** {dati['Buoni Pasto Annui']:.2f} €")
st.write(f"**Tasse totali:** {dati['Tasse Totali']:.2f} €")
st.write(f"**Detrazioni:** {dati['Detrazioni']:.2f} €")
st.write(
    f"**Fondo pensione totale:** {dati['Fondo Pensione Totale']:.2f} € "
    f"(Volontario + Datore)"
)
st.write(f"**Reddito imponibile fiscale:** {dati['Reddito Imponibile Fiscale']:.2f} €")
st.write(f"**Regione:** {dati['Regione']} — **Contratto:** {dati['Tipo Contratto']}")

# -------------------------
# Grafico
# -------------------------
df = pd.DataFrame([
    calcola_dettagli(
        l,
        regione,
        addizionale_comunale_perc,
        mensilita,
        tipo_contratto,
        buoni_pasto,
        giorni_buoni_pasto,
        assicurazione_sanitaria_perc,
        fondo_pensione_val,
        fondo_pensione_perc,
        contributo_datore_perc,
        giorni_lavoro
    )
    for l in range(1000, 80001, 1000)
])

fig = px.line(
    df,
    x="Stipendio Lordo",
    y=["Stipendio Netto Totale", "Tasse Totali"],
    title="Andamento Netto vs Lordo"
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Tabella simulazione RAL
# -------------------------
st.subheader("📋 Simulazione dettagliata RAL")

col1, col2 = st.columns(2)

ral_iniziale = col1.number_input(
    "RAL iniziale (€)",
    min_value=0,
    value=10000,
    step=500
)

step_ral = col2.number_input(
    "Step incremento RAL (€)",
    min_value=100,
    value=1000,
    step=100
)

NUM_RIGHE = 50

risultati = []
netto_precedente = None

for i in range(NUM_RIGHE):
    ral_corrente = ral_iniziale + i * step_ral

    dati_row = calcola_dettagli(
        ral_corrente,
        regione,
        addizionale_comunale_perc,
        mensilita,
        tipo_contratto,
        buoni_pasto,
        giorni_buoni_pasto,
        assicurazione_sanitaria_perc,
        fondo_pensione_val,
        fondo_pensione_perc,
        contributo_datore_perc,
        giorni_lavoro
    )

    netto_attuale = dati_row["Stipendio Netto Totale"]

    # Differenza marginale
    if netto_precedente is None:
        diff_marginale = None
    else:
        diff_marginale = netto_attuale - netto_precedente

    risultati.append({
        "Stipendio Lordo": ral_corrente,
        "Reddito Imponibile Fiscale": dati_row["Reddito Imponibile Fiscale"],
        "Stipendio Netto Totale": netto_attuale,
        "Tasse Totali": dati_row["Tasse Totali"],
        "Detrazioni": dati_row["Detrazioni"],
        "Differenza Marginale Netto": diff_marginale,
        f"Stipendio Netto Mensile su {mensilita}": netto_attuale / mensilita
    })

    netto_precedente = netto_attuale

df_simulazione = pd.DataFrame(risultati)

# Formattazione più leggibile
df_simulazione = df_simulazione.round(2)

st.dataframe(
    df_simulazione,
    use_container_width=True,
    hide_index=True
)


# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2025, Luca Merlini</p>", unsafe_allow_html=True)
