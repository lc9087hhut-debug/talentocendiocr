import re
from text_extractor import TextExtractor

class FacturaExtractorLatam(TextExtractor):
    """
    Clase para extraer datos específicos de tiquetes LATAM Airlines.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos del tiquete LATAM usando expresiones regulares.
        """
        extracted_data = {}
        
        # --- 1. Fecha de Emisión ---
        fecha_emision_patterns = [
            r'Ciudad\s+y\s+Fecha\s+de\s+emisi[oó]n\s+[^0-9]*(\d{2}/\d{2}/\d{2})',
            r'Fecha\s+de\s+emisi[oó]n[:\s]*(\d{2}/\d{2}/\d{2})',
            r'Colombia\s+(\d{2}/\d{2}/\d{2})',
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)

        # --- 2. Número de Factura (Nº de orden) ---
        # Patrones más flexibles para capturar LA0354771BNAY
        numero_factura_patterns = [
            r'N\s*de\s+orden\s+([A-Z]{2}\d+[A-Z]+)',
            r'orden\s+([A-Z]{2}\d{7,}[A-Z]*)',
            r'de\s+orden\s+([A-Z0-9]{10,})',
            r'OCTKSP\s+N\s+de\s+orden\s+([A-Z0-9]+)',
            r'(LA\d{7,}[A-Z]+)',
        ]
        extracted_data['numero_factura'] = self._search_patterns(numero_factura_patterns)

        # --- 3. Total Pagado ---
        valor_total_patterns = [
            r'Forma\s+de\s+pago\s+([\d\.]+)',
            r'pago\s+([\d\.]+)\s+Vuelo', 
        ]
        total_str = self._search_patterns(valor_total_patterns)
        extracted_data['valor_total'] = self._normalize_amount(total_str)

        # --- 4. Subtotal (Vuelo) ---
        subtotal_patterns = [
            r'Vuelo\s+\$\s*([\d\.,]+)',
            r'Vuelo\s+([\d\.,]+)',
            r'Pasaje\s+\$?\s*([\d\.,]+)',
        ]
        subtotal_str = self._search_patterns(subtotal_patterns)
        extracted_data['subtotal'] = self._normalize_amount(subtotal_str)

        # --- 5. IVA/Tasas (Tasas y/o impuestos) ---
        iva_patterns = [
            r'Vuelo\s+[\d\.]+\s+([\d\.]+)', 
            r'([\d\.]+)\s+LATAM\s+Wallet',
        ]
        iva_str = self._search_patterns(iva_patterns)
        extracted_data['iva'] = self._normalize_amount(iva_str)

        # --- 6. Razón Social ---
        razon_social_patterns = [
            r'(AEROVIAS\s+DE\s+INTEGRACI[OÓ]N\s+REGIONAL\s+S\.A\.)',
            r'(AEROVIAS\s+DE\s+INTEGRACION\s+REGIONAL\s+S\s*A)',
            r'(LATAM\s+AIRLINES\s+COLOMBIA)',
        ]
        razon_social = self._search_patterns(razon_social_patterns)
        if not razon_social:
            razon_social = "LATAM AIRLINES COLOMBIA"
        extracted_data['razon_social'] = razon_social

        # --- 7. NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT\s+([\d\.\-\s]+\-\s*\d)',
            r'NIT[:\s]*([\d\.\-]+)',
            r'NIT\s+(\d{3}\.\d{3}\.\d{3}\s*\-\s*\d)',
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- 8. NIT/Documento Cliente ---
        nit_cliente_patterns = [
            r'Documento\s+de\s+Identificaci[oó]n\s+(\d{7,})',
            r'Identificacion\s+(\d{7,})',
            r'Adulto\s+(\d{7,})',
            r'LOPEZ\s+Adulto\s+(\d{7,})',
            r'pasajero\s+Documento\s+de\s+Identificaci[oó]n\s+[^\d]*(\d{7,})',
            r'Adulto\s+\d+\s+(\d{7,})',
            r'Tipo\s+de\s+pasajero.*?(\d{10})',
            r'USECHE.*?(\d{10})',
            r'(\d{10})',
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)

        return extracted_data

    def _search_patterns(self, patterns):
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    result = match.group(1).strip()
                    # Limpieza adicional de espacios
                    result = re.sub(r'\s+', ' ', result).strip()
                    return result
                except IndexError:
                    result = match.group(0).strip()
                    return re.sub(r'\s+', ' ', result).strip()
        return ""

    def process(self):
        if not self.extract_text():
            return False, []
        
        print(f"\n=== DEBUG: Búsqueda de documento ===")
        
        doc_number = "1022981317"
        if doc_number in self.text:
            idx = self.text.index(doc_number)
            start = max(0, idx - 100)
            end = min(len(self.text), idx + 150)
            print(f"Contexto alrededor del documento:")
            print(f"'{self.text[start:end]}'")
        
        # Buscar "Adulto" y mostrar contexto
        adulto_matches = [m.start() for m in re.finditer(r'Adulto', self.text, re.IGNORECASE)]
        if adulto_matches:
            print(f"\nEncontradas {len(adulto_matches)} ocurrencias de 'Adulto':")
            for i, idx in enumerate(adulto_matches[:3], 1):  
                start = max(0, idx - 50)
                end = min(len(self.text), idx + 100)
                print(f"{i}. '{self.text[start:end]}'")
        
        print("=== FIN DEBUG ===\n")
            
        extracted_data = self.extract_data()
        
        required_fields = [
            'fecha_emision', 
            'numero_factura', 
            'valor_total', 
            'subtotal', 
            'iva', 
            'razon_social', 
            'nit_emisor', 
            'nit_cliente'
        ]
        
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            print(f"Campos faltantes: {missing}")
            print(f"Datos extraídos: {extracted_data}")
            return False, missing
            
        return True, extracted_data
    
    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"
        value = re.sub(r'\s+', '', value)
        value = value.replace('$', '').replace('S', '')
        
        clean = re.sub(r"[^\d\.]", "", value)
        
        if not clean:
            return "0,00"
        
        if '.' in clean:
            clean = clean.replace('.', '')
        
        try:
            num = int(clean)
            formatted = f"{num:,}" 
            
            formatted = formatted.replace(",", ".")
            
            return formatted + ",00"
            
        except (ValueError, OverflowError):
            return "0,00"

    @staticmethod
    def matches(text):
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        return ("LATAM" in text_upper and "AIRLINES" in text_upper) or \
               ("AEROVIAS" in text_upper and "REGIONAL" in text_upper) or \
               "TIQUETE DE TRANSPORTE" in text_upper