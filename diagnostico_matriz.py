import json

m = json.load(open('config/matriz_calidad.json'))

print("=== Etiqueta de categoría vs. suma real de sus ítems ===")
total_general = 0
hay_descuadre = False
for cat in m['categorias']:
    etiqueta = cat['peso_categoria']*100
    suma_items = sum(it['peso'] for it in cat['items'])*100
    total_general += suma_items
    if abs(etiqueta - suma_items) > 0.01:
        hay_descuadre = True
        print(f"❌ DESCUADRADO: {cat['nombre']}")
        print(f"   Etiqueta de la categoría: {etiqueta:.2f}%")
        print(f"   Suma real de sus ítems:   {suma_items:.2f}%")
        print(f"   Diferencia: {suma_items - etiqueta:+.2f}%")
        print("   Ítems de esta categoría:")
        for it in cat['items']:
            print(f"     {it['nombre']}: {it['peso']*100:.2f}%")
        print()

if not hay_descuadre:
    print("✅ Todas las categorías cuadran con sus ítems.")
    print(f"   El descuadre del {total_general:.2f}% viene de otra parte (redondeo acumulado entre categorías).")

print()
print(f"TOTAL GENERAL (todos los ítems, todas las categorías): {total_general:.2f}%")
