"""Operación registrada: diseño completo de muros RNE E.060.

Registro: ("diseno", "muro")
Entradas (data):
  - nombre, hm, lm, t, fc, fy, fyt, Pu, Vu, Mu  (obligatorios)
  - delta_u, c, Mn_manual, boundary_method, joint_Av, joint_mu (opcionales)
  Unidades internas: cm, kg, kg/cm², kg·cm
"""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.core.utils import to_float
from axis.muros.models import WallGeometry, WallMaterials, WallLoads, StoryData
from axis.muros.designer import design_wall, design_wall_multi_story


@register("diseno", "muro")
def diseno_muro(data: dict) -> dict:
    """Ejecuta el diseño completo de un muro y devuelve dict serializable."""
    required = ("nombre", "hm", "lm", "t", "fc", "fy", "fyt", "Pu", "Vu", "Mu")
    for key in required:
        if key not in data:
            raise InvalidInput(f"Falta el parámetro '{key}'.")

    nombre = str(data["nombre"])
    hm = to_float(data["hm"])
    lm = to_float(data["lm"])
    t = to_float(data["t"])
    fc = to_float(data["fc"])
    fy = to_float(data["fy"])
    fyt = to_float(data["fyt"])
    Pu = to_float(data["Pu"])
    Vu = to_float(data["Vu"])
    Mu = to_float(data["Mu"])

    delta_u = to_float(data.get("delta_u"), default=None) if "delta_u" in data else None
    c_val = to_float(data.get("c"), default=None) if "c" in data else None
    Mn_man = to_float(data.get("Mn_manual"), default=None) if "Mn_manual" in data else None
    b_method = data.get("boundary_method")
    j_Av = to_float(data.get("joint_Av"), default=None) if "joint_Av" in data else None
    j_mu = to_float(data.get("joint_mu"), default=1.0)

    if hm <= 0 or lm <= 0 or t <= 0:
        raise InvalidInput("hm, lm, t deben ser positivos.")
    if fc <= 0 or fy <= 0 or fyt <= 0:
        raise InvalidInput("fc, fy, fyt deben ser positivos.")

    geo = WallGeometry(hm=hm, lm=lm, t=t)
    mat = WallMaterials(fc=fc, fy=fy, fyt=fyt)
    loads = WallLoads(Pu=Pu, Vu=Vu, Mu=Mu, delta_u=delta_u, c=c_val, Mn_manual=Mn_man)

    result = design_wall(
        nombre=nombre,
        geo=geo,
        mat=mat,
        loads=loads,
        boundary_method=b_method,
        joint_Av=j_Av,
        joint_mu=j_mu,
        vu_for_min_steel=abs(Vu),
    )

    return _serialize(result)


@register("diseno", "muro_multi")
def diseno_muro_multi(data: dict) -> dict:
    """Ejecuta el diseno multipiso completo de un muro."""
    for key in ("nombre", "lm", "t", "fc", "fy", "fyt", "pisos"):
        if key not in data:
            raise InvalidInput(f"Falta el parametro '{key}'.")

    nombre = str(data["nombre"])
    lm = to_float(data["lm"])
    t = to_float(data["t"])
    fc = to_float(data["fc"])
    fy = to_float(data["fy"])
    fyt = to_float(data["fyt"])

    mat = WallMaterials(fc=fc, fy=fy, fyt=fyt)

    pisos_raw = data["pisos"]
    if not pisos_raw:
        raise InvalidInput("Debe haber al menos un piso.")

    stories = []
    for p in pisos_raw:
        mn = to_float(p.get("Mn_manual"), default=None) if p.get("Mn_manual") else None
        c_v = to_float(p.get("c"), default=None) if p.get("c") else None
        vu_cap = to_float(p["Vu_cap"]) if "Vu_cap" in p else None
        vua_sx = to_float(p["Vua_sx_max_kg"]) if p.get("Vua_sx_max_kg") not in (None, "") else None
        nu_j = to_float(p["Nu_junta_kg"]) if p.get("Nu_junta_kg") not in (None, "") else None
        pcm_j = to_float(p["Pcm_junta_tn"]) if p.get("Pcm_junta_tn") not in (None, "") else None
        stories.append(StoryData(
            piso=int(p["piso"]),
            hm=to_float(p["hm"]),
            Pu=to_float(p["Pu"]),
            Vu=to_float(p["Vu"]),
            Mu=to_float(p["Mu"]),
            Mn_manual=mn, c=c_v,
            Vu_cap_demand=vu_cap,
            Vua_sx_max_kg=vua_sx,
            Nu_junta_kg=nu_j,
            Pcm_junta_tn=pcm_j,
        ))

    delta_u = to_float(data.get("delta_u"), default=None) if data.get("delta_u") else None
    b_method = data.get("boundary_method")
    j_Av = to_float(data.get("joint_Av"), default=None) if data.get("joint_Av") else None
    j_mu = to_float(data.get("joint_mu"), default=1.0)
    k = to_float(data.get("k_buckling"), default=1.0)
    R = to_float(data.get("R"), default=None) if "R" in data else None

    result = design_wall_multi_story(
        nombre=nombre, lm=lm, t=t, mat=mat,
        stories=stories, boundary_method=b_method,
        delta_u=delta_u, joint_Av=j_Av, joint_mu=j_mu,
        k_buckling=k, R=R,
    )

    return _serialize_multi(result, R=R)


def _serialize_multi(r, R: float | None = None) -> dict:
    """Convierte MultiStoryResult a dict."""
    pisos = []
    for sr in r.stories:
        s = _serialize(sr.result)
        s["piso"] = sr.piso
        s["borde_requiere_piso"] = sr.requires_boundary
        s["largo_borde"] = sr.largo_borde
        if sr.vua_sx_max_kg is not None:
            s["Vua_sx_max_kg"] = round(sr.vua_sx_max_kg, 2)
        if sr.nu_junta_kg is not None:
            s["Nu_junta_kg"] = round(sr.nu_junta_kg, 2)
        if sr.pcm_junta_tn is not None:
            s["Pcm_junta_tn"] = round(sr.pcm_junta_tn, 4)
        pisos.append(s)

    bg = r.boundary_global
    out = {
        "nombre": r.nombre,
        "lm": r.lm, "t": r.t, "H_total": r.H_total,
        "pisos": pisos,
        "borde_global_requiere": bg.requires if bg else None,
        "borde_global_metodo": bg.method if bg else None,
        "borde_global_detalle": bg.details if bg else None,
        "delta_u": r.delta_u,
        "k_buckling": r.k_buckling,
        "phi_Pn_compresion": round(r.compression_phi_Pn, 2) if r.compression_phi_Pn else None,
        "diseno_ok": r.ok,
    }
    if R is not None:
        out["R"] = R
    return out


def _serialize(r) -> dict:
    """Convierte WallDesignResult a dict plano para almacenamiento/tabla."""
    f = r.flexure
    s = r.shear
    rf = r.reinforcement
    b = r.boundary
    j = r.joint

    out = {
        "nombre": r.nombre,
        "geometry_ok": r.geometry_ok,
        "thickness_msg": r.thickness_msg,
        # Flexión
        "Mn": round(f.Mn, 2),
        "Mua": round(f.Mua, 2),
        "phi_Mn": round(f.Mn * 0.9, 2),
        "flexion_ok": f.ok,
        "Mcr": round(f.Mcr, 2) if f.Mcr is not None else None,
        "cracking_ok": f.cracking_ok,
        # Corte
        "Vu_orig": round(s.Vu_orig, 2),
        "Vu_cap": round(s.Vu_cap, 2),
        "Vc": round(s.Vc, 2),
        "Vs": round(s.Vs, 2),
        "Vn": round(s.Vn, 2),
        "phi_Vn": round(s.phi_Vn, 2),
        "corte_ok": s.ok,
        "vn_limit_ok": s.vn_limit_ok,
        # Refuerzo
        "rho_h": round(rf.rho_h, 6),
        "rho_v": round(rf.rho_v, 6),
        # Borde
        "borde_requiere": b.requires if b else None,
        "borde_metodo": b.method if b else None,
        "borde_detalle": str(b.details) if b else None,
        # Juntas
        "junta_ok": j.ok if j else None,
        "Vn_joint": round(j.Vn_joint, 2) if j else None,
        "phi_Vn_joint": round(j.phi_Vn_joint, 2) if j else None,
        "Av_joint": round(j.Av, 2) if j else None,
        "mu_joint": round(j.mu, 2) if j else None,
        # Global
        "diseno_ok": r.ok,
    }
    return out
