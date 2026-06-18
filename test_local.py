import os
from dotenv import load_dotenv
from client import MercadoPublicoClient
from models import TenderAPIResponse

load_dotenv()
ticket = os.getenv("MERCADO_PUBLICO_API_TICKET")
print(f"Ticket cargado: {'SI' if ticket else 'NO'} (len={len(ticket) if ticket else 0})")

client = MercadoPublicoClient(ticket)
print("Consultando API de Mercado Publico...")
raw = client.fetch_tenders()
print(f"Claves de respuesta: {list(raw.keys())}")
print(f"Cantidad reportada: {raw.get('Cantidad')}")

data = TenderAPIResponse(**raw)
print(f"Validacion Pydantic OK -> Cantidad={data.Cantidad}, Listado={len(data.Listado)}")
for t in data.Listado[:5]:
    print(f"  - {t.CodigoExterno} | tipo={t.tipo_licitacion} | estado={t.CodigoEstado} | {t.Nombre[:50]}")
