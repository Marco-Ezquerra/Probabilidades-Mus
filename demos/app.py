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

# Mapa de equipos: A=(1,3), B=(2,4)
_EQUIPO_MAP = {1: (3, [2, 4]), 2: (4, [1, 3]), 3: (1, [2, 4]), 4: (2, [1, 3])}

# ─────────────────────── Carga de módulos ─────────────────
@st.cache_resource(show_spinner="Cargando motor IA…")
def _load_motor(perfil: str):
    from motor_decision import MotorDecisionMus
    return MotorDecisionMus(modo_8_reyes=True, perfil=perfil)


@st.cache_data(show_spinner=False)
def _load_politicas():
    csv_path = _ROOT / "calculadora_probabilidades_mus" / "politicas_optimas_fase2.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


@st.cache_data(show_spinner=False)
def _load_sanity():
    csv_path = _ROOT / "calculadora_probabilidades_mus" / "sanity_check_ev_8reyes.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


@st.cache_data(show_spinner=False)
def _load_segundas():
    """Carga tabla de probabilidades a segundas dadas (todas las posiciones)."""
    csv_path = _ROOT / "calculadora_probabilidades_mus" / "probabilidades_segundas.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return df
    return None


# ─────────────────────── Helpers ──────────────────────────
def _mano_key(mano: list) -> str:
    return str(sorted(mano))


def _buscar_politica(df_pol, mano: list, posicion: int):
    if df_pol is None:
        return None
    mano_str = _mano_key(mano)
    mask = (df_pol["mano"].apply(lambda x: _mano_key(eval(str(x)))) == mano_str) & \
           (df_pol["posicion"] == posicion)
    sub = df_pol[mask].sort_values("reward_medio", ascending=False)
    return sub if not sub.empty else None


def _nombre_descarte(mascara_idx: int, mano: list) -> str:
    cartas_desc = [NOMBRES_CARTA.get(c, str(c)) for k, c in enumerate(mano) if (mascara_idx >> k) & 1]
    if not cartas_desc:
        return "No descartar ninguna (guardar toda la mano)"
    return "Descartar: " + ", ".join(cartas_desc)


def _buscar_segundas(df_seg, mano: list, posicion: int,
                     n_comp: int, n_rival1: int, n_rival2: int):
    """Busca probabilidades a segundas para una mano, posición y config de cartas guardadas."""
    if df_seg is None:
        return None
    mano_str = _mano_key(mano)
    mask = (
        (df_seg["mano"].apply(lambda x: _mano_key(eval(str(x)))) == mano_str) &
        (df_seg["posicion_focal"] == posicion) &
        (df_seg["n_kept_comp"] == n_comp) &
        (df_seg["n_kept_rival1"] == n_rival1) &
        (df_seg["n_kept_rival2"] == n_rival2)
    )
    hits = df_seg[mask]
    return hits.iloc[0] if not hits.empty else None


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
    partner_pos, rivales = _EQUIPO_MAP[posicion][0], _EQUIPO_MAP[posicion][1]
    st.caption(
        f"**Mano** (pos. 1) juega primero / **Postre** (pos. 4) pierde empates.  \n"
        f"Tu compañero: J{partner_pos}  ·  Rivales: J{rivales[0]} y J{rivales[1]}"
    )

    st.divider()
    st.header("📘 Jerarquía de Juego")
    st.markdown(
        "31 > 32 > 40 > 37 > 36 > 35 > 34 > 33  \n"
        "*(31 = La 31, máxima; 33 = la menor)*"
    )


# ════════════════════════════════════════════════════════
#  PESTAÑAS PRINCIPALES
# ════════════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["🃏 Primeras Dadas", "🔄 Segundas Dadas", "📊 Ranking de Manos"])

# ══════════════════════════════════════
#  TAB 1 — PRIMERAS DADAS
# ══════════════════════════════════════
with tab1:
    st.subheader("🃏 Tu mano (primeras dadas)")
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
    st.write(f"**Mano:** {' · '.join(NOMBRES_CARTA[c] for c in mano)}")

    if st.button("🔮 Analizar mano", type="primary", use_container_width=True):
        motor = _load_motor(perfil)

        with st.spinner("Calculando Valor Esperado…"):
            try:
                # decidir() devuelve (decision_bool, P_cortar, EV_total, desglose)
                decision_bool, prob_cortar, ev_total, desglose = motor.decidir(
                    mano=mano, posicion=posicion
                )
                decision = "CORTAR" if decision_bool else "MUS"
            except Exception as exc:
                st.error(f"Error al calcular: {exc}")
                st.stop()

        # ── Resultado principal ──────────────────────────────
        st.divider()
        col_dec, col_prob, col_ev = st.columns(3)
        with col_dec:
            color = "🟢" if decision == "CORTAR" else "🔵"
            st.metric("Recomendación", f"{color} {decision}")
        with col_prob:
            st.metric("P(Cortar)", f"{prob_cortar:.1%}", delta=f"Perfil {perfil}")
        with col_ev:
            st.metric("EV Total", f"{ev_total:.4f}")

        # ── EV desglosado ────────────────────────────────────
        st.subheader("📊 EV por lance")
        lances_data = [
            ("Grande",  desglose.get("grande", {}).get("decision", 0)),
            ("Chica",   desglose.get("chica",  {}).get("decision", 0)),
            ("Pares",   desglose.get("pares",  {}).get("decision", 0)),
            ("Juego",   desglose.get("juego",  {}).get("decision", 0)),
            ("Punto",   desglose.get("punto",  {}).get("decision", 0)),
        ]
        df_lances = pd.DataFrame(lances_data, columns=["Lance", "EV"])

        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.bar_chart(df_lances.set_index("Lance"))
        with col_table:
            analisis = desglose.get("analisis_mano", {})
            st.markdown("**Características**")
            st.markdown(f"- Pares: **{analisis.get('tipo_pares', '—')}**")
            juego_raw = analisis.get("valor_juego_raw", 0)
            st.markdown(f"- Juego: **{'Sí — ' + str(juego_raw) if juego_raw else 'No'}**")
            st.markdown(f"- W pares: **{analisis.get('W_pares', 0)}**")
            st.markdown(f"- W juego: **{analisis.get('W_juego', 0)}**")

        # ── Política óptima de descarte (Fase 2) ────────────
        st.divider()
        st.subheader("♻️ Política de Descarte Óptima — Fase 2")

        df_pol = _load_politicas()
        if df_pol is None:
            st.info("Políticas de Fase 2 no disponibles. Ejecuta `generar_politicas_rollout.py`.")
        else:
            sub = _buscar_politica(df_pol, mano, posicion)
            if sub is None or sub.empty:
                st.warning("No se encontró política para esta mano y posición.")
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
                    show_cols = [c for c in ["mascara_idx", "reward_medio", "n_visitas"]
                                 if c in sub.columns]
                    st.dataframe(sub[show_cols].head(10).reset_index(drop=True))


# ══════════════════════════════════════
#  TAB 2 — SEGUNDAS DADAS
# ══════════════════════════════════════
with tab2:
    st.subheader("🔄 Probabilidades a Segundas Dadas")
    st.markdown(
        "Tras el descarte, observas cuántas cartas guarda cada jugador. "
        "Esa información actualiza las probabilidades de victoria en cada lance."
    )

    df_seg = _load_segundas()
    if df_seg is None:
        st.warning(
            "⏳ Las probabilidades a segundas aún no están disponibles.  \n"
            "La simulación está en curso (puede tardar ~1h con 4 workers).  \n"
            "Cuando termine, reinicia la app para cargar los datos."
        )
    else:
        partner_pos2, rivales2 = _EQUIPO_MAP[posicion][0], _EQUIPO_MAP[posicion][1]

        st.info(
            f"**Posición {posicion}** — Compañero: J{partner_pos2} · "
            f"Rivales: J{rivales2[0]} y J{rivales2[1]}"
        )

        # ── Cartas guardadas ─────────────────────────────────
        st.markdown("**¿Cuántas cartas guarda cada jugador?**")
        col_comp, col_r1, col_r2 = st.columns(3)
        with col_comp:
            n_comp = st.selectbox(
                f"J{partner_pos2} — Compañero",
                [1, 2, 3, 4], index=2, key="n_comp"
            )
        with col_r1:
            n_rival1 = st.selectbox(
                f"J{rivales2[0]} — Rival 1",
                [1, 2, 3, 4], index=1, key="n_rival1"
            )
        with col_r2:
            n_rival2 = st.selectbox(
                f"J{rivales2[1]} — Rival 2",
                [1, 2, 3, 4], index=1, key="n_rival2"
            )

        # ── Mano final propia ────────────────────────────────
        st.markdown("**Tu mano final (tras las segundas):**")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            s1 = st.selectbox("Carta 1", BARAJA_8R, index=7,
                              format_func=lambda x: NOMBRES_CARTA[x], key="s1")
        with col_s2:
            s2 = st.selectbox("Carta 2", BARAJA_8R, index=7,
                              format_func=lambda x: NOMBRES_CARTA[x], key="s2")
        with col_s3:
            s3 = st.selectbox("Carta 3", BARAJA_8R, index=0,
                              format_func=lambda x: NOMBRES_CARTA[x], key="s3")
        with col_s4:
            s4 = st.selectbox("Carta 4", BARAJA_8R, index=7,
                              format_func=lambda x: NOMBRES_CARTA[x], key="s4")
        mano_seg = [s1, s2, s3, s4]

        if st.button("📡 Calcular probabilidades a segundas", type="primary", use_container_width=True):
            row = _buscar_segundas(df_seg, mano_seg, posicion, n_comp, n_rival1, n_rival2)

            if row is None:
                st.warning("No se encontraron datos para esta combinación. Prueba otra mano o config.")
            else:
                st.divider()
                st.markdown("### Probabilidades de victoria condicionadas")
                col_g, col_c, col_p, col_j = st.columns(4)

                prob_g = float(row["prob_grande"])
                prob_c = float(row["prob_chica"])
                prob_p = float(row["prob_pares"])
                prob_j = float(row["prob_juego"])

                with col_g:
                    st.metric("Grande", f"{prob_g:.1%}", delta=f"{prob_g - 0.5:+.1%}")
                with col_c:
                    st.metric("Chica", f"{prob_c:.1%}", delta=f"{prob_c - 0.5:+.1%}")
                with col_p:
                    st.metric("Pares (equipo)", f"{prob_p:.1%}", delta=f"{prob_p - 0.5:+.1%}")
                with col_j:
                    st.metric("Juego/Punto (equipo)", f"{prob_j:.1%}", delta=f"{prob_j - 0.5:+.1%}")

                st.caption(
                    f"Estimado con {int(row.get('n_sims', 3000)):,} simulaciones Monte Carlo.  \n"
                    f"Config: Compañero guarda **{n_comp}** · "
                    f"Rival 1 guarda **{n_rival1}** · Rival 2 guarda **{n_rival2}**"
                )

                # ── Contexto ─────────────────────────────────
                st.divider()
                st.markdown("**Señales del entorno**")
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    total_rival = n_rival1 + n_rival2
                    if total_rival >= 7:
                        st.error(f"⚠️ Rivales guardan **{total_rival}** cartas — probablemente mano fuerte.")
                    elif total_rival <= 4:
                        st.success(f"✅ Rivales guardan solo **{total_rival}** cartas — probable mano débil.")
                    else:
                        st.warning(f"❓ Rivales guardan **{total_rival}** cartas — situación ambigua.")
                with col_i2:
                    if n_comp >= 3:
                        st.success(f"✅ Compañero guarda **{n_comp}** cartas — buen soporte esperado.")
                    else:
                        st.info(f"ℹ️ Compañero guarda **{n_comp}** cartas — soporte incierto.")

        # ── Tabla de exploración completa ───────────────────
        with st.expander("📋 Ver tabla completa de configs para esta mano y posición"):
            mano_str_exp = _mano_key(mano_seg)
            df_mano_pos = df_seg[
                (df_seg["mano"].apply(lambda x: _mano_key(eval(str(x)))) == mano_str_exp) &
                (df_seg["posicion_focal"] == posicion)
            ][["n_kept_comp", "n_kept_rival1", "n_kept_rival2",
               "prob_grande", "prob_chica", "prob_pares", "prob_juego"]].copy()

            if df_mano_pos.empty:
                st.info("No hay datos todavía para esta mano.")
            else:
                df_mano_pos = df_mano_pos.sort_values(
                    ["n_kept_comp", "n_kept_rival1", "n_kept_rival2"]
                ).reset_index(drop=True)
                st.dataframe(
                    df_mano_pos.style.format({
                        "prob_grande": "{:.3f}", "prob_chica": "{:.3f}",
                        "prob_pares":  "{:.3f}", "prob_juego": "{:.3f}"
                    }),
                    use_container_width=True
                )


# ══════════════════════════════════════
#  TAB 3 — RANKING EV
# ══════════════════════════════════════
with tab3:
    st.subheader("🏆 Ranking de Manos — Valor Esperado")

    df_ev_ranking = _load_sanity()
    if df_ev_ranking is not None:
        col_pos = None
        for c in df_ev_ranking.columns:
            if str(posicion) in c and "ev" in c.lower():
                col_pos = c
                break
        if col_pos is None:
            ev_cols = [c for c in df_ev_ranking.columns if "ev" in c.lower()]
            col_pos = ev_cols[0] if ev_cols else df_ev_ranking.columns[-1]

        col_mano = df_ev_ranking.columns[0]
        lbl = f"EV (pos. {posicion})"
        df_show = df_ev_ranking[[col_mano, col_pos]].rename(
            columns={col_mano: "Mano", col_pos: lbl}
        )
        df_show = df_show.sort_values(lbl, ascending=False).reset_index(drop=True)
        df_show.index += 1

        col_top, col_bot = st.columns(2)
        with col_top:
            st.markdown("**🏅 Top 10**")
            st.dataframe(df_show.head(10), use_container_width=True)
        with col_bot:
            st.markdown("**⚠️ Bottom 10**")
            st.dataframe(df_show.tail(10).iloc[::-1], use_container_width=True)

        with st.expander("Ver las 330 manos completas"):
            st.dataframe(df_show, use_container_width=True)
    else:
        st.info("Ejecuta `sanity_check_ev.py` para generar el ranking precomputado.")


# ── Footer ───────────────────────────────────────────────
st.divider()
st.caption(
    "Motor IA · Probabilidades-Mus v2.5 · "
    "[GitHub](https://github.com/Marco-Ezquerra/Probabilidades-Mus)"
)
