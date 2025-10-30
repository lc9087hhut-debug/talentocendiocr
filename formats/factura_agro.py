import re
from text_extractor import TextExtractor

class FacturaExtractorAgro(TextExtractor):
    """
    Clase para extraer datos específicos del formato de factura AGROCAMPO.
    """

    def extract_data(self):
        """
        Extrae los datos requeridos de la factura usando expresiones regulares
        específicas para el formato AGROCAMPO.
        """
        extracted_data = {}
        
        # --- NIT Emisor ---
        nit_emisor_patterns = [
            r'NIT[:\s]*([0-9.\-]+)',
            r'N\.?I\.?T\.?[:\s]*([0-9\-]+)',
        ]
        extracted_data['nit_emisor'] = self._search_patterns(nit_emisor_patterns)

        # --- NIT Cliente ---
        nit_cliente_patterns = [
            r'CLIENTE.*?NIT[^\d]*([\d\-]+)',
            r'NIT[^\d]*([\d\-]+).*?TEL',
        ]
        extracted_data['nit_cliente'] = self._search_patterns(nit_cliente_patterns)

        # --- Fecha Emisión ---
        fecha_emision_patterns = [
            r'FECHA EMISIÓN[:\s]*(\d{2}/\d{2}/\d{4})',
            r'Fecha de emisión[:\s]*(\d{2}-\d{2}-\d{4})',
        ]
        extracted_data['fecha_emision'] = self._search_patterns(fecha_emision_patterns)

        # --- RAZÓN SOCIAL (Cliente) ---
        razon_patterns = [
            r'AGROCAMPO SAS Res\.',
            r'ELABORADO POR\s*([^\n]+)',
        ]
        razon_social = self._search_patterns(razon_patterns)
        if razon_social:
            # Tomamos solo el primer nombre (antes del espacio)
            extracted_data['razon_social'] = razon_social.split()[0]
        else:
            extracted_data['razon_social'] = ""

        # --- NÚMERO DE FACTURA ---
        # Buscamos específicamente después de "FACTURA ELECTRÓNICA DE VENTA"
        factura_patterns = [
            r'FACTURA ELECTRÓNICA DE VENTA FACTURA ELECTRÓNICA DE\s+([A-Z0-9]+)',
            r'FACTURA\s+([A-Z0-9]+)',
        ]
        extracted_data['numero_factura'] = self._search_patterns(factura_patterns)

        # --- SUBTOTAL (TOTAL BRUTO) ---
        subtotal_patterns = [
            r'TOTAL BRUTO[:\s]*([0-9., ]+)',
        ]
        subtotal = self._search_patterns(subtotal_patterns)
        extracted_data['subtotal'] = self._normalize_amount(subtotal)

        # --- IVA ---
        iva_patterns = [
            r'IVA\s+[0-9.]+%\s*([0-9., ]+)',  # IVA 5.00% 10,274.00
            r'VALOR\s*IMPUESTO\s*%\s*([0-9., ]+)',  # VALOR IMPUESTO % 10,274.00
            r'VALOR\s*IMPUESTO\s*[0-9.]+%\s*([0-9., ]+)',  # VALOR IMPUESTO 5.00% 10,274.00
            r'IMPUESTO\s*([0-9., ]+)',  # Si aparece solo IMPUESTO y luego el valor
            r'IVA\s*([0-9., ]+)',  # Si aparece solo IVA y luego el valor
        ]
        iva = self._search_patterns(iva_patterns)
        extracted_data['iva'] = self._normalize_amount(iva)

        # --- TOTAL ---
        total_patterns = [
            r'VALOR TOTAL[:\s]*([0-9., ]+)',
        ]
        total = self._search_patterns(total_patterns)
        extracted_data['valor_total'] = self._normalize_amount(total)

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
        required_fields = ['nit_emisor', 'nit_cliente', 'fecha_emision', 'iva', 'razon_social', 'numero_factura', 'valor_total']
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
        return "AGROCAMPO SAS" in text_upper or "WWW.AGROCAMPO.COM.CO" in text_upper