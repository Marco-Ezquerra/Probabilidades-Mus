"""
Test rápido de integración para verificar que el tracking de descartes funciona.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "calculadora_probabilidades_mus"))
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from generar_politicas_rollout import QTableDescarte, simular_rollout_mascara_rapida, _MASCARAS
from descarte_heuristico import descarte_heuristico_base
from calculadoramus import inicializar_baraja
import random

def test_tracking_descartes():
    """Test básico para verificar que el tracking de descartes funciona."""
    print("=" * 70)
    print("TEST DE TRACKING DE DESCARTES")
    print("=" * 70)
    
    # Inicializar
    baraja = inicializar_baraja(True)
    random.shuffle(baraja)
    
    # Crear manos de prueba
    manos = {}
    for pos in [1, 2, 3, 4]:
        mano = baraja[:4]
        manos[pos] = sorted(mano, reverse=True)
        baraja = baraja[4:]
    
    mazo_restante = baraja
    
    print("\n🎴 Manos generadas:")
    for pos, mano in manos.items():
        print(f"  Posición {pos}: {mano}")
    
    # Preparar descartes heurísticos para otros jugadores
    posicion_objetivo = 1
    otros_manos_rest = {}
    for pos in [2, 3, 4]:
        mascara_h = descarte_heuristico_base(manos[pos], pos)
        otros_manos_rest[pos] = [manos[pos][i] for i in range(4) if i not in mascara_h]
        print(f"  Pos {pos} descarta máscara {mascara_h} ({len(mascara_h)} cartas)")
    
    # Simular rollout con máscara 0 (descartar 1 carta)
    mascara_idx = 0
    print(f"\n🎯 Jugador objetivo (Pos {posicion_objetivo}) prueba máscara {mascara_idx}: {_MASCARAS[mascara_idx]}")
    
    reward, info_descartes = simular_rollout_mascara_rapida(
        manos[posicion_objetivo], posicion_objetivo, mascara_idx,
        mazo_restante, otros_manos_rest
    )
    
    print(f"\n📊 Resultado del rollout:")
    print(f"  Reward (diferencial): {reward:+.1f} puntos")
    print(f"  Info de descartes: {info_descartes}")
    
    # Verificar que info_descartes está bien formado
    assert isinstance(info_descartes, dict), "info_descartes debe ser un dict"
    assert len(info_descartes) == 4, "info_descartes debe tener 4 posiciones"
    for pos in [1, 2, 3, 4]:
        assert pos in info_descartes, f"Posición {pos} debe estar en info_descartes"
        assert 1 <= info_descartes[pos] <= 4, f"Pos {pos}: descartes debe estar entre 1 y 4"
    
    print("\n✅ Info de descartes tiene el formato correcto")
    
    # Test de QTableDescarte con info de descartes
    print("\n" + "=" * 70)
    print("TEST DE QTABLE CON INFO DE DESCARTES")
    print("=" * 70)
    
    q_table = QTableDescarte()
    
    # Simular varios rollouts y actualizar Q-Table
    print("\n🔄 Simulando 5 rollouts con diferentes máscaras...")
    for mascara_idx in range(5):
        reward, info_descartes = simular_rollout_mascara_rapida(
            manos[1], 1, mascara_idx, mazo_restante, otros_manos_rest
        )
        q_table.actualizar(manos[1], 1, mascara_idx, reward, info_descartes)
        print(f"  Máscara {mascara_idx}: reward={reward:+.1f}, descartes={info_descartes}")
    
    # Exportar a CSV temporal
    csv_test_path = Path("/tmp/test_politicas_descartes.csv")
    n_entries = q_table.exportar_csv(csv_test_path)
    
    print(f"\n📝 CSV exportado: {n_entries} entradas guardadas")
    print(f"   Archivo: {csv_test_path}")
    
    # Leer y verificar CSV
    df = pd.read_csv(csv_test_path)
    print(f"\n📊 Estructura del CSV:")
    print(f"   Columnas: {list(df.columns)}")
    print(f"   Primeras filas:\n{df.head()}")
    
    # Verificar que las columnas de descartes existen
    columnas_esperadas = ['mano', 'posicion', 'mascara_idx', 'reward_promedio', 'n_visitas',
                          'n_descarte_j1', 'n_descarte_j2', 'n_descarte_j3', 'n_descarte_j4']
    for col in columnas_esperadas:
        assert col in df.columns, f"Columna {col} debe estar en el CSV"
    
    print("\n✅ CSV contiene todas las columnas esperadas")
    
    # Verificar que los valores de descartes son razonables
    for col in ['n_descarte_j1', 'n_descarte_j2', 'n_descarte_j3', 'n_descarte_j4']:
        valores = df[col].values
        assert all(1 <= v <= 4 for v in valores), f"Valores de {col} deben estar entre 1 y 4"
    
    print("✅ Valores de descartes son razonables (entre 1 y 4 cartas)")
    
    print("\n" + "=" * 70)
    print("🎉 TODOS LOS TESTS DE INTEGRACIÓN PASARON")
    print("=" * 70)

if __name__ == "__main__":
    test_tracking_descartes()
