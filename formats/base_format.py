import re
from text_extractor import TextExtractor

class BaseFactura(TextExtractor):

    def __init__(self, text):
        self.text = text.lower()
    
    def extract_data(self):
        """Método abstracto: cada clase hija debe implementarlo"""
        raise NotImplementedError("Debe implementarse en la subclase.")

    @staticmethod
    def _normalize_amount(value):

    @staticmethod
    def matches(text):