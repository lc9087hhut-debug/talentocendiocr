import re
from text_extractor import TextExtractor

class FacturaExtractorTaberna(TextExtractor):
    """
    Clase para extraer datos del formato de factura TABERNA.
    """

    def extract_data(self):
        extracted_data = {}

        # NIT
        extracted_data['nit'] = self._search_patterns([
            r'NIT[:\s]*([0-9.\-]+)',
            r'N\.?I\.?T\.?[:\s]*([0-9\-]+)',
        ])

        # FECHA
        extracted_data['fecha'] = self._search_patterns([
            r'FECHA[:\s]*(\d{2}/\d{2}/\d{4})',
            r'Fecha[:\s]*(\d{2}-\d{2}-\d{4})',
        ])

        # RAZÓN SOCIAL
        extracted_data['razon_social'] = self._search_patterns([
            r'RAZÓN SOCIAL[:\s]*([^\n]+)',
            r'CLIENTE[:\s]*([^\n]+)',
        ])

        # NÚMERO DE FACTURA
        extracted_data['numero_factura'] = self._search_patterns([
            r'FACTURA No\.[:\s]*([A-Z0-9\-]+)',
            r'FACTURA[:\s]*([A-Z0-9\-]+)',
        ])

        # SUBTOTAL
        extracted_data['subtotal'] = self._search_patterns([
            r'SUBTOTAL[:\s]*([0-9.,]+)',
        ])

        # IMPUESTOS
        extracted_data['valor_impuestos'] = self._search_patterns([
            r'IVA[:\s]*([0-9.,]+)',
        ])

        # TOTAL
        extracted_data['valor_total'] = self._search_patterns([
            r'TOTAL[:\s]*([0-9.,]+)',
        ])

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
        if not self.extract_text_tesseract():
            return False, []
        extracted_data = self.extract_data()
        required_fields = ['nit', 'fecha', 'razon_social', 'numero_factura', 'valor_total']
        missing = [f for f in required_fields if not extracted_data.get(f)]
        if missing:
            return False, missing
        return True, extracted_data

