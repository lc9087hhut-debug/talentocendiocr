import re
from text_extractor import TextExtractor

class FacturaExtractorBBI(TextExtractor):
    """
    Extractor para facturas electrónicas colombianas con formato estándar DIAN.
    Compatible con BBI, Tostao, Carulla, Éxito, etc., siempre que usen estructura similar.
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
        print("🧩 Iniciando extracción estructural (formato Colombia)...")
        
        # Extraer texto si no ha sido extraído
        if not self.has_text():
            self.extract_text()
        if not self.has_text():
            print("No se pudo extraer texto del documento")
            return False, {}

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

        # --- FECHA DE EMISIÓN ---
        m = re.search(r"Fecha de Emisi[oó]n:\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})", text, re.IGNORECASE)
        if m:
            data["fecha_emision"] = m.group(1)

        # --- NÚMERO DE FACTURA ---
        m = re.search(r"Número de Factura[:\s]*([\w\-]+)", text, re.IGNORECASE)
        if m:
            data["numero_factura"] = m.group(1).strip()
        else:
            m = re.search(r"(\b\d{3,4}[A-Z\-]*\d{4,5}\b)", text)
            if m:
                data["numero_factura"] = m.group(1).replace(" ", "").strip()

        # --- TOTAL FACTURA ---
        valor_total = None
        m = re.search(r'Total factura COP\s*([\d\.,]+)', text, re.IGNORECASE)
        if m:
            valor_total = self._normalize_amount(m.group(1))
        else:
            m = re.search(r'Total factura\s*\(\=\)[^\d]*([\d\.,]{5,})', text, re.IGNORECASE)
            if m:
                valor_total = self._normalize_amount(m.group(1))
            else:
                m = re.search(r'Total neto factura\s*\(\=\)\s*([\d\.,]+)', text, re.IGNORECASE)
                if m:
                    valor_total = self._normalize_amount(m.group(1))

        data["valor_total"] = valor_total if valor_total else "0,00"

        # --- SUBTOTAL ---
        patterns_subtotal = [
            r'Subtotal\s*([\d\.,]+)',
            r'Subtota[l]*[\w\s]{0,10}?([\d\.,]{3,15})',
        ]
        subtotal = None
        for pattern in patterns_subtotal:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                subtotal = self._normalize_amount(m.group(1))
                break
        data["subtotal"] = subtotal if subtotal else "0,00"

        # --- IVA / TOTAL IMPUESTOS ---
        patterns_iva = [
            r'Total impuesto\s*([\d\.,]+)', 
            r'IVA\s*[\d\.,%]*\s*([\d\.,]+)',
            r'IMPUESTOS\s*([\d\.,]+)',
        ]
        iva_total = None
        for pattern in patterns_iva:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                iva_total = self._normalize_amount(m.group(1))
                break
        data["iva"] = iva_total if iva_total else "0,00"

        # --- RAZÓN SOCIAL ---
        m = re.search(r'Raz[oó]n Social[:\s]*([A-Z0-9\s\.\-&]+?)(?=\s*(?:Nombre Comercial|Nit del Emisor|País|Tipo de Contribuyente|$))', text, re.IGNORECASE)
        if m:
            data["razon_social"] = m.group(1).strip()
        else:
            m2 = re.search(r'Nombre Comercial[:\s]*([A-Z0-9\s\.\-&]+?)(?=\s*(?:Nit del Emisor|País|$))', text, re.IGNORECASE)
            if m2:
                data["razon_social"] = m2.group(1).strip()

        # --- NIT EMISOR ---
        m = re.search(r'Nit del Emisor[:\s]*([\d\.\-\s]{8,15})', text, re.IGNORECASE)
        if m:
            nit = re.sub(r'[\s\.]', '', m.group(1))
            data["nit_emisor"] = nit

        # --- NIT CLIENTE ---
        m = re.search(r"Número Documento[:\s]*(\d{8,12})", text, re.IGNORECASE)
        if m:
            data["nit_cliente"] = m.group(1)
        else:
            m = re.search(r"(?:Adquiriente|Comprador).*?NIT\D*(\d{8,12})", text, re.IGNORECASE | re.DOTALL)
            if m:
                data["nit_cliente"] = m.group(1)
        return data

    @staticmethod
    def _normalize_amount(value):
        if not value:
            return "0,00"         
        clean = re.sub(r"[^\d,\.]", "", value)
        clean = clean.replace(".", "").replace(",", ".")
        try:
            num = float(clean)
            return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return "0,00"

    @staticmethod
    def matches(text: str) -> bool:
        """
        Detecta si el texto pertenece a una factura de BBI COLOMBIA S.A.S.
        Tolerante a errores OCR (B8I, espacios, puntos omitidos, etc.)
        """
        text_upper = text.upper()
        patrones = [
            r"NOMBRE\s*COMERCIAL[:\s]*B+[^A-Z0-9]*I*\s*COLOMBIA", 
            r"RAZ[ÓO]N\s*SOCIAL[:\s]*B+I+\s*COLOMBIA",
            r"BBI\s*COLOMBIA\s*S",  
            r"BBICOLOMBIASAS",     
            r"B8I\s*COLOMBIA",  
        ]
        for patron in patrones:
            if re.search(patron, text_upper):
                return True
        if "900860284" in text_upper:
            return True

        return False
