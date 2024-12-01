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

        // Сбор классов и их методов
        if ($node instanceof Node\Stmt\Class_) {
            $class_data = [
                'name' => $node->name->toString(),
                'code' => $this->prettyPrinter->prettyPrint([$node]),
                'methods' => [] // Место для хранения методов
            ];

            // Извлекаем методы класса
            foreach ($node->stmts as $stmt) {
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
    }

    private function getModifiers(Node\Stmt\ClassMethod $method) {
        // Извлекаем модификаторы метода
        $modifiers = [];
        if ($method->isPublic()) $modifiers[] = 'public';
        if ($method->isProtected()) $modifiers[] = 'protected';
        if ($method->isPrivate()) $modifiers[] = 'private';
        if ($method->isStatic()) $modifiers[] = 'static';
        if ($method->isFinal()) $modifiers[] = 'final';
        if ($method->isAbstract()) $modifiers[] = 'abstract';
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

    // Создаем обхідник для анализа AST
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
