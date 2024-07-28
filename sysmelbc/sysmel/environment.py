from .mop import *
from .syntax import *
from .asg import *
from .module import *

class ASGEnvironment(ABC):
    @abstractmethod
    def getTopLevelTargetEnvironment(self):
        pass

    @abstractmethod
    def lookSymbolBindingListRecursively(self, symbol: str):
        pass

    @abstractmethod
    def findCurrentLoopBodyEntryNode(self) -> ASGNode:
        pass
    
    @abstractmethod
    def addBreakNodeToCurrentLoop(self, node: ASGLoopBreakNode):
        pass

    @abstractmethod
    def addContinueNodeToCurrentLoop(self, node: ASGLoopContinueNode):
        pass

    def isLexicalEnvironment(self):
        return False

    def isScriptEnvironment(self):
        return False
    
    def childWithSymbolBinding(self, symbol: str, binding: ASGNode):
        return ASGChildEnvironmentWithBindings(self).childWithSymbolBinding(symbol, binding)
    
    @abstractmethod
    def getCompilationTarget(self):
        pass

class ASGMacroContext(ASGNode):
    derivation = ASGNodeDataAttribute(ASGNodeDerivation)
    expander = ASGNodeDataAttribute(object)

class ASGTopLevelTargetEnvironment(ASGEnvironment):
    def __init__(self, target: CompilationTarget) -> None:
        super().__init__()
        self.target = target
        self.symbolTable = {}
        self.typeUniverseIndexCache = {}
        topLevelDerivation = ASGNodeNoDerivation.getSingleton()
        self.topLevelUnificationTable = {}
        self.addBaseType(ASGIntegerTypeNode(topLevelDerivation, 'Integer'))
        self.addBaseType(ASGBottomTypeNode(topLevelDerivation, 'Abort'))
        voidType = self.addBaseType(ASGUnitTypeNode(topLevelDerivation, 'Void'))
        self.addBaseType(ASGSymbolTypeNode(topLevelDerivation, 'Symbol'))
        falseType = self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'False'))
        trueType = self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'True'))
        self.addBaseType(ASGSumTypeNode(topLevelDerivation, [falseType, trueType], 'Boolean'))
        self.addBaseType(ASGAnyTypeUniverseNode(topLevelDerivation, 'Type'))
        char8Type = self.addBaseType(ASGPrimitiveCharacterTypeNode(topLevelDerivation, 'Char8',  1, 1))
        self.addBaseType(ASGPrimitiveCharacterTypeNode(topLevelDerivation, 'Char16', 2, 2))
        self.addBaseType(ASGPrimitiveCharacterTypeNode(topLevelDerivation, 'Char32', 4, 4))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'Int8',  1, 1, True))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'Int16', 2, 2, True))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'Int32', 4, 4, True))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'Int64', 8, 8, True))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'UInt8',  1, 1, False))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'UInt16', 2, 2, False))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'UInt32', 4, 4, False))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'UInt64', 8, 8, False))
        sizeType = self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'Size', target.sizeSize, target.sizeAlignment, False))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'SignedSize', target.sizeSize, target.sizeAlignment, True))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'UIntPointer', target.pointerSize, target.pointerAlignment, False))
        self.addBaseType(ASGPrimitiveIntegerTypeNode(topLevelDerivation, 'IntPointer', target.pointerSize, target.pointerAlignment, True))
        self.addBaseType(ASGPrimitiveFloatTypeNode(topLevelDerivation, 'Float32', 4, 4))
        self.addBaseType(ASGPrimitiveFloatTypeNode(topLevelDerivation, 'Float64', 8, 8))
        self.addBaseType(ASGPrimitiveCVarArgTypeNode(topLevelDerivation, 'CVarArg'))

        self.addBaseType(ASGModuleTypeNode(topLevelDerivation, 'Module'))
        self.addBaseType(ASGMetaType(topLevelDerivation, 'ASGNode', ASGNode))
        self.addBaseType(ASGMetaType(topLevelDerivation, 'MacroContext', ASGMacroContext))
        self.addSymbolValue('void', ASGLiteralUnitNode(topLevelDerivation, voidType))
        self.addSymbolValue('false', ASGLiteralUnitNode(topLevelDerivation, falseType))
        self.addSymbolValue('true', ASGLiteralUnitNode(topLevelDerivation, trueType))

        char8PointerType = self.addUnificationValue(ASGPointerTypeNode(topLevelDerivation, char8Type))
        self.addBaseType(ASGStringTypeNode(topLevelDerivation, [char8PointerType, sizeType], 'String', ('elements', 'size')))

        self.addBaseType(ASGMirVoidTypeNode(topLevelDerivation, 'MIR::Void', 0, 1))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Boolean', 1, 1))

        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Int8',  1, 1))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Int16', 2, 2))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Int32', 4, 4))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Int64', 8, 8))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::UInt8',  1, 1))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::UInt16', 2, 2))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::UInt32', 4, 4))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::UInt64', 8, 8))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Float32', 4, 4))
        self.addBaseType(ASGMirBaseTypeNode(topLevelDerivation, 'MIR::Float64', 8, 8))
        self.addBaseType(ASGMirCVarArgTypeNode(topLevelDerivation, 'MIR::CVarArg', target.pointerSize, target.pointerAlignment))
        self.addBaseType(ASGMirTypeUniverseNode(topLevelDerivation, 'MIR::Type', target.pointerSize, target.pointerAlignment))

        self.addPrimitiveFunctions()
        self.gcmCache = {}
        self.interpreterCache = {}

    def addBaseType(self, baseType: ASGBaseTypeNode):
        baseType = self.addUnificationValue(baseType)
        self.addSymbolValue(baseType.name, baseType)
        return baseType

    def addUnificationValue(self, value: ASGNode):
        comparisonValue = ASGUnificationComparisonNode(value)
        if comparisonValue in self.topLevelUnificationTable:
            return self.topLevelUnificationTable[comparisonValue]
        else:
            self.topLevelUnificationTable[comparisonValue] = value
            return value

    def addSymbolValue(self, name: str, value: ASGNode):
        if name is not None:
            self.symbolTable[name] = [value] + self.symbolTable.get(name, [])

    def lookLastBindingOf(self, name: str):
        if not name in self.symbolTable:
            return None
        return self.symbolTable[name][0]
    
    def lookValidLastBindingOf(self, name: str):
        if not name in self.symbolTable:
            raise Exception('Missing required binding for %s.' % name)
        return self.symbolTable[name][0]

    def getMirTypeUniverse(self):
        return self.lookValidLastBindingOf('MIR::Type')

    def getTopLevelTargetEnvironment(self):
        return self
    
    def getCompilationTarget(self):
        return self.target
    
    def getTypeUniverseWithIndex(self, index):
        if index in self.typeUniverseIndexCache:
            return self.typeUniverseIndexCache[index]
        
        universe = ASGTypeUniverseNode(ASGNodeNoDerivation.getSingleton(), index)
        self.typeUniverseIndexCache[index] = universe
        return universe

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, [])

    @classmethod
    def getForTarget(cls, target: CompilationTarget):
        if hasattr(target, 'asgTopLevelTargetEnvironment'):
            return target.asgTopLevelTargetEnvironment

        topLevelEnvironment = cls(target)
        target.asgTopLevelTargetEnvironment = topLevelEnvironment
        return topLevelEnvironment
    
    def makeFunctionType(self, argumentTypes: list[ASGNode], resultType: ASGNode, isMacro = False, isPure = False):
        if isMacro:
            return self.addUnificationValue(ASGMacroFunctionTypeNode(ASGNodeNoDerivation.getSingleton(), argumentTypes, resultType))
        else:
            return self.addUnificationValue(ASGFunctionTypeNode(ASGNodeNoDerivation.getSingleton(), argumentTypes, resultType, pure = isPure))
    
    def makeFunctionTypeWithSignature(self, signature, isMacro = False, isPure = False):
        arguments, resultType = signature
        arguments = list(map(self.lookValidLastBindingOf, arguments))
        resultType = self.lookValidLastBindingOf(resultType)
        return self.makeFunctionType(arguments, resultType, isMacro = isMacro, isPure = isPure)

    def addPrimitiveFunctions(self):
        self.addModuleMacros()
        self.addControlFlowMacros()
        self.addTypeConstructors()
        self.addPrimitiveTypeFunctions()

    def addModuleMacros(self):
        self.addPrimitiveFunctionsWithDesc([
            ('fromExternal:import:withType:', 'Module::fromExternal:import:withType:',  (('ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.fromExternalImportWithTypeMacro),
            ('fromExternal:import:as:withType:', 'Module::fromExternal:import:as:withType:',  (('ASGNode', 'ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.fromExternalImportAsWithTypeMacro),
            ('external:export:', 'Module::external:export:',  (('ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.externalExportMacro),
            ('export:', 'Module::export:',  (('ASGNode',), 'ASGNode'),  ['macro'], self.exportMacro),
        ])

    def fromExternalImportWithTypeMacro(self, macroContext: ASGMacroContext, externalName: ASGNode, nameExpression: ASGNode, typeExpression: ASGNode):
        return self.fromExternalImportAsWithTypeMacro(macroContext, externalName, nameExpression, nameExpression, typeExpression)

    def fromExternalImportAsWithTypeMacro(self, macroContext: ASGMacroContext, externalName: ASGNode, nameExpression: ASGNode, importedNameExpression: ASGNode, typeExpression: ASGNode):
        return ASGSyntaxBindingDefinitionNode(macroContext.derivation, None, nameExpression,
            ASGSyntaxFromExternalImportNode(macroContext.derivation, externalName, importedNameExpression, typeExpression)
        )

    def externalExportMacro(self, macroContext: ASGMacroContext, externalName: ASGNode, exportedExpressions: ASGNode):
        return exportedExpressions.withContextExpandAsExportWithExternalName(macroContext, externalName)

    def exportMacro(self, macroContext: ASGMacroContext, exportedExpressions: ASGNode):
        return self.externalExportMacro(macroContext, None, exportedExpressions)

    def addControlFlowMacros(self):
        self.addPrimitiveFunctionsWithDesc([
            ('if:then:',  'ControlFlow::if:then:',  (('ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.ifThenMacro),
            ('if:then:else:',  'ControlFlow::if:then:',  (('ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.ifThenElseMacro),
            ('do:while:',  'ControlFlow::do:while:',  (('ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.doWhileMacro),
            ('do:continueWith:while:',  'ControlFlow::do:continueWith:while:',  (('ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.doContinueWithWhileMacro),
            ('while:do:',  'ControlFlow::while:do:',  (('ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.whileDoMacro),
            ('while:do:continueWith:',  'ControlFlow::while:do:continueWith:',  (('ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.whileDoContinueWithMacro),
        ])

    def ifThenMacro(self, macroContext: ASGMacroContext, condition: ASGNode, ifTrue: ASGNode) -> ASGNode:
        return ASGSyntaxIfThenElseNode(macroContext.derivation, condition, ifTrue, None)

    def ifThenElseMacro(self, macroContext: ASGMacroContext, condition: ASGNode, ifTrue: ASGNode, ifFalse: ASGNode) -> ASGNode:
        return ASGSyntaxIfThenElseNode(macroContext.derivation, condition, ifTrue, ifFalse)

    def doWhileMacro(self, macroContext: ASGMacroContext, body: ASGNode, condition: ASGNode) -> ASGNode:
        return ASGSyntaxDoContinueWithWhileNode(macroContext.derivation, body, None, condition)

    def doContinueWithWhileMacro(self, macroContext: ASGMacroContext, body: ASGNode, continueNode: ASGNode, condition: ASGNode) -> ASGNode:
        return ASGSyntaxDoContinueWithWhileNode(macroContext.derivation, body, continueNode, condition)

    def whileDoMacro(self, macroContext: ASGMacroContext, condition: ASGNode, body: ASGNode) -> ASGNode:
        return ASGSyntaxWhileDoContinueWithNode(macroContext.derivation, condition, body, None)

    def whileDoContinueWithMacro(self, macroContext: ASGMacroContext, condition: ASGNode, body: ASGNode, continueNode: ASGNode) -> ASGNode:
        return ASGSyntaxWhileDoContinueWithNode(macroContext.derivation, condition, body, continueNode)

    def addTypeConstructors(self):
        self.addPrimitiveFunctionsWithDesc([
            ('mutable', 'Type::mutable', (('Type',), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGDecoratedTypeNode.mutableConstructorImpl),
            ('volatile', 'Type::volatile', (('Type',), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGDecoratedTypeNode.volatileConstructorImpl),
            ('array:', 'Type::array:', (('Type', 'Size'), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGArrayTypeNode.constructorImpl),
            ('[]:', 'Type::array:', (('Type', 'Size'), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGArrayTypeNode.constructorImpl),
            ('pointer', 'Type::pointer', (('Type',), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGPointerTypeNode.constructorImpl),
            ('ref', 'Type::pointer', (('Type',), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGReferenceTypeNode.constructorImpl),
            ('tempRef', 'Type::pointer', (('Type',), 'Type'),  ['compileTime', 'pure', 'alwaysInline'], ASGTemporaryReferenceTypeNode.constructorImpl),
        ])

    def findCurrentLoopBodyEntryNode(self) -> ASGNode:
        return None
    
    def addBreakNodeToCurrentLoop(self, node: ASGLoopBreakNode):
        raise Exception("Not in a loop")

    def addContinueNodeToCurrentLoop(self, node: ASGLoopContinueNode):
        raise Exception("Not in a loop")

    def addPrimitiveTypeFunctions(self):
        primitiveCharacterTypes = list(map(self.lookValidLastBindingOf, [
            'Char8', 'Char16', 'Char32'
        ]))
        primitiveIntegerTypes = list(map(self.lookValidLastBindingOf, [
            'Int8',  'Int16',  'Int32',  'Int64',
            'UInt8', 'UInt16', 'UInt32', 'UInt64',
        ]))
        primitiveFloatTypes = list(map(self.lookValidLastBindingOf, ['Float32', 'Float64']))
        numberTypes = list(map(self.lookValidLastBindingOf, ['Integer'])) + primitiveCharacterTypes + primitiveIntegerTypes + primitiveFloatTypes
        literalNumberTypes = list(map(self.lookValidLastBindingOf, ['Integer', 'Char32', 'Float64']))

        booleanNot = lambda derivation, resultType, operand: resultType.makeBooleanWithValue(derivation, not operand.value)
        booleanAnd = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value and right.value)
        booleanOr = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value or right.value)
        booleanXor = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value ^ right.value)

        negated = lambda derivation, resultType, operand: resultType.makeLiteralWithValue(derivation, -operand.value)
        bitInvert = lambda derivation, resultType, operand: resultType.makeLiteralWithValue(derivation, ~operand.value)

        plus = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value + right.value)
        minus = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value - right.value)
        times = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value * right.value)

        minWith = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, min(left.value, right.value))
        maxWith = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, max(left.value, right.value))

        bitAnd = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value & right.value)
        bitOr = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value | right.value)
        bitXor = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value ^ right.value)
        shiftLeft = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value << right.value)
        shiftRight = lambda derivation, resultType, left, right: resultType.makeLiteralWithValue(derivation, left.value >> right.value)

        equals = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value == right.value)
        notEquals = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value != right.value)
        lessThan = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value < right.value)
        lessOrEquals = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value <= right.value)
        greaterThan = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value > right.value)
        greaterOrEquals = lambda derivation, resultType, left, right: resultType.makeBooleanWithValue(derivation, left.value >= right.value)

        castToCharacter = lambda derivation, resultType, value: ASGLiteralCharacterNode(derivation, resultType, resultType.normalizeValue(int(value.value)))
        castToInteger = lambda derivation, resultType, value: ASGLiteralIntegerNode(derivation, resultType, resultType.normalizeValue(int(value.value)))
        castToFloat = lambda derivation, resultType, value: ASGLiteralFloatNode(derivation, resultType, resultType.normalizeValue(float(value.value)))

        self.addPrimitiveFunctionsWithDesc([
            ('not', 'Boolean::not', (('Boolean',), 'Boolean'),  ['compileTime', 'pure'], booleanNot),

            ('&', 'Boolean::&', (('Boolean', 'Boolean'), 'Boolean'),  ['compileTime', 'pure'], booleanAnd),
            ('|', 'Boolean::|', (('Boolean', 'Boolean'), 'Boolean'),  ['compileTime', 'pure'], booleanOr),
            ('^', 'Boolean::^', (('Boolean', 'Boolean'), 'Boolean'),  ['compileTime', 'pure'], booleanXor),
        ])

        for numberType in numberTypes:
            name = numberType.name
            namePrefix = numberType.name + '::'

            self.addPrimitiveFunctionsWithDesc([
                ('negated', namePrefix + 'negated', ((name,), name),  ['compileTime', 'pure'], negated),

                ('+', namePrefix + '+', ((name, name), name),  ['compileTime', 'pure'], plus),
                ('-', namePrefix + '-', ((name, name), name),  ['compileTime', 'pure'], minus),
                ('*', namePrefix + '*', ((name, name), name),  ['compileTime', 'pure'], times),

                ('min:', namePrefix + 'min:', ((name, name), name),  ['compileTime', 'pure'], minWith),
                ('max:', namePrefix + 'max:', ((name, name), name),  ['compileTime', 'pure'], maxWith),

                ('=',  namePrefix + '=',  ((name, name), 'Boolean'),  ['compileTime', 'pure'], equals),
                ('~=', namePrefix + '~=', ((name, name), 'Boolean'),  ['compileTime', 'pure'], notEquals),
                ('<',  namePrefix + '<',  ((name, name), 'Boolean'),  ['compileTime', 'pure'], lessThan),
                ('<=', namePrefix + '<=', ((name, name), 'Boolean'),  ['compileTime', 'pure'], lessOrEquals),
                ('>',  namePrefix + '>',  ((name, name), 'Boolean'),  ['compileTime', 'pure'], greaterThan),
                ('>=', namePrefix + '>=', ((name, name), 'Boolean'),  ['compileTime', 'pure'], greaterOrEquals),

                ('asChar8',  namePrefix + 'asChar8',  ((name,), 'Char8'),  ['compileTime', 'pure'], castToCharacter),
                ('asChar16', namePrefix + 'asChar16', ((name,), 'Char16'), ['compileTime', 'pure'], castToCharacter),
                ('asChar32', namePrefix + 'asChar32', ((name,), 'Char32'), ['compileTime', 'pure'], castToCharacter),

                ('asInt8',  namePrefix + 'asInt8',  ((name,), 'Int8'),  ['compileTime', 'pure'], castToInteger),
                ('asInt16', namePrefix + 'asInt16', ((name,), 'Int16'), ['compileTime', 'pure'], castToInteger),
                ('asInt32', namePrefix + 'asInt32', ((name,), 'Int32'), ['compileTime', 'pure'], castToInteger),
                ('asInt64', namePrefix + 'asInt64', ((name,), 'Int64'), ['compileTime', 'pure'], castToInteger),

                ('asUInt8',  namePrefix + 'asUInt8',  ((name,), 'UInt8'),  ['compileTime', 'pure'], castToInteger),
                ('asUInt16', namePrefix + 'asUInt16', ((name,), 'UInt16'), ['compileTime', 'pure'], castToInteger),
                ('asUInt32', namePrefix + 'asUInt32', ((name,), 'UInt32'), ['compileTime', 'pure'], castToInteger),
                ('asUInt64', namePrefix + 'asUInt64', ((name,), 'UInt64'), ['compileTime', 'pure'], castToInteger),

                ('asSize',        namePrefix + 'asSize',        ((name,), 'Size'),        ['compileTime', 'pure'], castToInteger),
                ('asSignedSize',  namePrefix + 'asSignedSize',  ((name,), 'SignedSize'),  ['compileTime', 'pure'], castToInteger),
                ('asIntPointer',  namePrefix + 'asIntPointer',  ((name,), 'IntPointer'),  ['compileTime', 'pure'], castToInteger),
                ('asUIntPointer', namePrefix + 'asUIntPointer', ((name,), 'UIntPointer'), ['compileTime', 'pure'], castToInteger),

                ('asFloat32', namePrefix + 'asFloat32', ((name,), 'Float32'), ['compileTime', 'pure'], castToFloat),
                ('asFloat64', namePrefix + 'asFloat64', ((name,), 'Float64'), ['compileTime', 'pure'], castToFloat),
            ])

        for numberType in primitiveIntegerTypes:
            name = numberType.name
            namePrefix = numberType.name + '::'
            self.addPrimitiveFunctionsWithDesc([
                ('bitInvert', namePrefix + 'bitInvert', ((name,), name),  ['compileTime', 'pure'], bitInvert),

                ('&', namePrefix + '&', ((name, name), name),  ['compileTime', 'pure'], bitAnd),
                ('|', namePrefix + '|', ((name, name), name),  ['compileTime', 'pure'], bitOr),
                ('^', namePrefix + '^', ((name, name), name),  ['compileTime', 'pure'], bitXor),
                ('<<', namePrefix + '<<', ((name, name), name),  ['compileTime', 'pure'], shiftLeft),
                ('>>', namePrefix + '>>', ((name, name), name),  ['compileTime', 'pure'], shiftRight),
            ])

        for numberType in literalNumberTypes:
            name = numberType.name
            namePrefix = numberType.name + '::'

            self.addPrimitiveFunctionsWithDesc([
                ('c8',  namePrefix + 'asChar8',  ((name,), 'Char8'),  ['compileTime', 'pure'], castToCharacter),
                ('c16', namePrefix + 'asChar16', ((name,), 'Char16'), ['compileTime', 'pure'], castToCharacter),
                ('c32', namePrefix + 'asChar32', ((name,), 'Char32'), ['compileTime', 'pure'], castToCharacter),

                ('i8',  namePrefix + 'asInt8',  ((name,), 'Int8'),  ['compileTime', 'pure'], castToInteger),
                ('i16', namePrefix + 'asInt16', ((name,), 'Int16'), ['compileTime', 'pure'], castToInteger),
                ('i32', namePrefix + 'asInt32', ((name,), 'Int32'), ['compileTime', 'pure'], castToInteger),
                ('i64', namePrefix + 'asInt64', ((name,), 'Int64'), ['compileTime', 'pure'], castToInteger),

                ('u8',  namePrefix + 'asUInt8',  ((name,), 'UInt8'),  ['compileTime', 'pure'], castToInteger),
                ('u16', namePrefix + 'asUInt16', ((name,), 'UInt16'), ['compileTime', 'pure'], castToInteger),
                ('u32', namePrefix + 'asUInt32', ((name,), 'UInt32'), ['compileTime', 'pure'], castToInteger),
                ('u64', namePrefix + 'asUInt64', ((name,), 'UInt64'), ['compileTime', 'pure'], castToInteger),

                ('sz',   namePrefix + 'asSize',        ((name,), 'Size'),        ['compileTime', 'pure'], castToInteger),
                ('ssz',  namePrefix + 'asSignedSize',  ((name,), 'SignedSize'),  ['compileTime', 'pure'], castToInteger),
                ('uptr', namePrefix + 'asUIntPointer', ((name,), 'UIntPointer'), ['compileTime', 'pure'], castToInteger),
                ('iptr', namePrefix + 'asIntPointer',  ((name,), 'IntPointer'),  ['compileTime', 'pure'], castToInteger),

                ('f32', namePrefix + 'asFloat32', ((name,), 'Float32'), ['compileTime', 'pure'], castToFloat),
                ('f64', namePrefix + 'asFloat64', ((name,), 'Float64'), ['compileTime', 'pure'], castToFloat),
            ])

    def addPrimitiveFunctionsWithDesc(self, descriptions):
        for name, primitiveName, functionTypeSignature, effects, implementation in descriptions:
            isMacro = 'macro' in effects
            isPure = 'pure' in effects
            functionType = self.makeFunctionTypeWithSignature(functionTypeSignature, isMacro = isMacro, isPure = isPure)
            isCompileTime = 'compileTime' in effects
            isAlwaysReduced = 'alwaysInline' in effects
            primitiveFunction = ASGLiteralPrimitiveFunctionNode(ASGNodeNoDerivation.getSingleton(), functionType, primitiveName, compileTimeImplementation = implementation, pure = isPure, compileTime = isCompileTime, alwaysInline = isAlwaysReduced)
            self.addUnificationValue(primitiveFunction)
            self.addSymbolValue(name, primitiveFunction)

class ASGChildEnvironment(ASGEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__()
        self.parent = parent
        self.sourcePosition = sourcePosition
        self.topLevelTargetEnvironment = parent.getTopLevelTargetEnvironment()
    
    def getTopLevelTargetEnvironment(self):
        return self.topLevelTargetEnvironment

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.parent.lookSymbolBindingListRecursively(symbol)

    def findCurrentLoopBodyEntryNode(self) -> ASGNode:
        return self.parent.findCurrentLoopBodyEntryNode()
    
    def addBreakNodeToCurrentLoop(self, node: ASGLoopBreakNode):
        return self.parent.addBreakNodeToCurrentLoop(node)

    def addContinueNodeToCurrentLoop(self, node: ASGLoopContinueNode):
        return self.parent.addContinueNodeToCurrentLoop(node)
    
    def getCompilationTarget(self):
        return self.parent.getCompilationTarget()

class ASGChildEnvironmentWithBindings(ASGChildEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.symbolTable = {}

    def postCopy(self):
        self.symbolTable = dict(self.symbolTable)

    def addSymbolBinding(self, symbol: str, binding: ASGNode):
        if symbol is not None:
            self.symbolTable[symbol] = [binding] + self.symbolTable.get(symbol, [])

    def childWithSymbolBinding(self, symbol: str, binding: ASGNode):
        child = copy.copy(self)
        child.postCopy()
        child.addSymbolBinding(symbol, binding)
        return child

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, []) + self.parent.lookSymbolBindingListRecursively(symbol)

class ASGLexicalEnvironment(ASGChildEnvironment):
    def isLexicalEnvironment(self):
        return True

class ASGLoopBodyEnvironment(ASGLexicalEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.loopBodyEntryNode: ASGNode = None
        self.breakNodes: list[ASGNode] = []
        self.continueNodes: list[ASGNode] = []

    def findCurrentLoopBodyEntryNode(self) -> ASGNode:
        return self.loopBodyEntryNode
    
    def addBreakNodeToCurrentLoop(self, node: ASGLoopBreakNode):
        self.breakNodes.append(node)

    def addContinueNodeToCurrentLoop(self, node: ASGLoopContinueNode):
        self.continueNodes.append(node)

class ASGFunctionalAnalysisEnvironment(ASGLexicalEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.arguments = []
        self.symbolTable = {}

    def addArgumentBinding(self, argument: ASGArgumentNode):
        self.arguments.append(argument)
        if argument.name is not None:
            self.symbolTable[argument.name] = [argument] + self.symbolTable.get(argument.name, [])

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, []) + self.parent.lookSymbolBindingListRecursively(symbol)

class ASGScriptEnvironment(ASGLexicalEnvironment):
    def __init__(self, parent: ASGEnvironment, module: Module, sourcePosition: SourcePosition = None, scriptDirectory = '', scriptName = 'script') -> None:
        super().__init__(parent, sourcePosition)
        self.scriptDirectory = scriptDirectory
        self.scriptName = scriptName
        self.module = module

    def isScriptEnvironment(self):
        return True

class ASGBuilderWithGVNAndEnvironment(ASGBuilderWithGVN):
    def __init__(self, parentBuilder, topLevelEnvironment: ASGTopLevelTargetEnvironment) -> None:
        super().__init__(parentBuilder)
        self.topLevelEnvironment = topLevelEnvironment

    def topLevelIdentifier(self, name: str):
        if self.parentBuilder is not None:
            return self.parentBuilder.topLevelIdentifier(name)

        value = self.topLevelEnvironment.lookLastBindingOf(name)
        return self.unifyWithPreviousBuiltNode(value)

def makeScriptAnalysisEnvironment(target: CompilationTarget, module, sourcePosition: SourcePosition, scriptPath: str) -> ASGEnvironment:
    topLevelEnvironment = ASGTopLevelTargetEnvironment.getForTarget(target)
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ASGScriptEnvironment(topLevelEnvironment, module, sourcePosition, scriptDirectory, scriptName)
