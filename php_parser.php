<?php
require 'vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node;
use PhpParser\PrettyPrinter;

class DependencyVisitor extends NodeVisitorAbstract {
    public $dependencies = [];
    public $namespace = null;
    public $functions = [];
    public $classes = [];

    private $prettyPrinter;

    public function __construct() {
        // Используем PrettyPrinter для получения исходного кода
        $this->prettyPrinter = new PrettyPrinter\Standard();
    }

    public function enterNode(Node $node) {
        try {
            // Сбор зависимостей (use statements)
            if ($node instanceof Node\Stmt\Use_) {
                foreach ($node->uses as $use) {
                    $this->dependencies[] = $use->name->toString();
                }
            }

            // Сбор пространства имен
            if ($node instanceof Node\Stmt\Namespace_) {
                $this->namespace = $node->name ? $node->name->toString() : null;
            }

            // Сбор классов, их методов и свойств
            if ($node instanceof Node\Stmt\Class_) {
                $class_data = [
                    'name' => $node->name->toString(),
                    'code' => $this->prettyPrinter->prettyPrint([$node]),
                    'methods' => [], // Место для хранения методов
                    'properties' => [] // Место для хранения свойств
                ];

                // Извлекаем свойства класса
                foreach ($node->stmts as $stmt) {
                    if ($stmt instanceof Node\Stmt\Property) {
                        foreach ($stmt->props as $prop) {
                            $class_data['properties'][] = [
                                'name' => $prop->name->toString(),
                                'type' => $stmt->type ? $stmt->type->toString() : null,
                                'modifiers' => $this->getModifiers($stmt),
                                'default_value' => $prop->default ? $this->prettyPrinter->prettyPrintExpr($prop->default) : null
                            ];
                        }
                    }

                    // Извлекаем методы класса
                    if ($stmt instanceof Node\Stmt\ClassMethod) {
                        $class_data['methods'][] = [
                            'name' => $stmt->name->toString(),
                            'modifiers' => $this->getModifiers($stmt),
                            'code' => $this->prettyPrinter->prettyPrint([$stmt]),
                            'start_line' => $stmt->getStartLine(),
                            'end_line' => $stmt->getEndLine()
                        ];
                    }
                }

                $this->classes[] = $class_data;
            }

            // Сбор глобальных функций
            if ($node instanceof Node\Stmt\Function_) {
                $this->functions[] = [
                    'name' => $node->name->toString(),
                    'code' => $this->prettyPrinter->prettyPrint([$node]),
                    'start_line' => $node->getStartLine(),
                    'end_line' => $node->getEndLine()
                ];
            }
        } catch (Throwable $e) {
            // Логирование ошибок
            error_log("Error processing node: " . $e->getMessage());
            error_log("Node type: " . get_class($node));
        }
    }

    private function getModifiers($node) {
        // Извлекаем модификаторы (public, protected, private, static, etc.)
        $modifiers = [];
        if ($node instanceof Node\Stmt\ClassMethod || $node instanceof Node\Stmt\Property) {
            if ($node->isPublic()) $modifiers[] = 'public';
            if ($node->isProtected()) $modifiers[] = 'protected';
            if ($node->isPrivate()) $modifiers[] = 'private';
            if ($node->isStatic()) $modifiers[] = 'static';
        }
        return $modifiers;
    }
}

try {
    // Получаем путь к анализируемому файлу из аргументов
    $file = $argv[1];
    $code = file_get_contents($file);

    // Создаем парсер
    $parserFactory = new ParserFactory();
    $parser = $parserFactory->createForHostVersion();

    // Парсим исходный код
    $stmts = $parser->parse($code);

    // Создаем обходчик для анализа AST
    $traverser = new NodeTraverser();
    $visitor = new DependencyVisitor();
    $traverser->addVisitor($visitor);
    $traverser->traverse($stmts);

    // Вывод результатов в формате JSON
    echo json_encode([
        'namespace' => $visitor->namespace,
        'dependencies' => $visitor->dependencies,
        'classes' => $visitor->classes,
        'functions' => $visitor->functions
    ], JSON_PRETTY_PRINT);
} catch (PhpParser\Error $e) {
    // Вывод ошибок парсинга
    echo json_encode(['error' => $e->getMessage()]);
}
