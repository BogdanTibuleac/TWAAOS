from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Gestiune inventar", version="1.0.0")


class Produs(BaseModel):
    """Model de date pentru un produs din inventar."""

    id: int
    nume: str
    pret: float
    stoc: int = 0


inventar: list[Produs] = []


@app.get("/")
def radacina():
    """Endpoint de verificare a stării serviciului."""
    return {"status": "activ"}


@app.get("/produse")
def obtine_toate_produsele(stoc_minim: int | None = None):
    """
    Returnează toate produsele din inventar.
    Dacă este furnizat stoc_minim, returnează
    doar produsele cu stoc mai mic decât valoarea dată.
    """
    if stoc_minim is None:
        return inventar

    produse_filtrate = [
        produs for produs in inventar if produs.stoc < stoc_minim
    ]
    return produse_filtrate


@app.get("/produse/{produs_id}")
def obtine_produs(produs_id: int):
    """Returnează produsul care corespunde ID-ului primit."""
    for produs in inventar:
        if produs.id == produs_id:
            return produs

    raise HTTPException(
        status_code=404,
        detail=f"Produsul cu ID-ul {produs_id} nu a fost găsit.",
    )


@app.post("/produse", status_code=201)
def adauga_produs(produs: Produs):
    """Adaugă un produs nou în inventar."""
    for produs_existent in inventar:
        if produs_existent.id == produs.id:
            raise HTTPException(
                status_code=400,
                detail=f"Există deja un produs cu ID-ul {produs.id}.",
            )

    inventar.append(produs)
    return produs


@app.put("/produse/{produs_id}")
def actualizeaza_produs(produs_id: int, produs_actualizat: Produs):
    """
    Înlocuiește complet produsul cu ID-ul primit.
    ID-ul din URL trebuie să fie același cu ID-ul din corpul cererii.
    """
    if produs_id != produs_actualizat.id:
        raise HTTPException(
            status_code=400,
            detail="ID-ul din URL trebuie să coincidă cu ID-ul din cerere.",
        )

    for index, produs in enumerate(inventar):
        if produs.id == produs_id:
            inventar[index] = produs_actualizat
            return produs_actualizat

    raise HTTPException(
        status_code=404,
        detail=f"Produsul cu ID-ul {produs_id} nu a fost găsit.",
    )


@app.delete("/produse/{produs_id}")
def sterge_produs(produs_id: int):
    """Șterge produsul cu ID-ul primit și returnează produsul șters."""
    for index, produs in enumerate(inventar):
        if produs.id == produs_id:
            produs_sters = inventar.pop(index)
            return produs_sters

    raise HTTPException(
        status_code=404,
        detail=f"Produsul cu ID-ul {produs_id} nu a fost găsit.",
    )
