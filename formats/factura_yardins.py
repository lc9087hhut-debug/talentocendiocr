"""import re
from text_extractor import TextExtractor

class FacturaExtractorYardins(TextExtractor):
    
    Clase para extraer datos específicos del formato de factura AGROCAMPO.
    

    def extract_data(self):
        
        Extrae los datos requeridos de la factura usando expresiones regulares
        específicas para el formato AGROCAMPO.
        
        extracted_data = {}
        
        # --- NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT[:\s]*([\d\-]+)',
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- NIT Cliente ---
        nit_cliente_patterns = [
            r'CC[:\s]*(\d+)',           # Busca 'CC:' seguido del número
            r'Cliente.*?NIT[^\d]*([\d\-]+)', # Patrón alternativo si la etiqueta fuera 'NIT'
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)

        # --- Fecha Emisión ---
        email_cliente_patterns = [
            r'Email:\s*(.+@.+\..+)',
        ]
        extracted_data['email_cliente'] = self._search_patterns(email_cliente_patterns)

        return extracted_data

    def _search_patterns(self, patterns):
        for pattern in patterns:
            match = re.search(pattern, self.text, re.IGNORECASE)
            if match:
                try:
                    return match.group(1).strip()
                except IndexError:
                    return match.group(0).strip()
        return ""

    def process(self):
        if not self.extract_text():
            return False, []
        extracted_data = self.extract_data()
        required_fields = ['nit_emisor', 'nit_cliente', 'email_cliente',]
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            return False, missing
        return True, extracted_data
    
    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"         
        value = re.sub(r'\s+', '', value)
        clean = re.sub(r"[^\d,\.]", "", value)
        
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')
        elif '.' in clean:
            pass      
        try:
            num = float(clean)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    @staticmethod
    def matches(text):
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        return "YARDINS" in text_upper or "BOGOTA" in text_upper"""

import re
from text_extractor import TextExtractor

class FacturaExtractorYardins(TextExtractor):
    """
    Clase para extraer datos específicos del formato de factura YARDINS.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos de la factura usando expresiones regulares
        específicas para el formato YARDINS.
        """
        extracted_data = {}
        
        # --- 1. NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT[:\s]*([\d\-\.]+)', # Captura números, guiones y puntos
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- 2. CC/NIT Cliente ---
        cc_cliente_patterns = [
            r'CC[:\s]*(\d+)',           # Busca 'CC:' seguido del número
            r'Cliente.*?NIT[^\d]*([\d\-]+)', # Patrón alternativo si la etiqueta fuera 'NIT'
        ]
        extracted_data['cc_cliente'] = self._search_patterns(cc_cliente_patterns)

        # --- 3. Email Cliente ---
        email_cliente_patterns = [
            r'Email[:\s]*([\w\.\-]+)[^\s@]+([\w\.\-]+\.\w+)',
            r'Email[:\s]*([\w\.\-]+)\s*.*?\s*([\w\.\-]+\.\w+)',
        ]
        extracted_data['email_cliente'] = self._search_patterns(email_cliente_patterns)

        # --- 4. Número de Factura ---
        numero_factura_patterns = [
            r'FACTURA\s+ELECTRÓNICA\s+DE\s+VENTA:\s*(\w+)',
        ]
        extracted_data['numero_factura'] = self._search_patterns(numero_factura_patterns)

        # --- 5. Fecha Emisión ---
        # Dato en factura: 2025-10-07 [cite: 38]
        fecha_emision_patterns = [
            r'Fecha\s+Emisión[:\s]*(\d{4}-\d{2}-\d{2})',
            r'Fecha\s+Pago:\s*(\d{4}-\d{2}-\d{2})', # En esta factura coincide con la fecha de pago [cite: 38, 39]
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)
        
        # --- 6. Total de la Operación ---
        total_patterns = [
            r'([\d\.,]+)\s*Total\s+de\s+la\s+operación:', 
            r'Total\s+de\s+la\s+operación:\s*COP\s*([\d\.,]+)',
            r'([\d\.,]+)\s*Total:',
            r'Total:\s*COP\s*([\d\.,]+)',
        ]
        # Almacenamos el valor sin normalizar por ahora
        total_str = self._search_patterns(total_patterns)
        extracted_data['total_operacion'] = self._normalize_amount(total_str)


        return extracted_data

    def _search_patterns(self, patterns):
        # NOTA: Usaremos self.text, asumiendo que TextExtractor ya cargó el contenido del PDF.
        for pattern in patterns:
            # re.IGNORECASE y re.DOTALL (para incluir saltos de línea)
            match = re.search(pattern, self.text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    # Intenta capturar el grupo 1 (el valor entre paréntesis)
                    return match.group(1).strip()
                except IndexError:
                    # Si no hay grupo 1, devuelve el match completo
                    return match.group(0).strip()
        return ""

    def process(self):
        # ... (Tu código de process se mantiene igual, PERO ajustamos required_fields)
        if not self.extract_text():
            return False, []
            
        extracted_data = self.extract_data()
        
        # Ajuste en los campos requeridos: cambiamos 'nit_cliente' por 'cc_cliente'
        required_fields = ['nit_emisor','cc_cliente','numero_factura','fecha_emision', 'total_operacion']
        
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            print(f"Campos faltantes: {missing}")
            return False, missing
            
        return True, extracted_data
    
    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"         
        value = re.sub(r'\s+', '', value)
        clean = re.sub(r"[^\d,\.]", "", value)
        
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')
        elif '.' in clean:
            pass      
        try:
            num = float(clean)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    @staticmethod
    def matches(text):
        if not isinstance(text, str):
            return False
        text_upper = text.upper()
        return "YARDINS" in text_upper or "BOGOTA" in text_upper