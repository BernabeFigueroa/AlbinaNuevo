# Albina Accesorios v1.1.20

- Las ventas fiadas envían siempre el precio de contado, incluso cuando el servidor todavía utiliza una versión anterior de la función de ventas.
- Se evita que los artículos provisorios de una venta fiada se registren con el recargo del 35% correspondiente a tarjeta.
- Se incorpora una corrección segura e idempotente para la venta #799 de Daniela Slame: total y deuda pasan de $440.909 a $403.984.
- La corrección histórica valida todos los importes esperados y se revierte completa si encuentra datos diferentes, sin modificar otras ventas.
