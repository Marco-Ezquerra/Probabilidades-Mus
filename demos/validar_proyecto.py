#!/usr/bin/env python3
"""
Script de Validación del Proyecto - Sistema de Análisis de Mus
Verifica que todos los componentes estén presentes y funcionales.
"""

import os
import sys
from pathlib import Path

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    """Imprime un encabezado destacado."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    """Imprime mensaje de éxito."""
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    """Imprime mensaje de error."""
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    """Imprime mensaje de advertencia."""
    print(f"{YELLOW}⚠{RESET} {text}")

def check_file_exists(filepath, description):
    """Verifica que un archivo exista."""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print_success(f"{description} [{size:,} bytes]")
        return True
    else:
        print_error(f"{description} - NO ENCONTRADO")
        return False

def check_module_import(module_path, module_name):
    """Intenta importar un módulo."""
    try:
        sys.path.insert(0, str(Path(module_path).parent))
        __import__(module_name)
        print_success(f"Importación de {module_name}.py")
        return True
    except Exception as e:
        print_error(f"Error importando {module_name}: {e}")
        return False

def count_lines(filepath):
    """Cuenta líneas en un archivo."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def validate_csv_file(filepath, expected_min_lines):
    """Valida un archivo CSV."""
    if not os.path.exists(filepath):
        print_error(f"CSV {Path(filepath).name} no encontrado")
        return False
    
    lines = count_lines(filepath)
    if lines >= expected_min_lines:
        print_success(f"CSV {Path(filepath).name} ({lines} líneas)")
        return True
    else:
        print_error(f"CSV {Path(filepath).name} tiene solo {lines} líneas (esperadas ≥{expected_min_lines})")
        return False

def main():
    """Función principal de validación."""
    
    print_header("VALIDACIÓN DEL PROYECTO - SISTEMA DE ANÁLISIS DE MUS")
    
    base_path = Path(__file__).parent
    calc_path = base_path / "calculadora_probabilidades_mus"
    
    results = {
        'archivos': 0,
        'errores': 0,
        'warnings': 0
    }
    
    # ========================================================================
    # 1. DOCUMENTACIÓN
    # ========================================================================
    print_header("1. DOCUMENTACIÓN")
    
    docs = [
        ("README.md", "README principal"),
        ("RESUMEN_PROYECTO.md", "Resumen ejecutivo"),
        ("MOTOR_DECISION.md", "Docs motor IA"),
        ("SIMULADOR_DINAMICO.md", "Docs simulador dinámico"),
        ("ARQUITECTURA_FLUJOS.md", "Arquitectura y flujos"),
        ("INDICE_PROYECTO.md", "Índice del proyecto"),
        ("requirements.txt", "Dependencias")
    ]
    
    for filename, desc in docs:
        if check_file_exists(base_path / filename, desc):
            results['archivos'] += 1
        else:
            results['errores'] += 1
    
    # ========================================================================
    # 2. CÓDIGO FUENTE PRINCIPAL
    # ========================================================================
    print_header("2. CÓDIGO FUENTE PRINCIPAL")
    
    code_files = [
        ("calculadoramus.py", "Motor Monte Carlo estático"),
        ("simular_dinamico.py", "Simulador dinámico"),
        ("motor_decision.py", "Motor de decisión IA"),
        ("ordenartabla.py", "Utilidad ordenación")
    ]
    
    for filename, desc in code_files:
        filepath = calc_path / filename
        if check_file_exists(filepath, desc):
            lines = count_lines(filepath)
            print(f"  └─ {lines} líneas de código")
            results['archivos'] += 1
        else:
            results['errores'] += 1
    
    # ========================================================================
    # 3. SCRIPTS DE TEST
    # ========================================================================
    print_header("3. SCRIPTS DE TEST")
    
    test_files = [
        ("test_simulador_dinamico.py", "Tests simulador"),
        ("test_motor_decision.py", "Tests motor IA"),
        ("test_baraja.py", "Tests baraja")
    ]
    
    for filename, desc in test_files:
        filepath = base_path / filename
        if check_file_exists(filepath, desc):
            results['archivos'] += 1
        else:
            results['errores'] += 1
    
    # ========================================================================
    # 4. DEMO
    # ========================================================================
    print_header("4. DEMO INTERACTIVA")
    
    if check_file_exists(base_path / "demo_interactiva.py", "Script de demo"):
        results['archivos'] += 1
    else:
        results['errores'] += 1
    
    # ========================================================================
    # 5. DATOS GENERADOS
    # ========================================================================
    print_header("5. DATOS GENERADOS")
    
    # CSVs de estadísticas
    csv_files = [
        ("resultados_4reyes.csv", 716, "Estadísticas 4 reyes"),
        ("resultados_8reyes.csv", 246, "Estadísticas 8 reyes")
    ]
    
    for filename, expected_lines, desc in csv_files:
        filepath = calc_path / filename
        if validate_csv_file(filepath, expected_lines):
            results['archivos'] += 1
        else:
            results['errores'] += 1
    
    # TXTs de estadísticas
    txt_files = [
        ("resultados_4reyes.txt", "Formato legible 4 reyes"),
        ("resultados_8reyes.txt", "Formato legible 8 reyes")
    ]
    
    for filename, desc in txt_files:
        filepath = calc_path / filename
        if check_file_exists(filepath, desc):
            results['archivos'] += 1
        else:
            results['warnings'] += 1
            print_warning(f"{desc} no crítico, se puede regenerar")
    
    # Caché de calibración
    cache_file = calc_path / "calibracion_mu.json"
    if os.path.exists(cache_file):
        print_success("Caché de calibración (calibracion_mu.json)")
        results['archivos'] += 1
    else:
        print_warning("Caché de calibración no existe (se generará automáticamente)")
        results['warnings'] += 1
    
    # ========================================================================
    # 6. IMPORTACIONES DE MÓDULOS
    # ========================================================================
    print_header("6. VALIDACIÓN DE MÓDULOS")
    
    modules = [
        (calc_path / "calculadoramus.py", "calculadoramus"),
        (calc_path / "simular_dinamico.py", "simular_dinamico"),
        (calc_path / "motor_decision.py", "motor_decision")
    ]
    
    for module_path, module_name in modules:
        if check_module_import(module_path, module_name):
            results['archivos'] += 1
        else:
            results['errores'] += 1
    
    # ========================================================================
    # 7. DEPENDENCIAS
    # ========================================================================
    print_header("7. DEPENDENCIAS")
    
    dependencies = ['pandas', 'numpy']
    
    for dep in dependencies:
        try:
            __import__(dep)
            print_success(f"Paquete {dep} instalado")
        except ImportError:
            print_error(f"Paquete {dep} NO INSTALADO")
            results['errores'] += 1
            print(f"  └─ Instalar con: pip install {dep}")
    
    # ========================================================================
    # 8. RESUMEN FINAL
    # ========================================================================
    print_header("RESUMEN DE VALIDACIÓN")
    
    total = results['archivos'] + results['errores'] + results['warnings']
    
    print(f"\n{GREEN}Archivos validados correctamente:{RESET} {results['archivos']}")
    if results['warnings'] > 0:
        print(f"{YELLOW}Advertencias (no críticas):{RESET}      {results['warnings']}")
    if results['errores'] > 0:
        print(f"{RED}Errores encontrados:{RESET}             {results['errores']}")
    
    print(f"\n{'─' * 70}")
    
    if results['errores'] == 0:
        print(f"\n{GREEN}{'✓ PROYECTO COMPLETO Y FUNCIONAL':^70}{RESET}")
        print(f"{GREEN}{'Todos los componentes están presentes y validados':^70}{RESET}\n")
        
        print("Comandos sugeridos para comenzar:")
        print(f"  {BLUE}python3 demo_interactiva.py{RESET}          - Ver demo completa")
        print(f"  {BLUE}python3 test_motor_decision.py{RESET}       - Ejecutar tests del motor")
        print(f"  {BLUE}python3 test_simulador_dinamico.py{RESET}   - Ejecutar tests del simulador")
        
        return 0
    else:
        print(f"\n{RED}{'⚠ PROYECTO INCOMPLETO':^70}{RESET}")
        print(f"{RED}{'Se encontraron errores que deben ser corregidos':^70}{RESET}\n")
        
        if results['errores'] > 0:
            print("Revisa los errores marcados arriba y:")
            print("  1. Verifica que todos los archivos existen")
            print("  2. Instala dependencias: pip install -r requirements.txt")
            print("  3. Genera estadísticas: python3 calculadoramus.py")
        
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠ Validación interrumpida por el usuario{RESET}\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}✗ Error inesperado durante la validación: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
