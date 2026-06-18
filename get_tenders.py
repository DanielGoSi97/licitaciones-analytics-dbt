import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

def fetch_tenders():
    ticket = os.getenv('MERCADO_PUBLICO_API_TICKET')
    if not ticket or ticket == 'tu_ticket_aqui_sin_comillas':
        print("Error: Por favor configura tu MERCADO_PUBLICO_API_TICKET en el archivo .env")
        return

    base_url = "http://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"
    params = {'ticket': ticket}

    try:
        print("Consultando API de Mercado Público...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        tenders = data.get('Listado', [])
        if not tenders:
            print("No se encontraron licitaciones activas.")
            return

        # Crear DataFrame
        df = pd.DataFrame(tenders)
        
        # Guardar en Excel
        output_file = 'licitaciones_actuales.xlsx'
        df.to_excel(output_file, index=False)
        print(f"Licitaciones guardadas exitosamente en {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar la API: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    fetch_tenders()
