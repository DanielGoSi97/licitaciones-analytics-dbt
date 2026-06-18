from typing import List, Optional
from pydantic import BaseModel, Field

# Mapeos basados en la documentación oficial de Mercado Público
# https://api.mercadopublico.cl/modules/Licitacion.aspx
TIPO_LICITACION_MAP = {
    "L1": "Licitación Pública Menor a 100 UTM",
    "LE": "Licitación Pública Entre 100 y 1000 UTM",
    "LP": "Licitación Pública Mayor 1000 UTM",
    "LS": "Licitación Pública Servicios personales especializados",
    "A1": "Licitación Privada por Licitación Pública anterior sin oferentes",
    "B1": "Licitación Privada por otras causales, excluidas de la ley de Compras",
    "J1": "Licitación Privada por Servicios de Naturaleza Confidencial",
    "F1": "Licitación Privada por Convenios con Personas Jurídicas Extranjeras fuera del Territorio Nacional",
    "E1": "Licitación Privada por Remanente de Contrato anterior",
    "CO": "Licitación Privada entre 100 y 1000 UTM",
    "B2": "Licitación Privada Mayor a 1000 UTM",
    "A2": "Trato Directo por Producto de Licitación Privada anterior sin oferentes o desierta",
    "D1": "Trato Directo por Proveedor Único",
    "E2": "Licitación Privada Menor a 100 UTM",
    "C2": "Trato Directo (Cotización)",
    "C1": "Compra Directa (Orden de compra)",
    "F2": "Trato Directo (Cotización)",
    "F3": "Compra Directa (Orden de compra)",
    "G2": "Directo (Cotización)",
    "G1": "Compra Directa (Orden de compra)",
    "R1": "Orden de Compra menor a 3 UTM",
    "CA": "Orden de Compra sin Resolución",
    "SE": "Orden de Compra proveniente de adquisición sin emisión automática de OC",
}

# Códigos de estado de las licitaciones
ESTADO_MAP = {
    5: "Publicada",
    6: "Cerrada",
    7: "Desierta",
    8: "Adjudicada",
    18: "Revocada",
    19: "Suspendida",
}

# Clasificación temática heurística por palabras clave en el nombre de la licitación.
# Orden importante: la primera categoría que haga match gana.
CATEGORIAS_TEMATICAS = {
    "Salud y Medicamentos": ["medicamento", "insumo medico", "insumos medicos", "hospital",
                              "clinic", "salud", "farmac", "dental", "odontolog", "cenabast",
                              "quirurg", "laboratorio", "reactivo", "ambulancia"],
    "Construcción y Obras": ["construc", "obra", "edificaci", "pavimento", "asfalto", "remodelac",
                             "reparaci", "mantenci", "infraestructura", "alcantarillado", "techo"],
    "Tecnología e Informática": ["software", "hardware", "computador", "notebook", "servidor",
                                 "informatic", "sistema", "licencia", "ti ", "tecnolog", "red ",
                                 "datacenter", "ciberseg"],
    "Alimentación": ["aliment", "comida", "racion", "abarrote", "frut", "verdura", "carne",
                     "lacteo", "pan ", "casino", "minuta"],
    "Transporte y Vehículos": ["transporte", "vehiculo", "camion", "bus ", "combustible",
                               "neumatic", "flete", "movilizaci", "automov"],
    "Aseo y Mantención": ["aseo", "limpieza", "jardin", "areas verdes", "ornato", "fumigaci",
                          "desratiz", "residuos", "basura"],
    "Mobiliario y Equipamiento": ["mobiliario", "escritorio", "silla", "equipamiento", "electrodom",
                                  "maquinaria", "herramienta"],
    "Servicios Profesionales": ["asesoria", "consultoria", "capacitaci", "estudio", "auditoria",
                                "servicio profesional", "diseño", "honorario"],
    "Educación y Cultura": ["educaci", "escuela", "colegio", "jardin infantil", "biblioteca",
                            "cultural", "deport", "libro", "utiles escolares"],
    "Vestuario y Textil": ["vestuario", "uniforme", "ropa", "textil", "calzado", "zapato"],
    "Seguridad": ["seguridad", "vigilancia", "guardia", "camara", "extintor", "alarma"],
    "Combustibles y Energía": ["energia", "electrico", "gas ", "fotovoltaic", "luminaria", "panel solar"],
}


# Clasificación del tipo de entidad/organismo a partir del nombre del comprador.
# (La API no entrega el ministerio padre directamente; esto aproxima el tipo de ente.)
_REGLAS_ENTIDAD = [
    ("MUNICIPALIDAD", "Municipalidad"),
    ("MUNICIPAL", "Municipalidad"),
    ("SERVICIO DE SALUD", "Servicio de Salud"),
    ("HOSPITAL", "Hospital"),
    ("CESFAM", "Salud primaria"),
    ("CENTRO DE SALUD", "Salud primaria"),
    ("SUBSECRETARIA", "Ministerio (subsecretaría)"),
    ("MINISTERIO", "Ministerio"),
    ("GOBIERNO REGIONAL", "Gobierno Regional"),
    ("GORE", "Gobierno Regional"),
    ("UNIVERSIDAD", "Universidad"),
    ("JUNJI", "JUNJI"),
    ("JUNTA NACIONAL", "Junta Nacional (JUNAEB/JUNJI)"),
    ("CARABINEROS", "Carabineros"),
    ("EJERCITO", "Defensa"),
    ("FUERZA AEREA", "Defensa"),
    ("ARMADA", "Defensa"),
    ("GENDARMERIA", "Gendarmería"),
    ("CORPORACION", "Corporación"),
    ("INSTITUTO", "Instituto"),
    ("DIRECCION", "Dirección / Servicio"),
    ("SERVICIO", "Servicio público"),
]


def clasificar_entidad(nombre_organismo: str) -> str:
    """Aproxima el tipo de entidad (ministerio, municipalidad, salud, etc.)."""
    if not nombre_organismo:
        return "Sin dato"
    n = nombre_organismo.upper()
    for clave, etiqueta in _REGLAS_ENTIDAD:
        if clave in n:
            return etiqueta
    return "Otros organismos"


def categoria_tematica(nombre: str) -> str:
    """Asigna una categoría temática a partir de palabras clave en el nombre."""
    if not nombre:
        return "Sin clasificar"
    texto = nombre.lower()
    for categoria, claves in CATEGORIAS_TEMATICAS.items():
        if any(clave in texto for clave in claves):
            return categoria
    return "Otros / General"


class Tender(BaseModel):
    CodigoExterno: str
    Nombre: Optional[str] = None
    CodigoEstado: Optional[int] = None
    FechaCierre: Optional[str] = None

    @property
    def tipo_licitacion(self) -> str:
        # Extraer el tipo del código, ej: '1004-17-LP26' -> 'LP'
        parts = self.CodigoExterno.split('-')
        if len(parts) >= 3:
            tipo_code = parts[-1][:2]
            return TIPO_LICITACION_MAP.get(tipo_code, "Otro")
        return "Desconocido"

    @property
    def estado(self) -> str:
        return ESTADO_MAP.get(self.CodigoEstado, "Desconocido")

class TenderAPIResponse(BaseModel):
    Cantidad: int
    FechaCreacion: str
    Listado: List[Tender] = Field(default_factory=list)
