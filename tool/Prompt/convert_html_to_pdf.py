"""
HTML to PDF Converter
Supports multiple conversion methods:
1. pdfkit (wkhtmltopdf) - Good for complex HTML/CSS
2. weasyprint - Good for web standards compliance
3. reportlab - Good for programmatic PDF generation
4. playwright - Good for modern web content
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLToPDFConverter:
    """HTML to PDF converter with multiple backend options"""
    
    def __init__(self):
        self.available_methods = self._check_available_methods()
        
    def _check_available_methods(self) -> Dict[str, bool]:
        """Check which conversion methods are available"""
        methods = {}
        
        # Check pdfkit
        try:
            import pdfkit
            methods['pdfkit'] = True
        except ImportError:
            methods['pdfkit'] = False
            
        # Check weasyprint
        try:
            import weasyprint
            methods['weasyprint'] = True
        except ImportError:
            methods['weasyprint'] = False
            
        # Check reportlab
        try:
            import reportlab
            methods['reportlab'] = True
        except ImportError:
            methods['reportlab'] = False
            
        # Check playwright
        try:
            import playwright
            methods['playwright'] = True
        except ImportError:
            methods['playwright'] = False
            
        return methods
    
    def convert_with_pdfkit(self, html_content: str, output_path: str, 
                           options: Optional[Dict[str, Any]] = None) -> bool:
        """Convert HTML to PDF using pdfkit (wkhtmltopdf)"""
        try:
            import pdfkit
            
            default_options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            if options:
                default_options.update(options)
            
            pdfkit.from_string(html_content, output_path, options=default_options)
            logger.info(f"Successfully converted HTML to PDF using pdfkit: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting with pdfkit: {e}")
            return False
    
    def convert_with_weasyprint(self, html_content: str, output_path: str,
                               base_url: Optional[str] = None) -> bool:
        """Convert HTML to PDF using weasyprint"""
        try:
            import weasyprint
            
            html_doc = weasyprint.HTML(string=html_content, base_url=base_url)
            html_doc.write_pdf(output_path)
            logger.info(f"Successfully converted HTML to PDF using weasyprint: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting with weasyprint: {e}")
            return False
    
    def convert_with_playwright(self, html_content: str, output_path: str,
                               options: Optional[Dict[str, Any]] = None) -> bool:
        """Convert HTML to PDF using playwright"""
        try:
            from playwright.sync_api import sync_playwright
            
            default_options = {
                'format': 'A4',
                'margin': {
                    'top': '1in',
                    'right': '1in',
                    'bottom': '1in',
                    'left': '1in'
                },
                'print_background': True
            }
            
            if options:
                default_options.update(options)
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html_content)
                page.pdf(path=output_path, **default_options)
                browser.close()
                
            logger.info(f"Successfully converted HTML to PDF using playwright: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting with playwright: {e}")
            return False
    
    def convert_file(self, html_file_path: str, output_path: str, 
                    method: str = 'auto', **kwargs) -> bool:
        """Convert HTML file to PDF"""
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self.convert_string(html_content, output_path, method, **kwargs)
            
        except Exception as e:
            logger.error(f"Error reading HTML file {html_file_path}: {e}")
            return False
    
    def convert_string(self, html_content: str, output_path: str, 
                      method: str = 'auto', **kwargs) -> bool:
        """Convert HTML string to PDF"""
        
        # Auto-select method if not specified
        if method == 'auto':
            method = self._select_best_method()
        
        # Validate method availability
        if method not in self.available_methods or not self.available_methods[method]:
            logger.error(f"Method '{method}' is not available. Available methods: {[k for k, v in self.available_methods.items() if v]}")
            return False
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert based on method
        if method == 'pdfkit':
            return self.convert_with_pdfkit(html_content, output_path, kwargs.get('options'))
        elif method == 'weasyprint':
            return self.convert_with_weasyprint(html_content, output_path, kwargs.get('base_url'))
        elif method == 'playwright':
            return self.convert_with_playwright(html_content, output_path, kwargs.get('options'))
        else:
            logger.error(f"Unknown method: {method}")
            return False
    
    def _select_best_method(self) -> str:
        """Select the best available conversion method"""
        # Priority order: playwright > weasyprint > pdfkit
        if self.available_methods.get('playwright'):
            return 'playwright'
        elif self.available_methods.get('weasyprint'):
            return 'weasyprint'
        elif self.available_methods.get('pdfkit'):
            return 'pdfkit'
        else:
            raise RuntimeError("No conversion methods available. Please install pdfkit, weasyprint, or playwright.")
    
    def convert_folder(self, input_folder: str, output_folder: str, 
                      method: str = 'auto', **kwargs) -> Dict[str, bool]:
        """Convert all HTML files in a folder to PDF files with the same names"""
        results = {}
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Find all HTML files in the input folder
        input_path = Path(input_folder)
        html_files = []
        
        # Look for HTML files with various extensions
        for extension in ['*.html', '*.htm', '*.HTML', '*.HTM']:
            html_files.extend(input_path.glob(extension))
        
        if not html_files:
            logger.warning(f"No HTML files found in {input_folder}")
            return results
        
        logger.info(f"Found {len(html_files)} HTML files to convert")
        
        # Convert each HTML file
        for html_file in html_files:
            try:
                # Create output path with same name but .pdf extension
                output_path = Path(output_folder) / f"{html_file.stem}.pdf"
                
                logger.info(f"Converting {html_file.name} -> {output_path.name}")
                success = self.convert_file(str(html_file), str(output_path), method, **kwargs)
                results[str(html_file)] = success
                
            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
                results[str(html_file)] = False
        
        return results
    
    def batch_convert(self, html_files: list, output_dir: str, 
                     method: str = 'auto', **kwargs) -> Dict[str, bool]:
        """Convert multiple HTML files to PDF"""
        results = {}
        
        for html_file in html_files:
            try:
                html_path = Path(html_file)
                output_path = Path(output_dir) / f"{html_path.stem}.pdf"
                
                success = self.convert_file(str(html_path), str(output_path), method, **kwargs)
                results[html_file] = success
                
            except Exception as e:
                logger.error(f"Error processing {html_file}: {e}")
                results[html_file] = False
        
        return results
    
    def print_available_methods(self):
        """Print available conversion methods"""
        print("Available conversion methods:")
        for method, available in self.available_methods.items():
            status = "✓" if available else "✗"
            print(f"  {status} {method}")
        
        if not any(self.available_methods.values()):
            print("\nNo conversion methods available. Please install one of the following:")
            print("  pip install pdfkit")
            print("  pip install weasyprint")
            print("  pip install playwright")


def main():
    parser = argparse.ArgumentParser(description='Convert HTML files to PDF')
    parser.add_argument('input_folder', help='Input folder containing HTML files')
    parser.add_argument('-o', '--output', required=True, help='Output folder for PDF files')
    parser.add_argument('-m', '--method', choices=['auto', 'pdfkit', 'weasyprint', 'playwright'], 
                       default='auto', help='Conversion method')
    parser.add_argument('--list-methods', action='store_true', help='List available methods')
    parser.add_argument('--single-file', action='store_true', help='Convert single HTML file instead of folder')
    
    args = parser.parse_args()
    
    converter = HTMLToPDFConverter()
    
    if args.list_methods:
        converter.print_available_methods()
        return
    
    if not args.input_folder:
        print("Error: Input folder is required")
        return
    
    # Check if input exists
    if not os.path.exists(args.input_folder):
        print(f"Error: Input path '{args.input_folder}' does not exist")
        return
    
    # Handle single file conversion
    if args.single_file:
        if not os.path.isfile(args.input_folder):
            print(f"Error: '{args.input_folder}' is not a file")
            return
        
        # For single file, output should be the full path including filename
        input_path = Path(args.input_folder)
        if os.path.isdir(args.output):
            output_path = Path(args.output) / f"{input_path.stem}.pdf"
        else:
            output_path = Path(args.output)
        
        success = converter.convert_file(args.input_folder, str(output_path), args.method)
        
        if success:
            print(f"Successfully converted {args.input_folder} to {output_path}")
        else:
            print(f"Failed to convert {args.input_folder}")
    
    else:
        # Handle folder conversion (default behavior)
        if not os.path.isdir(args.input_folder):
            print(f"Error: '{args.input_folder}' is not a directory")
            return
        
        print(f"Converting HTML files from: {args.input_folder}")
        print(f"Output folder: {args.output}")
        
        results = converter.convert_folder(args.input_folder, args.output, args.method)
        
        if not results:
            print("No HTML files found to convert")
            return
        
        # Print results
        successful = sum(1 for r in results.values() if r)
        total = len(results)
        print(f"\nConversion complete: {successful}/{total} files converted successfully")
        
        for file, success in results.items():
            status = "✓" if success else "✗"
            filename = os.path.basename(file)
            print(f"  {status} {filename}")
        
        if successful > 0:
            print(f"\nPDF files saved to: {args.output}")


if __name__ == "__main__":
    main()