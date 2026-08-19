"""Rutas del editor de matriz de calidad — ver y ajustar los pesos de cada
ítem desde la web, sin tocar config/matriz_calidad.json a mano."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.typing import ResponseReturnValue

from matriz_editor import cargar_matriz_editable, guardar_pesos, suma_total_pesos, ITEMS_PROTEGIDOS

matriz_bp = Blueprint("matriz", __name__)


@matriz_bp.route("/matriz")
def matriz_editor_ver() -> ResponseReturnValue:
    """Muestra la matriz de calidad actual con sus pesos, para poder editarlos desde la web."""
    matriz = cargar_matriz_editable()
    total = suma_total_pesos(matriz)
    return render_template(
        "matriz_editor.html", matriz=matriz, total=total,
        items_protegidos=ITEMS_PROTEGIDOS, activo="matriz",
    )


@matriz_bp.route("/matriz/guardar", methods=["POST"])
def matriz_editor_guardar() -> ResponseReturnValue:
    """Guarda los pesos editados y avisa si la suma no da exactamente 100%."""
    matriz = cargar_matriz_editable()
    pesos_por_item = {}
    pesos_por_categoria = {}

    for cat in matriz["categorias"]:
        valor_cat = request.form.get(f"cat__{cat['nombre']}")
        if valor_cat is not None:
            try:
                pesos_por_categoria[cat["nombre"]] = float(valor_cat) / 100
            except ValueError:
                pass
        for it in cat["items"]:
            valor_item = request.form.get(f"item__{it['id']}")
            if valor_item is not None:
                try:
                    pesos_por_item[it["id"]] = float(valor_item) / 100
                except ValueError:
                    pass

    items_bloqueados = [
        item_id for item_id, minimo in ITEMS_PROTEGIDOS.items()
        if item_id in pesos_por_item and pesos_por_item[item_id] < minimo
    ]

    guardar_pesos(pesos_por_item, pesos_por_categoria)
    nuevo_total = suma_total_pesos()

    if items_bloqueados:
        flash(f"🔒 {', '.join(items_bloqueados)} es un ítem protegido — se dejó en su peso mínimo, no se puede apagar ni quitar.")

    if abs(nuevo_total - 1.0) > 0.001:
        flash(f"⚠️ Guardado, pero los pesos suman {nuevo_total*100:.1f}% en vez de 100% — revísalos.")
    else:
        flash("✅ Matriz actualizada correctamente (100%).")

    return redirect(url_for("matriz.matriz_editor_ver"))
