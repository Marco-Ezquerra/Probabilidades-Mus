"""
Genera los gráficos estáticos para el README:
  1. assets/curvas_sigmoide.png  — 3 perfiles de agresividad
  2. assets/heatmap_decision.png — P(Cortar) para manos interesantes (pos 1 vs pos 4)

Uso:
    cd calculadora_probabilidades_mus
    python ../utils/generar_assets.py
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import ast

ROOT = Path(__file__).parent.parent
CALC_DIR = ROOT / "calculadora_probabilidades_mus"
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(CALC_DIR))

from motor_decision import (
    MotorDecisionMus, EstadisticasEstaticas, calcular_ev_total,
    calibrar_umbral_mu, PERFILES
)

# ─────────────────────── Inicialización ───────────────────────
print("Cargando estadísticas…")
stats = EstadisticasEstaticas(modo_8_reyes=True)
print(f"  {len(stats.df)} manos cargadas")

# Pre-computar EV de todas las manos en las 4 posiciones con perfil normal
beta_normal = PERFILES['normal']['beta']
print("Calculando EV de todas las manos (pos 1–4)…")
ev_por_pos = {}   # {posicion: [ev1, ev2, ..., ev330]}
manos_lista = [list(m) for m in stats.df['mano_lista']]

for pos in [1, 2, 3, 4]:
    evs = []
    for mano in manos_lista:
        ev, _ = calcular_ev_total(mano, stats, beta=beta_normal, posicion=pos)
        evs.append(ev)
    ev_por_pos[pos] = np.array(evs)
    print(f"  pos {pos}: min={evs[0]:.3f} max={max(evs):.3f} → {len(evs)} manos")

# ══════════════════════════════════════════════════════════════════════
#  GRÁFICO 1 — CURVAS DE PERFIL SIGMOIDE
# ══════════════════════════════════════════════════════════════════════
print("\nGenerando curvas de perfil sigmoide…")

# Usar EVs de posición 1 como muestra de referencia
evs_ref = ev_por_pos[1]
ev_range = np.linspace(evs_ref.min() - 0.3, evs_ref.max() + 0.3, 400)

fig, ax = plt.subplots(figsize=(10, 6))

colores = {
    'conservador': '#2196F3',   # azul
    'normal':      '#4CAF50',   # verde
    'agresivo':    '#F44336',   # rojo
}
estilos = {'conservador': '--', 'normal': '-', 'agresivo': '-.'}

for perfil, params in PERFILES.items():
    k_base = params['k_base']
    factor_pos1 = 0.75   # FACTOR_K_POS[1]
    k_efec = k_base * factor_pos1
    mu = calibrar_umbral_mu(
        stats,
        percentil=params['percentil_mu'],
        beta=params['beta'],
        silent=True,
    )

    # Curva media (determinista)
    P_media = 1 / (1 + np.exp(-k_efec * (ev_range - mu)))
    ax.plot(ev_range, P_media,
            color=colores[perfil], linestyle=estilos[perfil],
            linewidth=2.5, label=f"{perfil.capitalize()} (k={k_efec:.2f}, μ={mu:.2f})")

    # Banda de incertidumbre: ±1σ en k
    sigma = params['sigma']
    k_lo = max(k_efec - sigma, 0.3)
    k_hi = k_efec + sigma
    P_lo = 1 / (1 + np.exp(-k_lo * (ev_range - mu)))
    P_hi = 1 / (1 + np.exp(-k_hi * (ev_range - mu)))
    ax.fill_between(ev_range, P_lo, P_hi,
                    color=colores[perfil], alpha=0.12)

    # Marcar umbral μ
    ax.axvline(mu, color=colores[perfil], linestyle=':', alpha=0.5, linewidth=1)

# Manos de referencia (etiquetas)
manos_ref = {
    "[1,12,12,12]": (evs_ref.max() * 0.97, "mejor"),
    "[12,12,12,12]": (sorted(evs_ref)[-2], "2ª mejor"),
    "[5,6,7,10]":  (evs_ref.min() * 1.02, "peor"),
}
mano_evs_pos1 = {}
for i, mano in enumerate(manos_lista):
    key = str(sorted(mano))
    mano_evs_pos1[key] = ev_por_pos[1][i]

ref_manos_ev = {
    "[1, 12, 12, 12]": mano_evs_pos1.get(str([1, 12, 12, 12]), 6.29),
    "[12, 12, 12, 12]": mano_evs_pos1.get(str([12, 12, 12, 12]), 6.14),
    "[5, 6, 7, 10]": mano_evs_pos1.get(str([5, 6, 7, 10]), 1.23),
}

for label, ev_val in ref_manos_ev.items():
    ax.axvline(ev_val, color='gray', linestyle=':', alpha=0.35, linewidth=0.8)
    ax.text(ev_val, 0.03, label.replace('[', '').replace(']', ''),
            rotation=90, va='bottom', ha='center', fontsize=7.5, color='gray')

ax.axhline(0.5, color='black', linestyle=':', linewidth=0.7, alpha=0.4)
ax.set_xlabel("EV de la mano (Valor Esperado)", fontsize=12)
ax.set_ylabel("P(Cortar)", fontsize=12)
ax.set_title("Curvas de Decisión Sigmoide — 3 Perfiles de Agresividad\n"
             "(Posición 1 — Mano, baraja 8 reyes)", fontsize=13, fontweight='bold')
ax.set_ylim(-0.02, 1.02)
ax.set_xlim(ev_range[0], ev_range[-1])
ax.legend(fontsize=11, loc='lower right')
ax.grid(True, alpha=0.25)

# Histograma de densidad de EVs (eje secundario)
ax2 = ax.twinx()
ax2.hist(evs_ref, bins=40, color='gray', alpha=0.12, density=True)
ax2.set_ylabel("Densidad de manos", fontsize=9, color='gray')
ax2.tick_params(axis='y', colors='gray')
ax2.set_ylim(0, ax2.get_ylim()[1] * 6)  # Comprimir para que no tape

plt.tight_layout()
out1 = ASSETS_DIR / "curvas_sigmoide.png"
fig.savefig(out1, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ {out1}")

# ══════════════════════════════════════════════════════════════════════
#  GRÁFICO 2 — HEATMAP DE P(CORTAR) CON MANOS INTERESANTES
# ══════════════════════════════════════════════════════════════════════
print("\nGenerando heatmap de decisión…")

# Seleccionar manos "interesantes": cubrir juego, pares y combinaciones
# — Top 5 juego, 5 pares, 5 punto, 5 bottom + manos "narrativas"
from calculadoramus import (
    calcular_valor_juego, clasificar_pares, calcular_valor_punto, convertir_valor_juego
)

# Clasificar todas las manos
filas = []
for i, mano in enumerate(manos_lista):
    vj = calcular_valor_juego(mano)
    tipo_p, vp, vs = clasificar_pares(mano)
    ev1 = ev_por_pos[1][i]
    ev4 = ev_por_pos[4][i]
    filas.append({
        'mano': mano,
        'mano_str': str(sorted(mano)),
        'tiene_juego': vj > 0,
        'valor_juego': vj,
        'rank_juego': convertir_valor_juego(vj) if vj > 0 else 0,
        'tipo_pares': tipo_p,
        'ev_pos1': ev1,
        'ev_pos4': ev4,
    })

df_all = pd.DataFrame(filas).sort_values('ev_pos1', ascending=False).reset_index(drop=True)

# Selección representativa (≈ 50 manos)
MANOS_NARRATIVAS = [
    [1, 12, 12, 12],   # mejor mano posible
    [12, 12, 12, 12],  # duples reyes
    [11, 11, 12, 12],  # duples R+C
    [11, 11, 11, 12],  # medias caballos
    [1, 1, 12, 12],    # medias (A+R)
    [10, 10, 10, 10],  # duples sotas
    [6, 6, 12, 12],    # juego 32 con pares
    [7, 7, 12, 12],    # juego 34 con pares
    [1, 4, 5, 12],     # sin pares con as
    [4, 5, 6, 7],      # peor mano
    [5, 6, 7, 10],     # sin pares, casi peor
    [4, 6, 7, 10],     # sin pares mediocre
    [1, 4, 4, 12],     # pares bajos con as
    [10, 11, 12, 1],   # juego 32 sin más
    [7, 7, 7, 10],     # medias sietes
]

set_narrativas = {str(sorted(m)) for m in MANOS_NARRATIVAS}

# Top 8 EV + bottom 8 EV + 8 con juego + variables
top_idx = df_all.head(8).index.tolist()
bot_idx = df_all.tail(8).index.tolist()
jue_idx = df_all[df_all['tiene_juego']].head(10).index.tolist()
nar_idx = [i for i, r in df_all.iterrows() if r['mano_str'] in set_narrativas]

sel_idx = sorted(set(top_idx + bot_idx + jue_idx + nar_idx))
df_sel = df_all.loc[sel_idx].sort_values('ev_pos1', ascending=True).reset_index(drop=True)

print(f"  {len(df_sel)} manos seleccionadas para el heatmap")

# Calcular P(Cortar) media (determinista, sin ruido) para perfil Normal
mu_normal = {
    pos: calibrar_umbral_mu(stats, percentil=PERFILES['normal']['percentil_mu'],
                             beta=PERFILES['normal']['beta'], silent=True)
    for pos in [1, 4]
}
from params import FACTOR_K_POS
k_normal = PERFILES['normal']['k_base']

def p_cortar_det(ev, pos, mu_dict):
    k = k_normal * FACTOR_K_POS.get(pos, 1.0)
    return 1 / (1 + np.exp(-k * (ev - mu_dict[pos])))

p1 = np.array([p_cortar_det(r['ev_pos1'], 1, mu_normal) for _, r in df_sel.iterrows()])
p4 = np.array([p_cortar_det(r['ev_pos4'], 4, mu_normal) for _, r in df_sel.iterrows()])

# Etiquetas de mano con iconos
def label_mano(row):
    icons = []
    if row['tiene_juego']:
        j = row['valor_juego']
        icons.append(f"J{int(j)}")
    if row['tipo_pares'] == 'duples':
        icons.append("DD")
    elif row['tipo_pares'] == 'medias':
        icons.append("MM")
    elif row['tipo_pares'] == 'pares':
        icons.append("P")
    prefix = "+".join(icons) + " " if icons else ""
    cards = row['mano_str'].replace('[', '').replace(']', '').replace(' ', '')
    return f"{prefix}[{cards}]"

etiquetas = [label_mano(r) for _, r in df_sel.iterrows()]

# Construir matriz 2x(n_manos) para el heatmap
matrix = np.column_stack([p1, p4]).T  # (2, n_manos)

fig, ax = plt.subplots(figsize=(max(16, len(df_sel) * 0.45), 4))

cmap = plt.cm.RdYlGn
im = ax.imshow(matrix, aspect='auto', cmap=cmap, vmin=0, vmax=1)

ax.set_yticks([0, 1])
ax.set_yticklabels(['Pos 1 — Mano', 'Pos 4 — Postre'], fontsize=11)
ax.set_xticks(range(len(etiquetas)))
ax.set_xticklabels(etiquetas, rotation=75, ha='right', fontsize=7.5)

# Anotar valores
for col in range(len(df_sel)):
    for row in range(2):
        val = matrix[row, col]
        color_txt = 'white' if val < 0.25 or val > 0.75 else 'black'
        ax.text(col, row, f"{val:.2f}", ha='center', va='center',
                fontsize=6.5, color=color_txt, fontweight='bold')

plt.colorbar(im, ax=ax, label='P(Cortar)', fraction=0.02, pad=0.02)

ax.set_title(
    "Probabilidad de Cortar — Manos Representativas · Perfil Normal\n"
    "Izquierda → Peor EV → Derecha · "
    "Verde = Cortar con alta prob · Rojo = Dar Mus",
    fontsize=11, fontweight='bold'
)
plt.tight_layout()
out2 = ASSETS_DIR / "heatmap_decision.png"
fig.savefig(out2, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ {out2}")

print("\n✅ Assets generados correctamente:")
print(f"   {out1}")
print(f"   {out2}")
