from .mop import *
from .syntax import *
from .asg import *

class ASGEnvironment(ABC):
    @abstractmethod
    def getTopLevelTargetEnvironment(self):
        pass

    @abstractmethod
    def lookSymbolBindingListRecursively(self, symbol: str):
        pass

    def isLexicalEnvironment(self):
        return False

    def isScriptEnvironment(self):
        return False
    
    def childWithSymbolBinding(self, symbol: str, binding: ASGNode):
        return ASGChildEnvironmentWithBindings(self).childWithSymbolBinding(symbol, binding)

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
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Integer'))
        self.addBaseType(ASGBottomTypeNode(topLevelDerivation, 'Abort'))
        voidType = self.addBaseType(ASGUnitTypeNode(topLevelDerivation, 'Void'))
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Symbol'))
        falseType = self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'False'))
        trueType = self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'True'))
        self.addBaseType(ASGSumTypeNode(topLevelDerivation, [falseType, trueType], 'Boolean'))
        self.addBaseType(ASGAnyTypeUniverseNode(topLevelDerivation, 'Type'))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char8',  1, 1))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char16', 2, 2))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char32', 4, 4))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int8',  1, 1, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int16', 2, 2, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int32', 4, 4, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int64', 8, 8, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt8',  1, 1, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt16', 2, 2, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt32', 4, 4, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt64', 8, 8, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Size', target.pointerSize, target.pointerAlignment, False))
        self.addBaseType(ASGPrimitiveFloatType(topLevelDerivation, 'Float32', 4, 4))
        self.addBaseType(ASGPrimitiveFloatType(topLevelDerivation, 'Float64', 8, 8))

        self.addBaseType(ASGMetaType(topLevelDerivation, 'ASGNode', ASGNode))
        self.addBaseType(ASGMetaType(topLevelDerivation, 'MacroContext', ASGMacroContext))
        self.addSymbolValue('void', ASGLiteralUnitNode(topLevelDerivation, voidType))
        self.addSymbolValue('false', ASGLiteralUnitNode(topLevelDerivation, falseType))
        self.addSymbolValue('true', ASGLiteralUnitNode(topLevelDerivation, trueType))

        self.addPrimitiveFunctions()

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

    def getTopLevelTargetEnvironment(self):
        return self
    
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
    
    def makeFunctionType(self, argumentTypes: list[ASGNode], resultType: ASGNode, isMacro = False):
        if isMacro:
            return self.addUnificationValue(ASGMacroFunctionTypeNode(ASGNodeNoDerivation.getSingleton(), argumentTypes, resultType))
        else:
            return self.addUnificationValue(ASGFunctionTypeNode(ASGNodeNoDerivation.getSingleton(), argumentTypes, resultType))
    
    def makeFunctionTypeWithSignature(self, signature, isMacro = False):
        arguments, resultType = signature
        arguments = list(map(self.lookValidLastBindingOf, arguments))
        resultType = self.lookValidLastBindingOf(resultType)
        return self.makeFunctionType(arguments, resultType, isMacro = isMacro)

    def addPrimitiveFunctions(self):
        self.addControlFlowMacros()
        self.addPrimitiveTypeFunctions()

    def addControlFlowMacros(self):
        self.addPrimitiveFunctionsWithDesc([
            ('if:then:',  'ControlFlow::if:then:',  (('ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.ifThenMacro),
            ('if:then:else:',  'ControlFlow::if:then:',  (('ASGNode', 'ASGNode', 'ASGNode'), 'ASGNode'),  ['macro'], self.ifThenElseMacro),
        ])

    def ifThenMacro(self, macroContext: ASGMacroContext, condition: ASGNode, ifTrue: ASGNode) -> ASGNode:
        return ASGSyntaxIfThenElseNode(macroContext.derivation, condition, ifTrue, None)

    def ifThenElseMacro(self, macroContext: ASGMacroContext, condition: ASGNode, ifTrue: ASGNode, ifFalse: ASGNode) -> ASGNode:
        return ASGSyntaxIfThenElseNode(macroContext.derivation, condition, ifTrue, ifFalse)

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

        for numberType in numberTypes:
            castToCharacter = lambda derivation, resultType, value: ASGLiteralCharacterNode(derivation, resultType, resultType.normalizeValue(int(value.value)))
            castToInteger = lambda derivation, resultType, value: ASGLiteralIntegerNode(derivation, resultType, resultType.normalizeValue(int(value.value)))
            castToFloat = lambda derivation, resultType, value: ASGLiteralFloatNode(derivation, resultType, resultType.normalizeValue(float(value.value)))

            self.addPrimitiveFunctionsWithDesc([
                ('c8',  'Integer::asChar8',  (('Integer',), 'Char8'),  ['compileTime', 'pure'], castToCharacter),
                ('c16', 'Integer::asChar16', (('Integer',), 'Char16'), ['compileTime', 'pure'], castToCharacter),
                ('c32', 'Integer::asChar32', (('Integer',), 'Char32'), ['compileTime', 'pure'], castToCharacter),

                ('i8',  'Integer::asInt8',  (('Integer',), 'Int8'),  ['compileTime', 'pure'], castToInteger),
                ('i16', 'Integer::asInt16', (('Integer',), 'Int16'), ['compileTime', 'pure'], castToInteger),
                ('i32', 'Integer::asInt32', (('Integer',), 'Int32'), ['compileTime', 'pure'], castToInteger),
                ('i64', 'Integer::asInt64', (('Integer',), 'Int64'), ['compileTime', 'pure'], castToInteger),

                ('u8',  'Integer::asUInt8',  (('Integer',), 'UInt8'),  ['compileTime', 'pure'], castToInteger),
                ('u16', 'Integer::asUInt16', (('Integer',), 'UInt16'), ['compileTime', 'pure'], castToInteger),
                ('u32', 'Integer::asUInt32', (('Integer',), 'UInt32'), ['compileTime', 'pure'], castToInteger),
                ('u64', 'Integer::asUInt64', (('Integer',), 'UInt64'), ['compileTime', 'pure'], castToInteger),

                ('f32', 'Integer::asFloat32', (('Integer',), 'Float32'), ['compileTime', 'pure'], castToFloat),
                ('f64', 'Integer::asFloat64', (('Integer',), 'Float64'), ['compileTime', 'pure'], castToFloat),
            ])

    def addPrimitiveFunctionsWithDesc(self, descriptions):
        for name, primitiveName, functionTypeSignature, effects, implementation in descriptions:
            isMacro = 'macro' in effects
            functionType = self.makeFunctionTypeWithSignature(functionTypeSignature, isMacro = isMacro)
            isPure = 'pure' in effects
            isCompileTime = 'compileTime' in effects
            primitiveFunction = ASGLiteralPrimitiveFunctionNode(ASGNodeNoDerivation.getSingleton(), functionType, primitiveName, compileTimeImplementation = implementation, isPure = isPure, isCompileTime = isCompileTime)
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
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None, scriptDirectory = '', scriptName = 'script') -> None:
        super().__init__(parent, sourcePosition)
        self.scriptDirectory = scriptDirectory
        self.scriptName = scriptName

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

def makeScriptAnalysisEnvironment(target: CompilationTarget, sourcePosition: SourcePosition, scriptPath: str) -> ASGEnvironment:
    topLevelEnvironment = ASGTopLevelTargetEnvironment.getForTarget(target)
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ASGScriptEnvironment(topLevelEnvironment, sourcePosition, scriptDirectory, scriptName)
