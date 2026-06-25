import * as fs from 'fs';
import * as path from 'path';
import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';
import * as xlsx from 'xlsx';
import officeParser from 'officeparser';
import * as cheerio from 'cheerio';
import csvParser from 'csv-parser';

export interface DocumentSegment {
  content: string;
  location: string; // e.g. "Página 1", "Diapositiva 2", "Filas 10-15", "Sección: ## Reglas"
}

/**
 * Limpia ruidos, dobles espacios, líneas en blanco excesivas y retornos de carro corruptos
 */
export function cleanTextContent(text: string): string {
  return text
    .replace(/\r\n/g, '\n')                     // Normalizar saltos de línea
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F]/g, '') // Eliminar caracteres de control corruptos
    .replace(/[ \t]+/g, ' ')                    // Colapsar espacios y tabulaciones duplicadas
    .replace(/\n\s*\n\s*\n+/g, '\n\n')          // Colapsar múltiples saltos de línea vacíos
    .trim();
}

/**
 * Parsea un documento HTML dividiéndolo por secciones usando los encabezados (h1, h2, h3)
 */
export function parseHtmlToSegments(htmlContent: string): DocumentSegment[] {
  const $ = cheerio.load(htmlContent);
  $('script, style').remove();
  
  const segments: DocumentSegment[] = [];
  let currentHeader = 'General';
  let currentContent: string[] = [];
  
  $('body').children().each((_, element) => {
    const tagName = element.tagName.toLowerCase();
    
    if (['h1', 'h2', 'h3', 'h4'].includes(tagName)) {
      // Si ya teníamos contenido acumulado, guardarlo antes de cambiar de sección
      if (currentContent.length > 0) {
        const text = cleanTextContent(currentContent.join('\n'));
        if (text.length > 0) {
          segments.push({ content: text, location: `Sección: ${currentHeader}` });
        }
        currentContent = [];
      }
      currentHeader = $(element).text().trim();
    } else {
      const text = $(element).text().trim();
      if (text.length > 0) {
        currentContent.push(text);
      }
    }
  });
  
  // Guardar la última sección
  if (currentContent.length > 0) {
    const text = cleanTextContent(currentContent.join('\n'));
    if (text.length > 0) {
      segments.push({ content: text, location: `Sección: ${currentHeader}` });
    }
  }
  
  return segments;
}

/**
 * Parsea un archivo PDF página por página interceptando el flujo de pdf-parse
 */
export async function parsePdfToSegments(fileBuffer: Buffer): Promise<DocumentSegment[]> {
  const segments: DocumentSegment[] = [];
  let pageCounter = 0;
  
  const options = {
    pagerender: async (pageData: any) => {
      pageCounter++;
      const textContent = await pageData.getTextContent();
      let lastY = -1;
      let pageText = '';
      
      for (const item of textContent.items) {
        if (lastY === -1 || lastY === item.transform[5]) {
          pageText += item.str;
        } else {
          pageText += '\n' + item.str;
        }
        lastY = item.transform[5];
      }
      
      const cleanText = cleanTextContent(pageText);
      if (cleanText.length > 0) {
        segments.push({
          content: cleanText,
          location: `Página ${pageCounter}`
        });
      }
      return pageText;
    }
  };
  
  await pdfParse(fileBuffer, options);
  return segments;
}

/**
 * Parsea un archivo Word (.docx) convirtiéndolo temporalmente a HTML 
 * para segmentar el texto lógicamente por encabezados.
 */
export async function parseDocxToSegments(fileBuffer: Buffer): Promise<DocumentSegment[]> {
  const result = await mammoth.convertToHtml({ buffer: fileBuffer });
  return parseHtmlToSegments(result.value);
}

/**
 * Parsea hojas de cálculo Excel (.xlsx / .xls) agrupando filas y marcando la ubicación exacta
 */
export function parseXlsxToSegments(filePath: string, rowsPerSegment: number = 10): DocumentSegment[] {
  const workbook = xlsx.readFile(filePath);
  const segments: DocumentSegment[] = [];
  
  for (const sheetName of workbook.SheetNames) {
    const worksheet = workbook.Sheets[sheetName];
    // Convertir la hoja a formato JSON estructurado
    const jsonData: any[] = xlsx.utils.sheet_to_json(worksheet, { header: 1 });
    
    if (jsonData.length === 0) continue;
    
    const headers = jsonData[0]; // Encabezados de columnas
    const dataRows = jsonData.slice(1);
    
    for (let i = 0; i < dataRows.length; i += rowsPerSegment) {
      const rowGroup = dataRows.slice(i, i + rowsPerSegment);
      const startRow = i + 2; // Fila 1 es el header (1-indexed), datos parten en fila 2
      const endRow = startRow + rowGroup.length - 1;
      
      // Convertir el bloque de filas a un texto representativo
      const contentText = rowGroup.map((row, index) => {
        const rowNum = startRow + index;
        const rowDetails = headers.map((header: any, colIdx: number) => {
          const val = row[colIdx] !== undefined ? row[colIdx] : '';
          return `${header}: ${val}`;
        }).join(' | ');
        return `[Fila ${rowNum}] ${rowDetails}`;
      }).join('\n');
      
      segments.push({
        content: contentText,
        location: `Hoja: ${sheetName}, Filas ${startRow}-${endRow}`
      });
    }
  }
  
  return segments;
}

/**
 * Parsea presentaciones PowerPoint (.pptx) diapositiva por diapositiva
 */
export async function parsePptxToSegments(filePath: string): Promise<DocumentSegment[]> {
  return new Promise((resolve, reject) => {
    officeParser.parseOffice(filePath, (data: any, err: any) => {
      if (err) {
        return reject(err);
      }
      
      // PowerPoint a veces se retorna separado por marcadores de slide
      // Si officeparser concatena todo, dividimos por dobles saltos de línea grandes
      const slidesText = data.split(/\n\s*\n\s*Slide \d+\s*\n/i);
      
      const segments = slidesText.map((slideContent: string, index: number) => ({
        content: cleanTextContent(slideContent),
        location: `Diapositiva ${index + 1}`
      })).filter((seg: any) => seg.content.length > 0);
      
      resolve(segments);
    }, { outputHTML: false });
  });
}

/**
 * Parsea un archivo CSV agrupando filas y manteniendo los metadatos de filas
 */
export async function parseCsvToSegments(filePath: string, rowsPerSegment: number = 8): Promise<DocumentSegment[]> {
  return new Promise((resolve, reject) => {
    const results: any[] = [];
    fs.createReadStream(filePath)
      .pipe(csvParser())
      .on('data', (data) => results.push(data))
      .on('end', () => {
        const segments: DocumentSegment[] = [];
        
        for (let i = 0; i < results.length; i += rowsPerSegment) {
          const rowGroup = results.slice(i, i + rowsPerSegment);
          const startRow = i + 1;
          const endRow = startRow + rowGroup.length - 1;
          
          const contentText = rowGroup.map((row, index) => {
            const rowNum = startRow + index;
            const details = Object.entries(row).map(([key, val]) => `${key}: ${val}`).join(' | ');
            return `[Registro ${rowNum}] ${details}`;
          }).join('\n');
          
          segments.push({
            content: contentText,
            location: `Filas ${startRow}-${endRow}`
          });
        }
        
        resolve(segments);
      })
      .on('error', (err) => reject(err));
  });
}

/**
 * Parsea archivos Markdown dividiendo por secciones lógicas usando sus encabezados (##, ###)
 */
export function parseMarkdownToSegments(mdContent: string): DocumentSegment[] {
  const lines = mdContent.split('\n');
  const segments: DocumentSegment[] = [];
  let currentHeader = 'General';
  let currentContent: string[] = [];
  
  for (const line of lines) {
    if (line.startsWith('#')) {
      // Guardar sección anterior
      if (currentContent.length > 0) {
        const text = cleanTextContent(currentContent.join('\n'));
        if (text.length > 0) {
          segments.push({ content: text, location: `Sección: ${currentHeader}` });
        }
        currentContent = [];
      }
      currentHeader = line.trim();
    } else {
      currentContent.push(line);
    }
  }
  
  // Guardar última sección
  if (currentContent.length > 0) {
    const text = cleanTextContent(currentContent.join('\n'));
    if (text.length > 0) {
      segments.push({ content: text, location: `Sección: ${currentHeader}` });
    }
  }
  
  return segments;
}

/**
 * Parsea un archivo JSON estructurado (ej. un array de objetos o un objeto anidado)
 */
export function parseJsonToSegments(jsonContent: string): DocumentSegment[] {
  const obj = JSON.parse(jsonContent);
  const segments: DocumentSegment[] = [];
  
  if (Array.isArray(obj)) {
    // Si es un array, tratamos cada objeto del array como un registro
    obj.forEach((item, index) => {
      segments.push({
        content: cleanTextContent(JSON.stringify(item, null, 2)),
        location: `Registro índice ${index}`
      });
    });
  } else {
    // Si es un objeto, podemos dividirlo por sus propiedades principales
    Object.entries(obj).forEach(([key, val]) => {
      segments.push({
        content: cleanTextContent(`${key}: ${JSON.stringify(val, null, 2)}`),
        location: `Llave principal: ${key}`
      });
    });
  }
  
  return segments;
}

/**
 * Parsea un archivo según su extensión y retorna un array de segmentos estructurados con ubicación
 */
export async function parseDocumentToSegments(filePath: string): Promise<DocumentSegment[]> {
  const ext = path.extname(filePath).toLowerCase();
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`El archivo no existe en la ruta: ${filePath}`);
  }
  
  switch (ext) {
    case '.md':
    case '.txt':
      const mdContent = fs.readFileSync(filePath, 'utf8');
      return parseMarkdownToSegments(mdContent);
      
    case '.json':
      const jsonContent = fs.readFileSync(filePath, 'utf8');
      return parseJsonToSegments(jsonContent);
      
    case '.html':
      const htmlContent = fs.readFileSync(filePath, 'utf8');
      return parseHtmlToSegments(htmlContent);
      
    case '.pdf':
      const pdfBuffer = fs.readFileSync(filePath);
      return await parsePdfToSegments(pdfBuffer);
      
    case '.docx':
      const docxBuffer = fs.readFileSync(filePath);
      return await parseDocxToSegments(docxBuffer);
      
    case '.xlsx':
    case '.xls':
      return parseXlsxToSegments(filePath);
      
    case '.pptx':
      return await parsePptxToSegments(filePath);
      
    case '.csv':
      return await parseCsvToSegments(filePath);
      
    default:
      throw new Error(`Extensión de archivo no soportada por el parser: ${ext}`);
  }
}
