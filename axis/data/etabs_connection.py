"""
Módulo para la conexión con ETABS mediante COM.

Requiere ETABS abierto con un modelo cargado y la librería comtypes instalada.
"""

from __future__ import annotations

from typing import Optional, Tuple, Any

try:
    import comtypes
    import comtypes.client
    import pythoncom
    ETABS_AVAILABLE = True
except ImportError:
    ETABS_AVAILABLE = False


def conectar_con_etabs() -> Optional[Tuple[Any, Any, Any]]:
    """
    Conecta con ETABS mediante COM.

    Returns:
        Tupla (SapModel, myETABSObject, helper) o None si falla.
    """
    if not ETABS_AVAILABLE:
        print("⚠ Error: comtypes no está disponible. Instale con: pip install comtypes")
        return None

    try:
        try:
            pythoncom.CoInitialize()
        except pythoncom.com_error:
            pass

        helper = comtypes.client.CreateObject("ETABSv1.Helper")
        try:
            import comtypes.gen.ETABSv1 as etabs  # noqa: F401
        except Exception:
            comtypes.client.GetModule("ETABSv1.tlb")
            import comtypes.gen.ETABSv1 as etabs
        helper = helper.QueryInterface(etabs.cHelper)

        try:
            myETABSObject = helper.GetObject("CSI.ETABS.API.ETABSObject")
        except (OSError, comtypes.COMError) as e:
            print(f"⚠ Error al obtener objeto ETABS: {e}")
            print("   Asegúrese de que ETABS esté abierto y con un modelo cargado.")
            return None

        SapModel = myETABSObject.SapModel
        Tn_m_C = 12
        SapModel.SetPresentUnits(Tn_m_C)

        return SapModel, myETABSObject, helper

    except Exception as e:
        print(f"⚠ Error inesperado en conexión: {e}")
        import traceback
        traceback.print_exc()
        return None


def verificar_etabs_disponible() -> bool:
    """
    Verifica si ETABS está disponible (comtypes instalado).

    Returns:
        True si ETABS está disponible, False en caso contrario.
    """
    return ETABS_AVAILABLE
