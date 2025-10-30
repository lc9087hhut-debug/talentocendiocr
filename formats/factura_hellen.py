import re
from text_extractor import TextExtractor

class FacturaExtractorHellen(TextExtractor):
    """
    Extractor para facturas de Cine Colombia (Factura_hellen.pdf).
    """
    def __init__(self, file_path):
        super().__init__(file_path)
        self.fields = [
            "fecha_emision",
            "numero_factura",
            "valor_total",
            "subtotal",
            "iva",
            "razon_social",
            "nit_emisor",
            "nit_cliente"
        ]

    def process(self):
        print("Iniciando extracción estructural (Cine Colombia)...")
        if not self.text:
            self.extract_text()
        extracted = self.extract_data()
        missing = [f for f, v in extracted.items() if not v]
        if missing:
            print(f"Campos faltantes: {', '.join(missing)}")
            return False, extracted
        print("Todos los campos extraídos correctamente.")
        return True, extracted

    def extract_data(self):
        data = {field: "" for field in self.fields}
        text = self.text

        # --- RAZÓN SOCIAL (emisor) ---
        m = re.search(
            r"NIT:\s*[\d\.\-]+\s+([A-Z\s\.]+?)(?=\s+(?:es\s+responsable|Agente\s+Retenedor|Factura\s+electrónica|www\.|$))",
            text,
            re.IGNORECASE
        )
        if m:
            data["razon_social"] = m.group(1).strip()
        else:
            # Fallback: buscar explícitamente "CINE COLOMBIA S.A.S."
            if "CINE COLOMBIA S.A.S." in text:
                data["razon_social"] = "CINE COLOMBIA S.A.S."
            else:
                data["razon_social"] = ""

        # --- NIT EMISOR ---
        m = re.search(r"NIT:\s*([\d\.\-]+)", text, re.IGNORECASE)
        if m:
            data["nit_emisor"] = re.sub(r'[^\d\-]', '', m.group(1))

        # --- NÚMERO DE FACTURA ---
        m = re.search(r"Factura Electrónica de Venta[^:]*:\s*[^\s]*\s*(AME-\d+)", text, re.IGNORECASE)
        if m:
            data["numero_factura"] = m.group(1).strip()
        else:
            m = re.search(r"\b(AME-\d+)\b", text, re.IGNORECASE)
            if m:
                data["numero_factura"] = m.group(1)

        # --- FECHA DE EMISIÓN ---
        m = re.search(r"ce:\s*(\d{1,2})[-\s](ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[a-z\.]*[-\s](\d{4})", text, re.IGNORECASE)
        if m:
            dia, mes_texto, año = m.groups()
            mes_map = {
                'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'ago': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
            }
            mes = mes_map.get(mes_texto.lower()[:3], '01')
            data["fecha_emision"] = f"{int(dia):02d}/{mes}/{año}"

        # --- VALOR TOTAL ---
        m = re.search(r"VALOR TOTAL\s*([\d\.,]{5,})", text)
        if m:
            data["valor_total"] = self._normalize_amount(m.group(1))
        else:
            # Fallback: buscar el último número grande del bloque de totales
            totals = re.findall(r"(?:VALOR TOTAL|TOTAL)\s*([\d\.,]{5,})", text)
            if totals:
                data["valor_total"] = self._normalize_amount(totals[-1])

        # --- SUBTOTAL ---
        m = re.search(r"SUBTOTAL[^\d]*([\d\.,]{5,})", text)
        if m:
            data["subtotal"] = self._normalize_amount(m.group(1))

        # --- IVA ---
        m = re.search(r"IMPUESTO A LAS VENTAS[^\d]*([\d\.,]{4,})", text)
        if m:
            data["iva"] = self._normalize_amount(m.group(1))

        # --- NIT CLIENTE ---
        m = re.search(r"NO\.\s*IDENTIFICACIÓN[:\s]*(\d{6,12})", text, re.IGNORECASE)
        if m:
            data["nit_cliente"] = m.group(1)
        return data

    @staticmethod
    def _normalize_amount(value):
        clean = re.sub(r"[^\d,\.]", "", value)
        clean = clean.replace(".", "").replace(",", ".")
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
        return (
            ("CINE" in text_upper and "COLOMBIA" in text_upper)
            or "FACTURA ELECTRÓNICA DE VENTA" in text_upper
        ) and "NIT" in text_upper
