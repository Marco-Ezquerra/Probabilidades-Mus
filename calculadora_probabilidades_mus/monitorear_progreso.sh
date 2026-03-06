#!/bin/bash
# Script para monitorear progreso de generación de políticas y simulador

echo "======================================================================"
echo "MONITOREO DE PROGRESO - FASE 2 (10M ITERACIONES)"
echo "======================================================================"
echo ""

# Verificar proceso de políticas
if pgrep -f "generar_politicas_rollout.py" > /dev/null; then
    echo "✅ Generador de políticas: CORRIENDO"
    echo ""
    echo "📊 Últimas líneas del log:"
    tail -20 generacion_politicas_10M.log
    echo ""
    echo "📈 Para seguir en tiempo real: tail -f generacion_politicas_10M.log"
else
    echo "⏹️  Generador de políticas: NO CORRIENDO"
    
    # Ver si ya terminó
    if grep -q "Archivo guardado" generacion_politicas_10M.log 2>/dev/null; then
        echo "✅ COMPLETADO!"
        echo ""
        echo "📊 Resumen final:"
        tail -30 generacion_politicas_10M.log | grep -A 20 "RESUMEN"
        
        # Verificar archivo generado
        if [ -f "politicas_optimas_fase2.csv" ]; then
            lineas=$(wc -l < politicas_optimas_fase2.csv)
            tamano=$(du -h politicas_optimas_fase2.csv | cut -f1)
            echo ""
            echo "📁 politicas_optimas_fase2.csv: $lineas líneas, $tamano"
        fi
    fi
fi

echo ""
echo "======================================================================"

# Verificar proceso de simulador
if pgrep -f "simulador_fase2.py" > /dev/null; then
    echo "✅ Simulador Fase 2: CORRIENDO"
    echo ""
    echo "📊 Últimas líneas del log:"
    tail -20 simulacion_fase2_10M.log
    echo ""
    echo "📈 Para seguir en tiempo real: tail -f simulacion_fase2_10M.log"
else
    echo "⏹️  Simulador Fase 2: NO CORRIENDO"
    
    # Ver si ya terminó
    if [ -f "simulacion_fase2_10M.log" ] && grep -q "Archivo guardado" simulacion_fase2_10M.log 2>/dev/null; then
        echo "✅ COMPLETADO!"
        echo ""
        echo "📊 Resumen final:"
        tail -30 simulacion_fase2_10M.log | grep -A 20 "RESUMEN"
    fi
fi

echo ""
echo "======================================================================"
echo "Para ejecutar este script: bash monitorear_progreso.sh"
echo "======================================================================"
