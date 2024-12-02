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
        // Удаляем const без значения, чтобы избежать ошибок
        return code.replace(/const\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*;/g, '');
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
            throw new Error(`Parsing failed for ${filePath}: ${parseError.message}`);
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

            ClassDeclaration: (path) => {
                try {
                    const classNode = path.node;
                    if (!classNode.id) return;

                    const classData = {
                        name: classNode.id.name,
                        code: generator(classNode).code,
                        methods: [],
                        properties: [],
                    };

                    classNode.body.body.forEach((element) => {
                        if (element.type === 'ClassMethod') {
                            classData.methods.push({
                                name: element.key?.name || null,
                                kind: element.kind || null,
                                static: element.static || false,
                                code: generator(element).code,
                                start_line: element.loc?.start?.line || null,
                                end_line: element.loc?.end?.line || null,
                            });
                        } else if (element.type === 'ClassProperty') {
                            classData.properties.push({
                                name: element.key?.name || null,
                                type: element.typeAnnotation
                                    ? generator(element.typeAnnotation).code
                                    : null,
                                static: element.static || false,
                                default_value: element.value
                                    ? generator(element.value).code
                                    : null,
                            });
                        }
                    });

                    if (isTSX && this.isReactComponent(classNode)) {
                        this.result.react_components.push(classData);
                    } else {
                        this.result.classes.push(classData);
                    }
                } catch (e) {
                    console.error('Error processing ClassDeclaration:', e.message, path.node);
                }
            },

            ArrowFunctionExpression: (path) => {
                try {
                    if (isTSX && this.isReactComponent(path.parent)) {
                        const componentName =
                            path.parent.id?.name || 'AnonymousComponent';
                        this.result.react_components.push({
                            name: componentName,
                            code: generator(path.node).code,
                            props: this.extractPropsFromJSX(path),
                        });
                    }
                } catch (e) {
                    console.error('Error processing ArrowFunctionExpression:', e.message, path.node);
                }
            },

            FunctionExpression: (path) => {
                try {
                    if (isTSX && this.isReactComponent(path.parent)) {
                        const componentName =
                            path.parent.id?.name || 'AnonymousComponent';
                        this.result.react_components.push({
                            name: componentName,
                            code: generator(path.node).code,
                            props: this.extractPropsFromJSX(path),
                        });
                    }
                } catch (e) {
                    console.error('Error processing FunctionExpression:', e.message, path.node);
                }
            },
        });

        return this.result;
    }

    logNodeProcessing(node) {
        console.log(`Processing node of type: ${node.type}`);
    }

    isReactComponent(node) {
        return (
            node?.superClass?.name === 'Component' ||
            node?.superClass?.name === 'PureComponent' ||
            (node.type === 'VariableDeclarator' &&
                node.init?.type === 'ArrowFunctionExpression') ||
            (node.type === 'FunctionDeclaration' &&
                node.params?.some((param) => param.type === 'Identifier'))
        );
    }

    extractPropsFromJSX(path) {
        const props = [];
        traverse(path.node, {
            JSXAttribute(attributePath) {
                props.push({
                    name: attributePath.node.name?.name || null,
                    value: attributePath.node.value
                        ? generator(attributePath.node.value).code
                        : null,
                });
            },
        });
        return props;
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
