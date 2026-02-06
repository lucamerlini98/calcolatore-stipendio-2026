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
        (15000, 0.0173),
        (28000, 0.0193),
        (50000, 0.0333),
        (float("inf"), 0.0333)
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
        (28000, 0.0268),
        (50000, 0.0331),
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
        (50000, 0.0278),
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
    Addizionale regionale IRPEF:
    aliquota UNICA in base alla fascia di reddito.
    NON è progressiva.
    """
    if regione not in ALIQUOTE_REGIONALI:
        return 0.0

    for soglia, aliquota in ALIQUOTE_REGIONALI[regione]:
        if reddito_imponibile <= soglia:
            return reddito_imponibile * aliquota

    return 0.0



# -------------------------
# Funzione per calcolare il netto
# -------------------------
def calcola_dettagli(
    ral,
    regione,
    addizionale_comunale_perc,
    mensilita,
    tipo_contratto,

    buono_giornaliero,
    giorni_buoni,

    assicurazione_sanitaria_perc,

    fondo_pensione_val,
    fondo_pensione_perc,
    contributo_datore_perc,

    premio_risultato,
    premio_modalita,   # "flat" o "irpef"
    premio_flat_perc,      # usato solo se flat
    welfare,

    giorni_lavorati,
    orario_settimanale,
    giorni_ferie
):
    # =========================
    # 1. CONTRIBUTI INPS
    # =========================
    aliquota_inps = 0.0584 if tipo_contratto.lower() == "apprendistato" else 0.0919
    contributi_inps = ral * aliquota_inps

    # =========================
    # 2. TFR
    # =========================
    tfr = ral / 13.5 - ral * 0.005

    # =========================
    # 3. FONDO PENSIONE (deducibile)
    # =========================
    base_fondo = ral - contributi_inps
    if fondo_pensione_val is not None:
        contributo_volontario = fondo_pensione_val
    elif fondo_pensione_perc is not None:
        contributo_volontario = base_fondo * fondo_pensione_perc / 100
    else:
        contributo_volontario = 0.0

    contributo_datore = base_fondo * contributo_datore_perc / 100
    fondo_totale = contributo_volontario + contributo_datore

    # =========================
    # 4. ASSICURAZIONE SANITARIA
    # =========================
    assicurazione = ral * assicurazione_sanitaria_perc / 100

    # =========================
    # 5. PREMIO VARIABILE
    # =========================
    if premio_modalita == "irpef":
        ral_effettiva = ral + premio_risultato
        premio_netto = 0  # viene tassato insieme alla RAL
    else:
        ral_effettiva = ral
        premio_netto = premio_risultato * (1 - premio_flat_perc / 100)

    # =========================
    # 6. IMPONIBILE IRPEF
    # =========================
    imponibile = max(0, ral_effettiva - contributi_inps - contributo_volontario - assicurazione)

    # =========================
    # 7. IRPEF
    # =========================
    if imponibile <= 28000:
        irpef_lorda = imponibile * 0.23
    elif imponibile <= 50000:
        irpef_lorda = 28000 * 0.23 + (imponibile - 28000) * 0.33
    else:
        irpef_lorda = 28000 * 0.23 + 22000 * 0.33 + (imponibile - 50000) * 0.43

    # =========================
    # 8. ADDIZIONALI
    # =========================
    add_regionale = calcola_addizionale_regionale(regione, imponibile)
    add_comunale = imponibile * addizionale_comunale_perc / 100

    if imponibile <= 8500:
        imposta_lorda_totale = 0
    else:
        imposta_lorda_totale = irpef_lorda + add_regionale + add_comunale

    # =========================
    # 9. DETRAZIONI LAVORO + BONUS RENZI
    # =========================

    if imponibile < 8500:
        detrazioni = 0
    elif imponibile <= 15000:
        detrazioni = 1955 + 1200
    elif imponibile <= 28000:
        detrazioni = 1910 + 1190 * (28000 - imponibile) / 13000
    elif imponibile <= 50000:
        detrazioni = 1910 * (50000 - imponibile) / 22000
    else:
        detrazioni = 0

    detrazioni *= giorni_lavorati / 365

    # =========================
    # 10. AGEVOLAZIONI
    # =========================

    if imponibile <= 20000:
        if imponibile <= 8500:
            agevolazioni = imponibile * 0.071
        elif imponibile <= 15000:
            agevolazioni = imponibile * 0.053
        else:
            agevolazioni = imponibile * 0.048
    elif imponibile <= 32000:
        agevolazioni = 1000
    elif imponibile <= 40000:
        agevolazioni = 1000 * (40000 - imponibile) / 8000
    else:
        agevolazioni = 0.0

    # =========================
    # 11. IMPOSTA NETTA
    # =========================
    imposta_netta = max(0, imposta_lorda_totale - detrazioni) - agevolazioni

    # imposta_netta =  imposta_lorda_totale - detrazioni - agevolazioni

    # =========================
    # 12. NETTO BUSTA
    # =========================
    netto_busta = imponibile - imposta_netta  + (premio_netto if premio_modalita=="flat" else 0)

    # =========================
    # 13. BUONI PASTO
    # =========================
    buoni_annui = buono_giornaliero * giorni_buoni
    buoni_mensili = buoni_annui / 12

    # =========================
    # 14. NETTO TOTALE E MENSILE
    # =========================
    netto_totale = netto_busta + buoni_annui + welfare
    netto_mensile = netto_busta / mensilita

    tasse_totali = imposta_lorda_totale

    # =========================
    # 15. NETTO ORARIO
    # =========================
    GIORNI_LAVORATIVI_STANDARD = 253

    giorni_effettivi = GIORNI_LAVORATIVI_STANDARD - giorni_ferie
    ore_giornaliere = orario_settimanale / 5

    ore_lavorate_annue = giorni_effettivi * ore_giornaliere

    netto_orario = netto_busta / ore_lavorate_annue


    return {
        "Stipendio Lordo": ral,
        "Reddito Imponibile Fiscale": imponibile,
        "IRPEF Lorda": irpef_lorda,
        "Addizionale Regionale": add_regionale,
        "Addizionale Comunale": add_comunale,
        "Detrazioni": detrazioni,
        "Agevolazioni": agevolazioni,
        "Tasse Totali": tasse_totali,
        "Stipendio Netto": netto_busta,
        "Stipendio Netto Orario": netto_orario,
        "Buoni Pasto Annui": buoni_annui,
        "Buoni Pasto Mensili": buoni_mensili,
        "Stipendio Netto con buoni": netto_totale,
        "Stipendio Netto Mensile": netto_mensile,
        "Fondo Pensione Totale": fondo_totale,
        "TFR": tfr,
        "Premio Netto": premio_netto,
        "Welfare": welfare,
        "Regione": regione,
        "Tipo Contratto": tipo_contratto
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
    "<h1 style='text-align: center;'>💸 Bella la RAL ma in busta quanto trovo?"
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
        ["Indeterminato", "Apprendistato", "Determinato"],
        index=0  # default Indeterminato
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
            "Lombardia", "Abruzzo", "Basilicata", "Calabria", "Campania",
            "Emilia-Romagna", "Friuli Venezia Giulia", "Lazio",
            "Liguria", "Marche", "Molise",
            "Piemonte", "Puglia", "Sardegna", "Sicilia",
            "Toscana", "Provincia Autonoma di Trento",
            "Provincia Autonoma di Bolzano", "Umbria",
            "Valle d’Aosta", "Veneto"
        ],
        index=0  
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
col1, col2 = st.columns(2)

with col1:
    orario_settimanale = st.number_input(
        "Ore settimanali",
        min_value=1.0,
        max_value=120.0,
        value=40.0,
        step=0.5
    )
with col2:
    giorni_ferie = st.number_input(
        "Giorni di ferie e permessi annui",
        min_value=0,
        max_value=100,
        value=26,
        step=1
    )

# -------------------------
# Benefit e contributi
# -------------------------
st.subheader("💼 Benefit e contributi opzionali")

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

premio_modalita = st.radio(
    "Modalità tassazione premio di risultato/ Variabile:",
    ("Flat (tassazione fissa)", "Aggiunto alla RAL"),
    horizontal=True
)
if premio_modalita == "Flat (tassazione fissa)":
    premio_modalita_val = "flat"
else:
    premio_modalita_val = "irpef"



col1, col2 = st.columns(2)
with col1:
    premio_risultato = st.number_input(
        "Premio / Variabile (€ annuo)",
        min_value=0.0,
        value=0.0,
        step=100.0
    )
    welfare = st.number_input(
        "Importo Welfare detassato (€ annuo)",
        min_value=0.0,
        value=0.0,
        step=50.0
    )
with col2:
    premio_flat_perc = st.number_input(
        "Tassazione premio (%)",
        min_value=0.0,
        max_value=50.0,
        value=1.0,
        step=1.0
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

col1, col2 = st.columns(2)
with col1:
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
with col2:
    contributo_datore_perc = st.number_input(
        "Contributo datoriale (% della RAL)",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1
    )

# =========================
# Calcolo deducibilità fondo pensione
# =========================
# base_fondo = RAL - INPS
base_fondo = lordo_input * (1 - (0.0584 if tipo_contratto.lower() == "apprendistato" else 0.0919))
if fondo_pensione_val is not None:
    contrib_vol = fondo_pensione_val
elif fondo_pensione_perc is not None:
    contrib_vol = base_fondo * fondo_pensione_perc / 100
else:
    contrib_vol = 0.0

contrib_datore = base_fondo * contributo_datore_perc / 100
fondo_totale = contrib_vol + contrib_datore

# soglia deducibilità 2026
soglia_deducibile = 5300

# messaggio colorato
if fondo_totale <= soglia_deducibile:
    restante = soglia_deducibile - fondo_totale
    st.markdown(f"<span style='color:green'>Deducibile ✅, puoi ancora dedurre {restante:.2f} €</span>", unsafe_allow_html=True)
else:
    eccedenza = fondo_totale - soglia_deducibile
    st.markdown(f"<span style='color:red'>Supera la soglia di 5.300€ ❌, eccedenza {eccedenza:.2f} €</span>", unsafe_allow_html=True)

# -------------------------
# Calcolo
# -------------------------
dati = calcola_dettagli(
    ral=lordo_input,
    regione=regione,
    addizionale_comunale_perc=addizionale_comunale_perc,
    mensilita=mensilita,
    tipo_contratto=tipo_contratto,
    buono_giornaliero=buoni_pasto,
    giorni_buoni=giorni_buoni_pasto,
    assicurazione_sanitaria_perc=assicurazione_sanitaria_perc,
    fondo_pensione_val=fondo_pensione_val,
    fondo_pensione_perc=fondo_pensione_perc,
    contributo_datore_perc=contributo_datore_perc,
    premio_risultato=premio_risultato,
    premio_modalita=premio_modalita_val,
    premio_flat_perc=premio_flat_perc,
    welfare=welfare,
    giorni_lavorati=giorni_lavoro,
    orario_settimanale=orario_settimanale,
    giorni_ferie=giorni_ferie
)

# -------------------------
# Risultati
# -------------------------
st.subheader("📊 Risultati Calcolo")

st.metric(
    "💶 Netto Mensile Totale",
    f"{dati['Stipendio Netto Mensile']:.2f} €"
)

col1, col2= st.columns(2)



col1.metric(
    "Buoni pasto mensili",
    f"{dati['Buoni Pasto Mensili']:.2f} €"
)

col2.metric(
    "Buoni pasto + busta paga",
    f"{(dati['Stipendio Netto con buoni']):.2f} €"
)

st.divider()
st.write(f"**Reddito imponibile fiscale:** {dati['Reddito Imponibile Fiscale']:.2f} €")
st.write(f"**Netto annuale:** {dati['Stipendio Netto']:.2f} €")
st.write(f"**Netto orario:** {dati['Stipendio Netto Orario']:.2f} €")
st.write(f"**Tasse totali:** {dati['Tasse Totali']:.2f} €")
st.write(f"**Detrazioni:** {dati['Detrazioni']:.2f} €")
st.write(f"**Buoni pasto annui:** {dati['Buoni Pasto Annui']:.2f} €")
st.write(
    f"**Fondo pensione totale:** {dati['Fondo Pensione Totale']:.2f} € "
    f"(Volontario + Datore)"
)
st.write(f"**TFR stimato:** {dati['TFR']:.2f} €")
st.write(f"**Premio Netto:** {dati['Premio Netto']:.2f} €")
st.write(f"**Welfare detassato:** {dati['Welfare']:.2f} €")


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
        premio_risultato,
        premio_modalita,
        premio_flat_perc,
        welfare,
        giorni_lavoro,
        orario_settimanale,
        giorni_ferie

    )
    for l in range(1000, 80001, 1000)
])

fig = px.line(
    df,
    x="Stipendio Lordo",
    y=[
        "Stipendio Netto", 
        "Tasse Totali",
        "Detrazioni",
        "Agevolazioni"
    ],
    title="Andamento Netto Annuale vs Lordo",
    labels={
        "value": "Euro (€)",
        "variable": "Voce"
    }
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

    try:
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
            premio_risultato,
            premio_modalita,
            premio_flat_perc,
            welfare,
            giorni_lavoro,
            orario_settimanale,
            giorni_ferie

        )

        netto_busta = float(dati_row["Stipendio Netto"])

    except Exception:
        # salta le righe che danno problemi (RAL bassi, imponibile negativo, ecc.)
        continue

    # Differenza marginale
    if netto_precedente is None:
        diff_marginale = None
    else:
        diff_marginale = netto_busta - netto_precedente

    risultati.append({
        "RAL": ral_corrente,
        "Imponibile fiscale": dati_row["Reddito Imponibile Fiscale"],
        "Netto annuale": netto_busta,
        "Differenza marginale netto": diff_marginale,
        f"Netto su {mensilita} mensilità": netto_busta / mensilita,
        "Netto orario": dati_row["Stipendio Netto Orario"],
        "Tasse": dati_row["Tasse Totali"],
        "Detrazioni": dati_row["Detrazioni"],
        "Agevolazioni": dati_row["Agevolazioni"]
    })

    netto_precedente = netto_busta


df_simulazione = pd.DataFrame(risultati).round(2)

st.dataframe(df_simulazione, use_container_width=True, hide_index=True)


st.subheader("💎 Ricchezza Generata")

st.markdown("""
**Quanto questo lavoro ti rende, non solo quanto ti paga.**

Non tutto quello che ricevi dal tuo lavoro vale come denaro liquido:
- 1€ in buoni pasto non vale come 1€ sul conto
- 1€ in welfare ha valore, ma non è libero
- 1€ in TFR o fondo pensione è tuo, ma non lo puoi usare oggi

Qui puoi dire al sistema **quanto per te vale davvero 1€ in ciascuna voce**.
Il risultato è un unico numero che rappresenta la **ricchezza reale generata dal lavoro**.
""")

col1, col2, col3 = st.columns(3)

with col1:
    coeff_buoni = st.number_input(
        "Valore buoni pasto (1€ = …)",
        min_value=0.0,
        max_value=1.0,
        value=0.95,
        step=0.01
    )

with col2:
    coeff_welfare = st.number_input(
        "Valore welfare (1€ = …)",
        min_value=0.0,
        max_value=1.0,
        value=0.95,
        step=0.01
    )

with col3:
    coeff_futuro = st.number_input(
        "Valore fondo pensione / TFR (1€ = …)",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01
    )

ricchezza_generata = (
    dati["Stipendio Netto"]
    + dati["Buoni Pasto Annui"] * coeff_buoni
    + dati["Welfare"] * coeff_welfare
    + (dati["Fondo Pensione Totale"] + dati["TFR"]) * coeff_futuro
)

ricchezza_mensile = ricchezza_generata / 12

giorni_effettivi = 253 - giorni_ferie
ore_giornaliere = orario_settimanale / 5
ore_lavorate_annue = giorni_effettivi * ore_giornaliere
ricchezza_oraria = ricchezza_generata / ore_lavorate_annue

# ricchezza_oraria = ricchezza_generata / ((253 - giorni_ferie) * (orario_settimanale / 5))

col1, col2, col3 = st.columns(3)

col1.metric(
    "💎 Ricchezza Generata Annua",
    f"{ricchezza_generata:,.2f} €"
)

col2.metric(
    "Ricchezza Generata Mensile",
    f"{ricchezza_mensile:,.2f} €"
)

col3.metric(
    "Ricchezza Generata Oraria",
    f"{ricchezza_oraria:,.2f} € /h"
)


import plotly.graph_objects as go

valori = [
    dati["Stipendio Netto"],
    dati["Buoni Pasto Annui"] * coeff_buoni,
    dati["Welfare"] * coeff_welfare,
    (dati["Fondo Pensione Totale"] + dati["TFR"]) * coeff_futuro
]

etichette = [
    "Netto in busta",
    "Buoni pasto (scontati)",
    "Welfare (scontato)",
    "Fondo pensione + TFR (scontati)"
]

fig = go.Figure(
    data=[go.Pie(
        labels=etichette,
        values=valori,
        hole=0.5
    )]
)

fig.update_layout(
    title="Composizione della Ricchezza Generata",
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)


# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2026, Luca Merlini</p>", unsafe_allow_html=True)



