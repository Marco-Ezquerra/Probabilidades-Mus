"""
Mus IA — Web App (Streamlit)
Interfaz para el motor de decisión probabilístico del Mus (baraja 8 reyes).

Uso:
    streamlit run demos/app.py
"""

import sys
from pathlib import Path

# Añadir raíz del proyecto al path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "calculadora_probabilidades_mus"))
sys.path.insert(0, str(_ROOT / "utils"))

import streamlit as st
import pandas as pd
import numpy as np

# ─────────────────────── Constantes ───────────────────────
BARAJA_8R = [1, 4, 5, 6, 7, 10, 11, 12]
NOMBRES_CARTA = {
    1: "As", 4: "Cuatro", 5: "Cinco", 6: "Seis",
    7: "Siete", 10: "Sota", 11: "Caballo", 12: "Rey",
}
POSICIONES = {1: "1 — Mano", 2: "2 — Interior izda.", 3: "3 — Interior dcha.", 4: "4 — Postre"}
PERFILES = ["conservador", "normal", "agresivo"]
PERFILES_LABELS = {"conservador": "🛡️ Conservador", "normal": "⚖️ Normal", "agresivo": "⚔️ Agresivo"}

DESCR_PERFILES = {
    "conservador": "Corta solo con EVs claramente superiores a la media. Reduce el riesgo de exponer manos débiles.",
    "normal":      "Perfil de referencia. Equilibrio entre agresividad y fiabilidad. Umbral p74.",
    "agresivo":    "Mayor tolerancia al riesgo. Corta con EVs por debajo de la media del campo. Umbral p65.",
}

# ─────────────────────── Carga de módulos ─────────────────
@st.cache_resource(show_spinner="Cargando motor IA…")
def _load_motor(perfil: str):
    from motor_decision import MotorDecisionMus
    return MotorDecisionMus(modo_8_reyes=True, perfil=perfil)


@st.cache_data(show_spinner=False)
def _load_politicas():
    """Carga tabla de políticas de Fase 2 si existe."""
    csv_path = _ROOT / "calculadora_probabilidades_mus" / "politicas_optimas_fase2.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


@st.cache_data(show_spinner=False)
def _load_sanity():
    """Carga ranking de EV precomputado."""
    csv_path = _ROOT / "calculadora_probabilidades_mus" / "sanity_check_ev_8reyes.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


# ─────────────────────── Helpers ──────────────────────────
def _mano_key(mano: list) -> str:
    return str(sorted(mano))


def _buscar_politica(df_pol, mano: list, posicion: int) -> pd.DataFrame | None:
    if df_pol is None:
        return None
    mano_str = _mano_key(mano)
    mask = (df_pol["mano"].apply(lambda x: _mano_key(eval(str(x)))) == mano_str) & \
           (df_pol["posicion"] == posicion)
    sub = df_pol[mask].sort_values("reward_medio", ascending=False)
    return sub if not sub.empty else None


def _nombre_descarte(mascara_idx: int, mano: list) -> str:
    """Muestra nombres de las cartas a descartar según máscara de bits."""
    cartas_desc = [NOMBRES_CARTA.get(c, str(c)) for k, c in enumerate(mano) if (mascara_idx >> k) & 1]
    if not cartas_desc:
        return "No descartar ninguna (**MUS sin descarte**)"
    return "Descartar: " + ", ".join(cartas_desc)


# ─────────────────────── UI ───────────────────────────────
st.set_page_config(page_title="Mus IA — Motor de Decisión", page_icon="🎴", layout="wide")
st.title("🎴 Mus IA — Motor de Decisión Probabilístico")
st.caption("Baraja 8 reyes · Cálculo exacto por distribución hipergeométrica + Q-Learning")

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuración")
    perfil = st.radio(
        "Perfil de agresividad",
        PERFILES,
        index=1,
        format_func=lambda p: PERFILES_LABELS[p],
    )
    st.info(DESCR_PERFILES[perfil])

    st.divider()
    posicion = st.selectbox(
        "Tu posición en la mesa",
        list(POSICIONES.keys()),
        format_func=lambda k: POSICIONES[k],
        index=0,
    )
    st.caption(
        "**Mano** (pos. 1) juega primero / **Postre** (pos. 4) pierde empates. "
        "La posición altera P(Cortar) por desempates."
    )

    st.divider()
    st.header("📘 Jerarquía de Juego")
    st.markdown(
        "31 > 32 > 40 > 37 > 36 > 35 > 34 > 33  \n"
        "*(31 = La 31, máxima; 33 = la menor)*"
    )

# ── Selección de cartas ──────────────────────────────────
st.subheader("🃏 Tu mano")
col1, col2, col3, col4 = st.columns(4)
with col1:
    c1 = st.selectbox("Carta 1", BARAJA_8R, index=7, format_func=lambda x: NOMBRES_CARTA[x], key="c1")
with col2:
    c2 = st.selectbox("Carta 2", BARAJA_8R, index=7, format_func=lambda x: NOMBRES_CARTA[x], key="c2")
with col3:
    c3 = st.selectbox("Carta 3", BARAJA_8R, index=0, format_func=lambda x: NOMBRES_CARTA[x], key="c3")
with col4:
    c4 = st.selectbox("Carta 4", BARAJA_8R, index=7, format_func=lambda x: NOMBRES_CARTA[x], key="c4")

mano = [c1, c2, c3, c4]
st.write(f"**Mano seleccionada:** {[NOMBRES_CARTA[c] for c in mano]}")

# ── Calcular ─────────────────────────────────────────────
if st.button("🔮 Analizar mano", type="primary", use_container_width=True):

    motor = _load_motor(perfil)

    with st.spinner("Calculando Valor Esperado…"):
        try:
            resultado = motor.decidir(mano=mano, posicion=posicion)
        except Exception as exc:
            st.error(f"Error al calcular: {exc}")
            st.stop()

    # resultado puede ser dict o tuple — normalizar
    if isinstance(resultado, dict):
        decision = resultado.get("decision", "MUS")
        prob_cortar = resultado.get("prob_cortar", 0.5)
        ev_total = resultado.get("ev_total", 0)
        ev_detalle = resultado.get("ev_por_lance", {})
    elif isinstance(resultado, (list, tuple)) and len(resultado) >= 2:
        decision, prob_cortar = resultado[0], resultado[1]
        ev_total = resultado[2] if len(resultado) > 2 else None
        ev_detalle = resultado[3] if len(resultado) > 3 else {}
    else:
        decision, prob_cortar, ev_total, ev_detalle = str(resultado), 0.5, None, {}

    # ── Resultado principal ──────────────────────────────
    st.divider()
    col_dec, col_prob, col_ev = st.columns([2, 2, 2])

    with col_dec:
        color = "🟢" if str(decision).upper() == "CORTAR" else "🔵"
        st.metric(
            label="Recomendación",
            value=f"{color} {str(decision).upper()}",
        )

    with col_prob:
        if prob_cortar is not None:
            st.metric(
                label="P(Cortar)",
                value=f"{float(prob_cortar):.1%}",
                delta=f"Umbral {PERFILES_LABELS[perfil]}",
            )

    with col_ev:
        if ev_total is not None:
            st.metric(
                label="EV Total",
                value=f"{float(ev_total):.4f}",
            )

    # ── EV desglosado por lance ──────────────────────────
    if ev_detalle:
        st.subheader("📊 EV por lance")
        lances_nombres = {
            "grande": "Grande", "chica": "Chica",
            "pares": "Pares", "juego": "Juego / Punto",
        }
        rows = []
        for k, v in ev_detalle.items():
            rows.append({"Lance": lances_nombres.get(k, k), "EV": round(float(v), 4)})
        if rows:
            df_ev = pd.DataFrame(rows)
            st.bar_chart(df_ev.set_index("Lance"))

    # ── Política óptima de descarte (Fase 2) ────────────
    st.divider()
    st.subheader("♻️ Política de Descarte Óptima — Fase 2")

    df_pol = _load_politicas()
    if df_pol is None:
        st.info(
            "Las políticas de Fase 2 no están disponibles todavía. "
            "Ejecuta `python calculadora_probabilidades_mus/generar_politicas_rollout.py` "
            "para generarlas."
        )
    else:
        sub = _buscar_politica(df_pol, mano, posicion)
        if sub is None or sub.empty:
            st.warning("No se encontró política para esta combinación de mano y posición.")
        else:
            top = sub.iloc[0]
            try:
                mascara = int(top["mascara_idx"])
                reward = float(top["reward_medio"])
                visitas = int(top.get("n_visitas", 0))
                st.success(
                    f"**{_nombre_descarte(mascara, mano)}**  \n"
                    f"Reward medio: **{reward:+.4f}** · {visitas:,} visitas"
                )
            except Exception:
                st.dataframe(top)

            with st.expander("Ver todas las opciones de descarte"):
                show_cols = [c for c in ["mascara_idx", "reward_medio", "n_visitas"] if c in sub.columns]
                st.dataframe(sub[show_cols].head(10).reset_index(drop=True))

# ── Ranking de manos ────────────────────────────────────
st.divider()
st.subheader("🏆 Ranking de Manos — Extremos por EV")

df_ev_ranking = _load_sanity()
if df_ev_ranking is not None:
    # Filtrar por posicion actual si la columna existe
    col_pos = None
    for c in df_ev_ranking.columns:
        if str(posicion) in c and "ev" in c.lower():
            col_pos = c
            break
    if col_pos is None:
        col_pos = df_ev_ranking.columns[df_ev_ranking.columns.str.lower().str.contains("ev")][0] if any(
            df_ev_ranking.columns.str.lower().str.contains("ev")
        ) else df_ev_ranking.columns[-1]

    col_mano = df_ev_ranking.columns[0]
    df_show = df_ev_ranking[[col_mano, col_pos]].rename(columns={col_mano: "Mano", col_pos: "EV"})
    df_show = df_show.sort_values("EV", ascending=False).reset_index(drop=True)

    col_top, col_bot = st.columns(2)
    with col_top:
        st.markdown("**Top 5**")
        st.dataframe(df_show.head(5), use_container_width=True, hide_index=True)
    with col_bot:
        st.markdown("**Bottom 5**")
        st.dataframe(df_show.tail(5).iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.info("Ejecuta `sanity_check_ev.py` para generar el ranking precomputado.")

# ── Footer ───────────────────────────────────────────────
st.divider()
st.caption(
    "Motor IA · Probabilidades-Mus v2.5 · "
    "[GitHub](https://github.com/Marco-Ezquerra/Probabilidades-Mus)"
)
