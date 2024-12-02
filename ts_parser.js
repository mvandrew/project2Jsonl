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
        // Удаляем const без значения
        code = code.replace(/const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*;/g, 'let $1;');
        // Удаляем любые декларации `export const` без инициализаторов
        code = code.replace(/export\s+const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*;/g, 'export let $1;');
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
            throw new Error(`Parsing failed for ${filePath}: ${parseError.message}`);
        }

        const self = this; // Сохраняем контекст this для traverse

        traverse(ast, {
            ImportDeclaration(path) {
                self.result.imports.push(path.node.source?.value || null);
            },

            ExportNamedDeclaration(path) {
                const declaration = path.node.declaration;
                if (declaration) {
                    const exportCode = generator(declaration).code;
                    self.result.exports.push({
                        name: declaration.id?.name || null,
                        type: declaration.type || null,
                        code: exportCode,
                    });
                } else {
                    path.node.specifiers.forEach((specifier) => {
                        self.result.exports.push({
                            name: specifier.exported?.name || null,
                            code: null,
                        });
                    });
                }
            },

            ExportDefaultDeclaration(path) {
                const declaration = path.node.declaration;
                const exportCode = declaration ? generator(declaration).code : null;
                self.result.exports.push({
                    name: 'default',
                    type: declaration?.type || null,
                    code: exportCode,
                });
            },

            TSInterfaceDeclaration(path) {
                if (path.node.id?.name) {
                    const typeCode = generator(path.node).code;
                    self.result.types.push({
                        name: path.node.id.name,
                        kind: 'interface',
                        code: typeCode,
                    });
                }
            },

            TSTypeAliasDeclaration(path) {
                if (path.node.id?.name) {
                    const typeCode = generator(path.node).code;
                    self.result.types.push({
                        name: path.node.id.name,
                        kind: 'type',
                        code: typeCode,
                    });
                }
            },

            FunctionDeclaration(path) {
                const functionNode = path.node;
                if (functionNode.id) {
                    self.result.functions.push({
                        name: functionNode.id.name,
                        code: generator(functionNode).code,
                        start_line: functionNode.loc?.start?.line || null,
                        end_line: functionNode.loc?.end?.line || null,
                    });
                }
            },
        });

        return this.result;
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

    // Выводим только результат парсинга
    console.log(JSON.stringify(result, null, 4));
} catch (error) {
    console.error(JSON.stringify({ error: error.message }));
    process.exit(1);
}
