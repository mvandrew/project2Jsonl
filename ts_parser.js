const fs = require('fs');
const path = require('path');
const babelParser = require('@babel/parser');
const traverse = require('@babel/traverse').default; // Использование .default для правильного экспорта
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

    parse(filePath) {
        // Считываем исходный код файла
        const code = fs.readFileSync(filePath, 'utf-8');

        // Определяем тип файла (tsx или ts)
        const isTSX = path.extname(filePath).toLowerCase() === '.tsx';

        // Парсим код с использованием Babel
        const ast = babelParser.parse(code, {
            sourceType: 'module',
            plugins: isTSX ? ['typescript', 'jsx'] : ['typescript'],
        });

        // Проходим по AST
        traverse(ast, {
            ImportDeclaration: (path) => {
                this.result.imports.push(path.node.source?.value || null);
            },

            ExportNamedDeclaration: (path) => {
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
            },

            ExportDefaultDeclaration: (path) => {
                const declaration = path.node.declaration;
                const exportCode = declaration ? generator(declaration).code : null;
                this.result.exports.push({
                    name: 'default',
                    type: declaration?.type || null,
                    code: exportCode,
                });
            },

            TSInterfaceDeclaration: (path) => {
                const typeCode = generator(path.node).code;
                this.result.types.push({
                    name: path.node.id?.name || null,
                    kind: 'interface',
                    code: typeCode,
                });
            },

            TSTypeAliasDeclaration: (path) => {
                const typeCode = generator(path.node).code;
                this.result.types.push({
                    name: path.node.id?.name || null,
                    kind: 'type',
                    code: typeCode,
                });
            },

            FunctionDeclaration: (path) => {
                const functionNode = path.node;
                if (functionNode.id) {
                    this.result.functions.push({
                        name: functionNode.id.name,
                        code: generator(functionNode).code,
                        start_line: functionNode.loc?.start?.line || null,
                        end_line: functionNode.loc?.end?.line || null,
                    });
                }
            },

            ClassDeclaration: (path) => {
                const classNode = path.node;
                if (!classNode.id) return; // Пропускаем анонимные классы

                const classData = {
                    name: classNode.id.name,
                    code: generator(classNode).code,
                    methods: [],
                    properties: [],
                };

                // Разбираем свойства и методы класса
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
            },

            ArrowFunctionExpression: (path) => {
                if (isTSX && this.isReactComponent(path.parent)) {
                    const componentName =
                        path.parent.id?.name || 'AnonymousComponent';
                    this.result.react_components.push({
                        name: componentName,
                        code: generator(path.node).code,
                        props: this.extractPropsFromJSX(path),
                    });
                }
            },

            FunctionExpression: (path) => {
                if (isTSX && this.isReactComponent(path.parent)) {
                    const componentName =
                        path.parent.id?.name || 'AnonymousComponent';
                    this.result.react_components.push({
                        name: componentName,
                        code: generator(path.node).code,
                        props: this.extractPropsFromJSX(path),
                    });
                }
            },
        });

        return this.result;
    }

    isReactComponent(node) {
        // Проверяем, является ли узел React-компонентом (классовый или функциональный)
        return (
            node?.superClass?.name === 'Component' ||
            node?.superClass?.name === 'PureComponent' ||
            (node.type === 'VariableDeclarator' &&
                node.init?.type === 'ArrowFunctionExpression') ||
            (node.type === 'FunctionDeclaration' &&
                node.params.some((param) => param.type === 'Identifier'))
        );
    }

    extractPropsFromJSX(path) {
        // Извлечение пропсов из JSX (для функциональных компонентов)
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

    // Выводим результат в формате JSON
    console.log(JSON.stringify(result, null, 4));
} catch (error) {
    console.error('Error parsing TypeScript/TSX file:', error.message);
    process.exit(1);
}
