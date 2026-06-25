import * as fs from 'fs';
import * as path from 'path';
import pdfParse from 'pdf-parse';
import mammoth from 'mammoth';
import * as xlsx from 'xlsx';
import officeParser from 'officeparser';
import * as cheerio from 'cheerio';
import csvParser from 'csv-parser';

/**
 * Parsea un archivo HTML eliminando etiquetas y devolviendo texto plano limpio
 */
export function parseHtml(htmlContent: string): string {
  const $ = cheerio.load(htmlContent);
  // Eliminar scripts y estilos
  $('script, style').remove();
  return $('body').text().replace(/\s+/g, ' ').trim();
}

/**
 * Parsea un archivo PDF usando la librería pdf-parse
 */
export async function parsePdf(fileBuffer: Buffer): Promise<string> {
  const data = await pdfParse(fileBuffer);
  return data.text;
}

/**
 * Parsea un archivo de Word (.docx) convirtiendo a texto limpio usando mammoth
 */
export async function parseDocx(fileBuffer: Buffer): Promise<string> {
  const result = await mammoth.extractRawText({ buffer: fileBuffer });
  return result.value;
}

/**
 * Parsea hojas de cálculo Excel (.xlsx / .xls) convirtiendo todas las filas a formato de texto plano estructurado
 */
export function parseXlsx(filePath: string): string {
  const workbook = xlsx.readFile(filePath);
  let textOutput = '';
  
  for (const sheetName of workbook.SheetNames) {
    textOutput += `\n--- Hoja: ${sheetName} ---\n`;
    const worksheet = workbook.Sheets[sheetName];
    // Convertir a formato texto legible (CSV temporal)
    const csvData = xlsx.utils.sheet_to_csv(worksheet);
    textOutput += csvData;
  }
  
  return textOutput;
}

/**
 * Parsea presentaciones de PowerPoint (.pptx) extrayendo el texto de las diapositivas
 */
export async function parsePptx(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    officeParser.parseOffice(filePath, (data: any, err: any) => {
      if (err) {
        reject(err);
      } else {
        resolve(data);
      }
    });
  });
}

/**
 * Parsea archivos CSV a formato de texto representativo
 */
export async function parseCsv(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const results: any[] = [];
    fs.createReadStream(filePath)
      .pipe(csvParser())
      .on('data', (data) => results.push(data))
      .on('end', () => {
        // Convertir el JSON de resultados a texto estructurado por filas
        const formattedRows = results.map(row => 
          Object.entries(row).map(([key, val]) => `${key}: ${val}`).join(' | ')
        ).join('\n');
        resolve(formattedRows);
      })
      .on('error', (err) => reject(err));
  });
}

/**
 * Orquestador principal de parsing: Identifica la extensión del archivo
 * y aplica el procesador correspondiente para retornar texto limpio.
 */
export async function extractTextFromFile(filePath: string): Promise<string> {
  const ext = path.extname(filePath).toLowerCase();
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`El archivo no existe en la ruta: ${filePath}`);
  }
  
  switch (ext) {
    case '.md':
    case '.txt':
      return fs.readFileSync(filePath, 'utf8');
      
    case '.json':
      const jsonContent = fs.readFileSync(filePath, 'utf8');
      // Intentar formatear el JSON para que el agente lo entienda estructuralmente
      const jsonObj = JSON.parse(jsonContent);
      return JSON.stringify(jsonObj, null, 2);
      
    case '.html':
      const htmlContent = fs.readFileSync(filePath, 'utf8');
      return parseHtml(htmlContent);
      
    case '.pdf':
      const pdfBuffer = fs.readFileSync(filePath);
      return await parsePdf(pdfBuffer);
      
    case '.docx':
      const docxBuffer = fs.readFileSync(filePath);
      return await parseDocx(docxBuffer);
      
    case '.xlsx':
    case '.xls':
      return parseXlsx(filePath);
      
    case '.pptx':
      return await parsePptx(filePath);
      
    case '.csv':
      return await parseCsv(filePath);
      
    default:
      throw new Error(`Extensión de archivo no soportada en la ingesta del agente: ${ext}`);
  }
}
