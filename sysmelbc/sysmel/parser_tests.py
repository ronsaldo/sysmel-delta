import unittest
from .parsetree import *
from .parser import parseSourceString

class TestParser(unittest.TestCase):
    def parseSourceStringWithoutErrors(self, string: str) -> ParseTreeNode:
        ast = parseSourceString(string)
        self.assertTrue(ParseTreeErrorVisitor().checkAndPrintErrors(ast))
        return ast

    def testEmpty(self):
        ast = self.parseSourceStringWithoutErrors('')
        self.assertTrue(ast.isSequenceNode())

    def testApplication(self):
        node = self.parseSourceStringWithoutErrors("a()")
        self.assertTrue(node.isApplicationNode())
        self.assertTrue(node.functional.isIdentifierReferenceNode())
        self.assertEqual(node.functional.value, 'a')

        self.assertEqual(len(node.arguments), 0)

    def testApplication2(self):
        node = self.parseSourceStringWithoutErrors("a(42)")
        self.assertTrue(node.isApplicationNode())
        self.assertTrue(node.functional.isIdentifierReferenceNode())
        self.assertEqual(node.functional.value, 'a')

        self.assertEqual(len(node.arguments), 1)
        argument: ParseTreeNode = node.arguments[0]

        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 42)

    def testApplication3(self):
        node = self.parseSourceStringWithoutErrors("a(42. 5)")
        self.assertTrue(node.isApplicationNode())
        self.assertTrue(node.functional.isIdentifierReferenceNode())
        self.assertEqual(node.functional.value, 'a')

        self.assertEqual(len(node.arguments), 2)
        argument: ParseTreeNode = node.arguments[0]

        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 42)

        argument: ParseTreeNode = node.arguments[1]

        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 5)

    def testAssociation(self):
        node = self.parseSourceStringWithoutErrors("42 : 5")
        self.assertTrue(node.isTupleNode())
        self.assertEqual(len(node.elements), 2)

        element: ParseTreeLiteralIntegerNode = node.elements[0]
        self.assertTrue(element.isLiteralIntegerNode())
        self.assertEqual(element.value, 42)

        element: ParseTreeLiteralIntegerNode = node.elements[1]
        self.assertTrue(element.isLiteralIntegerNode())
        self.assertEqual(element.value, 5)

    def testTuple(self):
        node = self.parseSourceStringWithoutErrors("()")
        self.assertTrue(node.isTupleNode())
        self.assertEqual(len(node.elements), 0)

    def testTuple1(self):
        node = self.parseSourceStringWithoutErrors("42,")
        self.assertTrue(node.isTupleNode())
        self.assertEqual(len(node.elements), 1)

        element: ParseTreeLiteralIntegerNode = node.elements[0]
        self.assertTrue(element.isLiteralIntegerNode())
        self.assertEqual(element.value, 42)

    def testTuple2(self):
        node = self.parseSourceStringWithoutErrors("42, 5")
        self.assertTrue(node.isTupleNode())
        self.assertEqual(len(node.elements), 2)

        element: ParseTreeLiteralIntegerNode = node.elements[0]
        self.assertTrue(element.isLiteralIntegerNode())
        self.assertEqual(element.value, 42)

        element: ParseTreeLiteralIntegerNode = node.elements[1]
        self.assertTrue(element.isLiteralIntegerNode())
        self.assertEqual(element.value, 5)

    def testAssignment(self):
        node: ParseTreeAssignmentNode = self.parseSourceStringWithoutErrors("a := 42")
        self.assertTrue(node.isAssignmentNode())
        self.assertTrue(node.store.isIdentifierReferenceNode())
        self.assertEqual(node.store.value, 'a')

        self.assertTrue(node.value.isLiteralIntegerNode())
        self.assertEqual(node.value.value, 42)

    def testLiteralInteger(self):
        node = self.parseSourceStringWithoutErrors('42')
        self.assertTrue(node.isLiteralIntegerNode())
        self.assertEqual(node.value, 42)

        node = self.parseSourceStringWithoutErrors('2r1010')
        self.assertTrue(node.isLiteralIntegerNode())
        self.assertEqual(node.value, 0b1010)

        node = self.parseSourceStringWithoutErrors('16rC0DE')
        self.assertTrue(node.isLiteralIntegerNode())
        self.assertEqual(node.value, 0xC0DE)

    def testLiteralCharacter(self):
        node = self.parseSourceStringWithoutErrors("'A'")
        self.assertTrue(node.isLiteralCharacterNode())
        self.assertEqual(node.value, ord('A'))

    def testLiteralFloat(self):
        node = self.parseSourceStringWithoutErrors('42.5')
        self.assertTrue(node.isLiteralFloatNode())
        self.assertEqual(node.value, 42.5)

        node = self.parseSourceStringWithoutErrors('42.5e3')
        self.assertTrue(node.isLiteralFloatNode())
        self.assertEqual(node.value, 42.5e3)

    def testLiteralString(self):
        node = self.parseSourceStringWithoutErrors('"Hello World"')
        self.assertTrue(node.isLiteralStringNode())
        self.assertEqual(node.value, 'Hello World')

        node = self.parseSourceStringWithoutErrors('"Hello \\"World\\""')
        self.assertTrue(node.isLiteralStringNode())
        self.assertEqual(node.value, 'Hello "World"')

    def testLiteralSymbolIdentifier(self):
        node = self.parseSourceStringWithoutErrors("#symbol")
        self.assertTrue(node.isLiteralSymbolNode())
        self.assertEqual(node.value, 'symbol')

    def testLiteralSymbolKeyword(self):
        node = self.parseSourceStringWithoutErrors("#keyword:")
        self.assertTrue(node.isLiteralSymbolNode())
        self.assertEqual(node.value, 'keyword:')

        node = self.parseSourceStringWithoutErrors("#keyword:with:")
        self.assertTrue(node.isLiteralSymbolNode())
        self.assertEqual(node.value, 'keyword:with:')

    def testLiteralSymbolString(self):
        node = self.parseSourceStringWithoutErrors('#"Hello World"')
        self.assertTrue(node.isLiteralSymbolNode())
        self.assertEqual(node.value, 'Hello World')

        node = self.parseSourceStringWithoutErrors('#"Hello \\"World\\""')
        self.assertTrue(node.isLiteralSymbolNode())
        self.assertEqual(node.value, 'Hello "World"')

    def testIdentifierReference(self):
        node = self.parseSourceStringWithoutErrors("identifier")
        self.assertTrue(node.isIdentifierReferenceNode())
        self.assertEqual(node.value, 'identifier')

    def testBinaryExpressionSequence(self):
        node = self.parseSourceStringWithoutErrors("1 + 2")
        self.assertTrue(node.isBinaryExpressionSequenceNode())
        self.assertEqual(len(node.elements), 3)

        term: ParseTreeNode = node.elements[0]
        self.assertTrue(term.isLiteralIntegerNode())
        self.assertEqual(term.value, 1)

        operator: ParseTreeNode = node.elements[1]
        self.assertTrue(operator.isLiteralSymbolNode())
        self.assertEqual(operator.value, '+')

        term: ParseTreeNode = node.elements[2]
        self.assertTrue(term.isLiteralIntegerNode())
        self.assertEqual(term.value, 2)

    def testBinaryExpressionSequence(self):
        node = self.parseSourceStringWithoutErrors("1 + 2 * 4")
        self.assertTrue(node.isBinaryExpressionSequenceNode())
        self.assertEqual(len(node.elements), 5)

        term: ParseTreeNode = node.elements[0]
        self.assertTrue(term.isLiteralIntegerNode())
        self.assertEqual(term.value, 1)

        operator: ParseTreeNode = node.elements[1]
        self.assertTrue(operator.isLiteralSymbolNode())
        self.assertEqual(operator.value, '+')

        term: ParseTreeNode = node.elements[2]
        self.assertTrue(term.isLiteralIntegerNode())
        self.assertEqual(term.value, 2)

        operator: ParseTreeNode = node.elements[3]
        self.assertTrue(operator.isLiteralSymbolNode())
        self.assertEqual(operator.value, '*')

        term: ParseTreeNode = node.elements[4]
        self.assertTrue(term.isLiteralIntegerNode())
        self.assertEqual(term.value, 4)

    def testUnaryMessageSend(self):
        node = self.parseSourceStringWithoutErrors("a negated")
        self.assertTrue(node.isMessageSendNode())
        self.assertTrue(node.receiver.isIdentifierReferenceNode())
        self.assertEqual(node.receiver.value, 'a')

        self.assertTrue(node.selector.isLiteralSymbolNode())
        self.assertEqual(node.selector.value, 'negated')

        self.assertEqual(len(node.arguments), 0)

    def testKeywordMessageSend(self):
        node = self.parseSourceStringWithoutErrors("a perform: #yourself")
        self.assertTrue(node.isMessageSendNode())
        self.assertTrue(node.receiver.isIdentifierReferenceNode())
        self.assertEqual(node.receiver.value, 'a')

        self.assertTrue(node.selector.isLiteralSymbolNode())
        self.assertEqual(node.selector.value, 'perform:')

        self.assertEqual(len(node.arguments), 1)
        argument: ParseTreeNode = node.arguments[0]

        self.assertTrue(argument.isLiteralSymbolNode())
        self.assertEqual(argument.value, 'yourself')

    def testKeywordMessageSend2(self):
        node = self.parseSourceStringWithoutErrors("a perform: #doSomethingWith: with: 42")
        self.assertTrue(node.isMessageSendNode())
        self.assertTrue(node.receiver.isIdentifierReferenceNode())
        self.assertEqual(node.receiver.value, 'a')

        self.assertTrue(node.selector.isLiteralSymbolNode())
        self.assertEqual(node.selector.value, 'perform:with:')

        self.assertEqual(len(node.arguments), 2)

        argument: ParseTreeNode = node.arguments[0]
        self.assertTrue(argument.isLiteralSymbolNode())
        self.assertEqual(argument.value, 'doSomethingWith:')

        argument: ParseTreeNode = node.arguments[1]
        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 42)

    def testCascadeMessageSend(self):
        node = self.parseSourceStringWithoutErrors("a + 2; - 3; yourself")
        self.assertTrue(node.isMessageCascadeNode())
        self.assertTrue(node.receiver.isIdentifierReferenceNode())
        self.assertEqual(node.receiver.value, 'a')

        self.assertEqual(len(node.messages), 3)

        message: ParseTreeCascadeMessageNode = node.messages[0]
        self.assertTrue(message.selector.isLiteralSymbolNode())
        self.assertEqual(message.selector.value, '+')
        self.assertEqual(len(message.arguments), 1)

        argument: ParseTreeNode = message.arguments[0]
        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 2)

        message: ParseTreeCascadeMessageNode = node.messages[1]
        self.assertTrue(message.selector.isLiteralSymbolNode())
        self.assertEqual(message.selector.value, '-')
        self.assertEqual(len(message.arguments), 1)

        argument: ParseTreeNode = message.arguments[0]
        self.assertTrue(argument.isLiteralIntegerNode())
        self.assertEqual(argument.value, 3)

        message: ParseTreeCascadeMessageNode = node.messages[2]
        self.assertTrue(message.selector.isLiteralSymbolNode())
        self.assertEqual(message.selector.value, 'yourself')
        self.assertEqual(len(message.arguments), 0)

    def testQuasiQuote(self):
        node = self.parseSourceStringWithoutErrors("``42")
        self.assertTrue(node.isQuasiQuoteNode())
        self.assertTrue(node.term.isLiteralIntegerNode())
        self.assertEqual(node.term.value, 42)

    def testQuasiUnquote(self):
        node = self.parseSourceStringWithoutErrors("`,42")
        self.assertTrue(node.isQuasiUnquoteNode())
        self.assertTrue(node.term.isLiteralIntegerNode())
        self.assertEqual(node.term.value, 42)

    def testQuote(self):
        node = self.parseSourceStringWithoutErrors("`'42")
        self.assertTrue(node.isQuoteNode())
        self.assertTrue(node.term.isLiteralIntegerNode())
        self.assertEqual(node.term.value, 42)

    def testSplice(self):
        node = self.parseSourceStringWithoutErrors("`@42")
        self.assertTrue(node.isSpliceNode())
        self.assertTrue(node.term.isLiteralIntegerNode())
        self.assertEqual(node.term.value, 42)

if __name__ == '__main__':
    unittest.main()