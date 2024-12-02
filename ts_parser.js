const fs = require('fs');
const path = require('path');
const babelParser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generator = require('@babel/generator').default;

/**
 * Парсер TypeScript и TSX файлов.
 */
class TsParser {
    constructor() {
        this.result = {
            namespace: null,
            imports: [],
            exports: [],
            types: [],
            functions: [],
            classes: [],
            react_components: [],
        };
    }

    preprocessCode(code) {
        console.log("Preprocessing code...");
        // Удаляем const без значения
        code = code.replace(/const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*;/g, 'let $1;');
        // Удаляем любые декларации `export const` без инициализаторов
        code = code.replace(/export\s+const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*;/g, 'export let $1;');
        console.log("Code after preprocessing:", code.slice(0, 300)); // Лог первых 300 символов
        return code;
    }

    parse(filePath) {
        let code = fs.readFileSync(filePath, 'utf-8');
        code = this.preprocessCode(code); // Применяем предобработку кода
        const isTSX = path.extname(filePath).toLowerCase() === '.tsx';

        let ast;
        try {
            ast = babelParser.parse(code, {
                sourceType: 'module',
                plugins: isTSX ? ['typescript', 'jsx'] : ['typescript'],
            });
        } catch (parseError) {
            console.error(
                `Error parsing file: ${filePath}`,
                parseError.message,
                parseError.loc
                    ? ` at line ${parseError.loc.line}, column ${parseError.loc.column}`
                    : ''
            );

            // Дополнительная обработка проблемы
            if (parseError.message.includes('Missing initializer in const declaration')) {
                console.warn(`Attempting to fix missing const initializer in ${filePath}`);
                code = this.fixConstDeclarations(code);
                try {
                    ast = babelParser.parse(code, {
                        sourceType: 'module',
                        plugins: isTSX ? ['typescript', 'jsx'] : ['typescript'],
                    });
                } catch (secondaryError) {
                    console.error(`Secondary parse error: ${secondaryError.message}`);
                    throw new Error(`Parsing failed for ${filePath}: ${secondaryError.message}`);
                }
            } else {
                throw new Error(`Parsing failed for ${filePath}: ${parseError.message}`);
            }
        }

        traverse(ast, {
            enter(path) {
                try {
                    this.logNodeProcessing(path.node);
                } catch (e) {
                    console.error('Error logging node:', e.message);
                }
            },

            ImportDeclaration: (path) => {
                try {
                    this.result.imports.push(path.node.source?.value || null);
                } catch (e) {
                    console.error('Error processing ImportDeclaration:', e.message, path.node);
                }
            },

            ExportNamedDeclaration: (path) => {
                try {
                    const declaration = path.node.declaration;
                    if (declaration) {
                        const exportCode = generator(declaration).code;
                        this.result.exports.push({
                            name: declaration.id?.name || null,
                            type: declaration.type || null,
                            code: exportCode,
                        });
                    } else {
                        path.node.specifiers.forEach((specifier) => {
                            this.result.exports.push({
                                name: specifier.exported?.name || null,
                                code: null,
                            });
                        });
                    }
                } catch (e) {
                    console.error('Error processing ExportNamedDeclaration:', e.message, path.node);
                }
            },

            ExportDefaultDeclaration: (path) => {
                try {
                    const declaration = path.node.declaration;
                    const exportCode = declaration ? generator(declaration).code : null;
                    this.result.exports.push({
                        name: 'default',
                        type: declaration?.type || null,
                        code: exportCode,
                    });
                } catch (e) {
                    console.error('Error processing ExportDefaultDeclaration:', e.message, path.node);
                }
            },

            TSInterfaceDeclaration: (path) => {
                try {
                    if (path.node.id?.name) {
                        const typeCode = generator(path.node).code;
                        this.result.types.push({
                            name: path.node.id.name,
                            kind: 'interface',
                            code: typeCode,
                        });
                    }
                } catch (e) {
                    console.error('Error processing TSInterfaceDeclaration:', e.message, path.node);
                }
            },

            TSTypeAliasDeclaration: (path) => {
                try {
                    if (path.node.id?.name) {
                        const typeCode = generator(path.node).code;
                        this.result.types.push({
                            name: path.node.id.name,
                            kind: 'type',
                            code: typeCode,
                        });
                    }
                } catch (e) {
                    console.error('Error processing TSTypeAliasDeclaration:', e.message, path.node);
                }
            },

            FunctionDeclaration: (path) => {
                try {
                    const functionNode = path.node;
                    if (functionNode.id) {
                        this.result.functions.push({
                            name: functionNode.id.name,
                            code: generator(functionNode).code,
                            start_line: functionNode.loc?.start?.line || null,
                            end_line: functionNode.loc?.end?.line || null,
                        });
                    }
                } catch (e) {
                    console.error('Error processing FunctionDeclaration:', e.message, path.node);
                }
            },
        });

        return this.result;
    }

    fixConstDeclarations(code) {
        return code.replace(/const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*;/g, 'let $1;');
    }

    logNodeProcessing(node) {
        console.log(`Processing node of type: ${node.type}`);
    }
}

// Получаем путь к анализируемому файлу
const filePath = process.argv[2];

if (!filePath || !fs.existsSync(filePath)) {
    console.error('Error: File path is invalid or does not exist.');
    process.exit(1);
}

try {
    const parser = new TsParser();
    const result = parser.parse(filePath);

    console.log(JSON.stringify(result, null, 4));
} catch (error) {
    console.error('Error parsing TypeScript/TSX file:', error.message);
    process.exit(1);
}
