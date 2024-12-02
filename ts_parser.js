import fs from 'fs';
import path from 'path';
import * as babelParser from '@babel/parser';
import traverse from '@babel/traverse';
import generator from '@babel/generator';

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
                this.result.imports.push(path.node.source.value);
            },

            ExportNamedDeclaration: (path) => {
                if (path.node.declaration) {
                    const exportCode = generator(path.node.declaration).code;
                    this.result.exports.push({
                        name: path.node.declaration.id?.name || null,
                        type: path.node.declaration.type,
                        code: exportCode,
                    });
                } else {
                    path.node.specifiers.forEach((specifier) => {
                        this.result.exports.push({
                            name: specifier.exported.name,
                            code: null,
                        });
                    });
                }
            },

            ExportDefaultDeclaration: (path) => {
                const exportCode = generator(path.node.declaration).code;
                this.result.exports.push({
                    name: 'default',
                    type: path.node.declaration.type,
                    code: exportCode,
                });
            },

            TSInterfaceDeclaration: (path) => {
                const typeCode = generator(path.node).code;
                this.result.types.push({
                    name: path.node.id.name,
                    kind: 'interface',
                    code: typeCode,
                });
            },

            TSTypeAliasDeclaration: (path) => {
                const typeCode = generator(path.node).code;
                this.result.types.push({
                    name: path.node.id.name,
                    kind: 'type',
                    code: typeCode,
                });
            },

            FunctionDeclaration: (path) => {
                const functionNode = path.node;
                this.result.functions.push({
                    name: functionNode.id.name,
                    code: generator(functionNode).code,
                    start_line: functionNode.loc.start.line,
                    end_line: functionNode.loc.end.line,
                });
            },

            ClassDeclaration: (path) => {
                const classNode = path.node;
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
                            name: element.key.name,
                            kind: element.kind,
                            static: element.static || false,
                            code: generator(element).code,
                            start_line: element.loc.start.line,
                            end_line: element.loc.end.line,
                        });
                    } else if (element.type === 'ClassProperty') {
                        classData.properties.push({
                            name: element.key.name,
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
            node.superClass?.name === 'Component' ||
            node.superClass?.name === 'PureComponent' ||
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
                    name: attributePath.node.name.name,
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
