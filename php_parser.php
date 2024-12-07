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
    public $classes = [];
    public $functions = [];

    private $prettyPrinter;
    private $currentClass = null;

    public function __construct() {
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

            // Сбор классов
            if ($node instanceof Node\Stmt\Class_) {
                // Сохраняем текущий класс
                $this->currentClass = [
                    'name' => $node->name->toString(),
                    'code' => $this->prettyPrinter->prettyPrint([$node]),
                    'methods' => [],
                    'properties' => []
                ];
            }

            // Сбор свойств текущего класса
            if ($this->currentClass && $node instanceof Node\Stmt\Property) {
                foreach ($node->props as $prop) {
                    $this->currentClass['properties'][] = [
                        'name' => $prop->name->toString(),
                        'type' => $node->type ? $node->type->toString() : null,
                        'modifiers' => $this->getModifiers($node),
                        'default_value' => $prop->default ? $this->prettyPrinter->prettyPrintExpr($prop->default) : null
                    ];
                }
            }

            // Сбор методов текущего класса
            if ($this->currentClass && $node instanceof Node\Stmt\ClassMethod) {
                $this->currentClass['methods'][] = [
                    'name' => $node->name->toString(),
                    'modifiers' => $this->getModifiers($node),
                    'code' => $this->prettyPrinter->prettyPrint([$node]),
                    'start_line' => $node->getStartLine(),
                    'end_line' => $node->getEndLine()
                ];
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
            error_log("Error processing node: " . $e->getMessage());
            error_log("Node type: " . get_class($node));
        }
    }

    public function leaveNode(Node $node) {
        // Завершение обработки класса
        if ($node instanceof Node\Stmt\Class_) {
            $this->classes[] = $this->currentClass;
            $this->currentClass = null; // Сброс текущего класса
        }
    }

    private function getModifiers($node) {
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
