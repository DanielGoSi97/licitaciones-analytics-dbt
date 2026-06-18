import os
import boto3
import pandas as pd
import logging
import requests
from client import MercadoPublicoClient
from io import StringIO
from models import TenderAPIResponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def send_alert_to_n8n(message, is_error=True):
    webhook_url = os.environ.get('N8N_WEBHOOK_URL')
    if not webhook_url:
        logger.warning("No se ha configurado N8N_WEBHOOK_URL")
        return
        
    payload = {
        "status": "error" if is_error else "success",
        "message": message,
        "function": "TenderCollectorLambda"
    }
    try:
        requests.post(webhook_url, json=payload, timeout=5)
    except Exception as e:
        logger.error(f"Error fatal enviando alerta a n8n: {e}")

def lambda_handler(event, context):
    try:
        ticket = os.environ.get('MERCADO_PUBLICO_API_TICKET')
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        
        # Opcional: recibir filtros desde el evento (ej: EventBridge o trigger manual)
        fecha = event.get('fecha')
        estado = event.get('estado')
        
        client = MercadoPublicoClient(ticket)
        raw_data = client.fetch_tenders(fecha=fecha, estado=estado)
        
        # Validación con Pydantic
        validated_data = TenderAPIResponse(**raw_data)
        
        if validated_data.Listado:
            # Convertir objetos Pydantic a lista de diccionarios
            data = [t.model_dump() for t in validated_data.Listado]
            df = pd.DataFrame(data)
            
            # Convertir a CSV en memoria
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            
            # Subir a S3
            s3 = boto3.client('s3')
            s3.put_object(
                Bucket=bucket_name,
                Key='licitaciones_finales.csv',
                Body=csv_buffer.getvalue()
            )
            logger.info("Datos subidos correctamente a S3")
            send_alert_to_n8n("Extracción de licitaciones completada exitosamente.", is_error=False)
            return {"status": "success"}
        else:
            send_alert_to_n8n("No se encontraron licitaciones nuevas.", is_error=False)
            return {"status": "no_data"}
            
    except Exception as e:
        error_msg = f"Error crítico en la ejecución: {str(e)}"
        logger.error(error_msg)
        send_alert_to_n8n(error_msg, is_error=True)
        raise e 
