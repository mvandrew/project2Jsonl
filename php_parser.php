<?php
require 'vendor/autoload.php';

use PhpParser\ParserFactory;
use PhpParser\NodeTraverser;
use PhpParser\NodeVisitorAbstract;
use PhpParser\Node;

class DependencyVisitor extends NodeVisitorAbstract {
    public $dependencies = [];
    public $namespace = null;
    public $functions = [];
    public $classes = [];

    public function enterNode(Node $node) {
        if ($node instanceof Node\Stmt\Use_) {
            foreach ($node->uses as $use) {
                $this->dependencies[] = $use->name->toString();
            }
        }
        if ($node instanceof Node\Stmt\Namespace_) {
            $this->namespace = $node->name ? $node->name->toString() : null;
        }
        if ($node instanceof Node\Stmt\Class_) {
            $this->classes[] = $node->name ? $node->name->toString() : null;
        }
        if ($node instanceof Node\Stmt\Function_) {
            $this->functions[] = $node->name ? $node->name->toString() : null;
        }
    }
}

try {
    $file = $argv[1];
    $code = file_get_contents($file);

    $parserFactory = new ParserFactory();
    $parser = $parserFactory->createForHostVersion();

    $stmts = $parser->parse($code);

    $traverser = new NodeTraverser();
    $visitor = new DependencyVisitor();
    $traverser->addVisitor($visitor);
    $traverser->traverse($stmts);

    echo json_encode([
        'namespace' => $visitor->namespace,
        'dependencies' => $visitor->dependencies,
        'classes' => $visitor->classes,
        'functions' => $visitor->functions
    ], JSON_PRETTY_PRINT);
} catch (PhpParser\Error $e) {
    echo json_encode(['error' => $e->getMessage()]);
}
