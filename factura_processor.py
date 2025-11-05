from formats.factura_bbi import FacturaExtractorBBI
from formats.factura_hellen import FacturaExtractorHellen
from formats.factura_agro import FacturaExtractorAgro
from formats.factura_taberna import FacturaExtractorTaberna
from formats.factura_cuotas import FacturaExtractorCuotas
from formats.factura_latam import FacturaExtractorLatam
from formats.factura_avianca import FacturaExtractorAvianca
from formats.factura_procafe import FacturaExtractorProcafe
from formats.factura_d1 import FacturaExtractorD1

# CLASE PRINCIPAL: FACTURA PROCESSOR
class FacturaProcessor:
    """
    Clase principal que coordina la extracción de datos según el tipo de factura.
    Gestiona la instancia del extractor correcto según el tipo detectado.
    """

    # Mapa centralizado de extractores disponibles
    MAPA_EXTRACTORES = {
        "bbi": FacturaExtractorBBI,
        "hellen": FacturaExtractorHellen,
        "agro": FacturaExtractorAgro,
        "taberna": FacturaExtractorTaberna,
        "cuotas": FacturaExtractorCuotas,
        "latam": FacturaExtractorLatam,
        "avianca": FacturaExtractorAvianca,
        "procafe": FacturaExtractorProcafe,
        "d1": FacturaExtractorD1,
    }

    @staticmethod
    def process_factura(file_path, factura_type="desconocido"):
        if not factura_type or factura_type.lower() == "desconocido":
            print("Tipo de factura no reconocido o vacío.")
            return False, {}

        tipo_normalizado = factura_type.strip().lower()       
        if tipo_normalizado not in FacturaProcessor.MAPA_EXTRACTORES:
            print(f"Tipo de factura no soportado: {factura_type}")
            print(f"Tipos válidos: {', '.join(FacturaProcessor.MAPA_EXTRACTORES.keys())}")
            return False, {}
        extractor_class = FacturaProcessor.MAPA_EXTRACTORES[tipo_normalizado]
        
        try:
            print(f"Iniciando procesamiento con extractor: {extractor_class.__name__}")
            extractor = extractor_class(file_path)

            # Paso 1: Extraer texto si es necesario
            if hasattr(extractor, "extract_text") and not extractor.text:
                print("Extrayendo texto del documento...")
                extractor.extract_text()
            elif hasattr(extractor, "extract_text") and extractor.text:
                print("Texto ya extraído, omitiendo paso de extracción.")

            # Paso 2: Ejecutar el metodo principal
            if hasattr(extractor, "process"):
                success, data = extractor.process()
            elif hasattr(extractor, "extraer_datos"):
                data = extractor.extraer_datos()
                success = bool(data) and isinstance(data, dict) and len(data) > 0
            else:
                print(f"El extractor {extractor_class.__name__} no tiene método 'process' ni 'extraer_datos'.")
                return False, {}
            if not success:
                print(f"El extractor {extractor_class.__name__} devolvió un error.")
                return False, {}               
            if not isinstance(data, dict):
                print(f"El extractor {extractor_class.__name__} no devolvió un diccionario.")
                return False, {}               
            if len(data) == 0:
                print(f"El extractor {extractor_class.__name__} devolvió un diccionario vacío.")
                return False, {}

            required_fields = ["fecha_emision", "numero_factura", "valor_total", "subtotal", "iva", "razon_social", "nit_emisor", "nit_cliente"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"Campos faltantes en {extractor_class.__name__}: {', '.join(missing_fields)}")

            print(f"Extracción completada: {len(data)} campos encontrados.")
            return True, data

        except Exception as e:
            print(f"Error al procesar factura tipo {factura_type}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, {}