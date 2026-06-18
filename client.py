import requests
from tenacity import retry, stop_after_attempt, wait_exponential

class MercadoPublicoClient:
    BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

    def __init__(self, ticket: str):
        self.ticket = ticket

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_tenders(self, fecha: str = None, estado: str = None,
                      codigo: str = None, codigo_proveedor: str = None,
                      codigo_organismo: str = None):
        """Consulta licitaciones de Mercado Público.

        Tipos de consulta soportados (ver documentación oficial):
          - Por código de licitación (codigo): ignora la fecha, devuelve detalle.
          - Del día actual: sin parámetros.
          - Por fecha (fecha, formato ddmmaaaa).
          - Por estado (estado: 'activas', 'publicada', 'cerrada', 'desierta',
            'adjudicada', 'revocada', 'suspendida', 'todos').
          - Por código de proveedor (codigo_proveedor) u organismo (codigo_organismo),
            normalmente combinados con fecha.
        """
        params = {'ticket': self.ticket}
        if codigo: params['codigo'] = codigo
        if fecha: params['fecha'] = fecha  # Formato ddmmaaaa
        if estado: params['estado'] = estado
        if codigo_proveedor: params['CodigoProveedor'] = codigo_proveedor
        if codigo_organismo: params['CodigoOrganismo'] = codigo_organismo

        response = requests.get(self.BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
