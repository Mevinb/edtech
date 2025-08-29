import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from typing import Optional, Dict, Any
import logging
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Advanced PDF processing with multiple extraction methods"""
    
    def __init__(self):
        self.extraction_methods = [
            self._extract_with_pdfplumber,
            self._extract_with_pypdf2,
            self._extract_with_pymupdf
        ]
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF using multiple methods for best results
        """
        try:
            # Try different extraction methods
            for method in self.extraction_methods:
                try:
                    text = method(file_path)
                    if text and len(text.strip()) > 100:  # Ensure meaningful text
                        logger.info(f"Successfully extracted text using {method.__name__}")
                        return self._clean_text(text)
                except Exception as e:
                    logger.warning(f"Method {method.__name__} failed: {str(e)}")
                    continue
            
            raise Exception("All extraction methods failed")
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_with_pdfplumber(self, file_path: str) -> str:
        """Extract text using pdfplumber (best for tables and layouts)"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    
    def _extract_with_pypdf2(self, file_path: str) -> str:
        """Extract text using PyPDF2 (good for simple PDFs)"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        return text
    
    def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (good for complex layouts)"""
        text = ""
        doc = fitz.open(file_path)
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n\n"
        doc.close()
        return text
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join lines and normalize spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Replace multiple spaces with single space
        import re
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Replace multiple newlines with double newline
        cleaned_text = re.sub(r'\n+', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    'page_count': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                    'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                    'subject': pdf_reader.metadata.get('/Subject', '') if pdf_reader.metadata else '',
                    'creator': pdf_reader.metadata.get('/Creator', '') if pdf_reader.metadata else '',
                }
                return metadata
        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {str(e)}")
            return {'page_count': 0}
    
    def extract_images(self, file_path: str, output_dir: str) -> list:
        """Extract images from PDF (for future diagram analysis)"""
        try:
            doc = fitz.open(file_path)
            image_list = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                image_matrix = page.get_images()
                
                for img_index, img in enumerate(image_matrix):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_name = f"page_{page_num}_img_{img_index}.png"
                        img_path = os.path.join(output_dir, img_name)
                        pix.save(img_path)
                        image_list.append(img_path)
                    
                    pix = None
            
            doc.close()
            return image_list
            
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            return []
    
    def is_scanned_pdf(self, file_path: str) -> bool:
        """Check if PDF is scanned (image-based) and needs OCR"""
        try:
            text = self._extract_with_pdfplumber(file_path)
            # If very little text is extracted, it's likely a scanned PDF
            return len(text.strip()) < 100
        except:
            return True
