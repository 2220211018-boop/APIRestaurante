"""Valida los manifiestos de Kubernetes sin necesidad de un clúster.

Comprueba: YAML válido, campos obligatorios, que cada Service apunte a un Deployment
existente y que los Secrets referenciados existan (o sean los de las llaves RSA,
que el pipeline crea en el despliegue).

Uso:  python scripts/validar_k8s.py
"""
import sys
from pathlib import Path

import yaml

CARPETA = Path(__file__).resolve().parents[1] / "k8s"
SECRETOS_EXTERNOS = {"rsa-private-key", "rsa-public-key"}  # los crea el job de despliegue

errores, docs = [], []
for archivo in sorted(CARPETA.glob("*.yaml")):
    try:
        for d in yaml.safe_load_all(archivo.read_text(encoding="utf-8")):
            if d:
                docs.append((archivo.name, d))
    except yaml.YAMLError as e:
        errores.append(f"{archivo.name}: YAML inválido ({e})")

for nombre, d in docs:
    for campo in ("apiVersion", "kind", "metadata"):
        if campo not in d:
            errores.append(f"{nombre}: falta '{campo}'")
    if "name" not in d.get("metadata", {}):
        errores.append(f"{nombre}: falta metadata.name")

secretos = {d["metadata"]["name"] for _, d in docs if d.get("kind") == "Secret"} | SECRETOS_EXTERNOS

etiquetas = []
for nombre, d in docs:
    if d.get("kind") != "Deployment":
        continue
    plantilla = d["spec"]["template"]
    etiquetas.append(plantilla["metadata"]["labels"])
    for c in plantilla["spec"]["containers"]:
        if not c.get("image"):
            errores.append(f"{nombre}: contenedor '{c.get('name')}' sin imagen")
        for e in c.get("env", []):
            ref = e.get("valueFrom", {}).get("secretKeyRef")
            if ref and ref["name"] not in secretos:
                errores.append(f"{nombre}: secreto '{ref['name']}' no existe")
    for v in plantilla["spec"].get("volumes", []):
        ref = v.get("secret", {}).get("secretName")
        if ref and ref not in secretos:
            errores.append(f"{nombre}: volumen con secreto '{ref}' que no existe")

for nombre, d in docs:
    if d.get("kind") == "Service":
        sel = d["spec"]["selector"]
        if not any(all(e.get(k) == v for k, v in sel.items()) for e in etiquetas):
            errores.append(f"{nombre}: el Service '{d['metadata']['name']}' no apunta a ningún Deployment")

tipos = {}
for _, d in docs:
    tipos[d["kind"]] = tipos.get(d["kind"], 0) + 1
print("Objetos encontrados:", ", ".join(f"{k}={v}" for k, v in sorted(tipos.items())))

if errores:
    print("\nERRORES:")
    for e in errores:
        print("  -", e)
    sys.exit(1)
print("Manifiestos de Kubernetes OK")
