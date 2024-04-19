from abc import ABC, abstractmethod
from .ghir import *
from .memoryDescriptor import *

class HIRContext:
    def __init__(self, pointerSize: int = 8) -> None:
        self.typeUniverses = dict()
        self.pointerSize = pointerSize
        self.pointerAlignment = pointerSize
        self.gcPointerSize = pointerSize*2
        self.gcPointerAlignment = pointerSize

        self.anySize = self.gcPointerSize
        self.anyAlignment = self.gcPointerAlignment
        self.functionTypeSize = self.gcPointerSize
        self.functionTypeAlignment = self.gcPointerAlignment
        self.anyType = HIRAnyType(self, 'Any', self.anySize, self.anyAlignment)
        self.booleanType = HIRPrimitiveBooleanType(self, 'Boolean', 1, 1)
        self.voidType = HIRVoidType(self, 'Void', 0, 1)

        self.int8Type   = HIRPrimitiveIntegerType(self, 'Int8',   True, 1, 1)
        self.int16Type  = HIRPrimitiveIntegerType(self, 'Int16',  True, 2, 2)
        self.int32Type  = HIRPrimitiveIntegerType(self, 'Int32',  True, 4, 4)
        self.int64Type  = HIRPrimitiveIntegerType(self, 'Int64',  True, 8, 8)

        self.uint8Type  = HIRPrimitiveIntegerType(self, 'UInt8',  False, 1, 1)
        self.uint16Type = HIRPrimitiveIntegerType(self, 'UInt16', False, 2, 2)
        self.uint32Type = HIRPrimitiveIntegerType(self, 'UInt32', False, 4, 4)
        self.uint64Type = HIRPrimitiveIntegerType(self, 'UInt64', False, 8, 8)

        self.cvargArgType = HIRPrimitiveCVarArgType(self, 'CVarArg', self.pointerSize, self.pointerAlignment)

        self.char8Type  = self.uint8Type
        self.char16Type = self.uint16Type
        self.char32Type = self.uint32Type

        if pointerSize == 4:
            self.sizeType        = self.uint32Type
            self.signedSizeType  =  self.int32Type
            self.uintPointerType = self.uint32Type
            self.intPointerType  =  self.int32Type
        else:
            self.sizeType        = self.uint64Type
            self.signedSizeType  =  self.int64Type
            self.uintPointerType = self.uint64Type
            self.intPointerType  =  self.int64Type

        self.float32Type = HIRPrimitiveFloatType(self, 'Float32', 4, 4)
        self.float64Type = HIRPrimitiveFloatType(self, 'Float64', 8, 8)

        self.float32x2Type = HIRPrimitiveVectorType(self, 'Float32x2', self.float32Type, 2, 8)
        self.float32x3Type = HIRPrimitiveVectorType(self, 'Float32x3', self.float32Type, 3, 16)
        self.float32x4Type = HIRPrimitiveVectorType(self, 'Float32x4', self.float32Type, 4, 16)
        self.float64x2Type = HIRPrimitiveVectorType(self, 'Float64x2', self.float64Type, 2, 16)
        self.float64x3Type = HIRPrimitiveVectorType(self, 'Float64x3', self.float64Type, 3, 32)
        self.float64x4Type = HIRPrimitiveVectorType(self, 'Float64x4', self.float64Type, 4, 32)

        self.int32x2Type = HIRPrimitiveVectorType(self, 'Int32x2', self.int32Type, 2, 8)
        self.int32x3Type = HIRPrimitiveVectorType(self, 'Int32x3', self.int32Type, 3, 16)
        self.int32x4Type = HIRPrimitiveVectorType(self, 'Int32x4', self.int32Type, 4, 16)
        self.uint32x2Type = HIRPrimitiveVectorType(self, 'UInt32x2', self.uint32Type, 2, 8)
        self.uint32x3Type = HIRPrimitiveVectorType(self, 'UInt32x3', self.uint32Type, 3, 16)
        self.uint32x4Type = HIRPrimitiveVectorType(self, 'UInt32x4', self.uint32Type, 4, 16)

        self.basicBlockType = HIRBasicBlockType(self, 'BasicBlock', self.pointerSize, self.pointerAlignment)
        self.functionalDefinitionType = HIRFunctionalDefinitionType(self, 'FunctionalDefinition', pointerSize, pointerSize)
        self.moduleType = HIRModuleType(self, 'Module', self.gcPointerSize, self.gcPointerAlignment)
        self.importedModuleType = HIRImportedModuleType(self, 'ImportedModule', self.gcPointerSize, self.gcPointerAlignment)

    def getTypeUniverse(self, index):
        if index not in self.typeUniverses:
            self.typeUniverses[index] = HIRTypeUniverse(self, index)
        return self.typeUniverses[index]

class HIRValueVisitor(ABC):
    @abstractmethod
    def visitPrimitiveType(self, value):
        pass

    @abstractmethod
    def visitFunctionType(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveFunction(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveInteger(self, value):
        pass

    @abstractmethod
    def visitConstantPrimitiveFloat(self, value):
        pass

    @abstractmethod
    def visitFunctionalDefinitionValue(self, value):
        pass

    @abstractmethod
    def visitFunctionalCaptureValue(self, value):
        pass

    @abstractmethod
    def visitFunctionalArgumentValue(self, value):
        pass

    @abstractmethod
    def visitBasicBlock(self, value):
        pass

    @abstractmethod
    def visitCallInstruction(self, value):
        pass

    @abstractmethod
    def visitReturnInstruction(self, value):
        pass

    @abstractmethod
    def visitConstantLambda(self, value):
        pass

    @abstractmethod
    def visitModule(self, value):
        pass

class HIRValue(ABC):
    def __init__(self, context: HIRContext) -> None:
        self.context = context

    @abstractmethod
    def accept(self, visitor: HIRValueVisitor):
        pass

    @abstractmethod
    def getType(self):
        pass

    def isConstantPrimitiveFunction(self) -> bool:
        return False

    def isConstantPrimitiveInteger(self) -> bool:
        return False

    def isConstantLambda(self) -> bool:
        return False

    def isFunctionalLocalValue(self) -> bool:
        return False

    def isTerminatorInstruction(self) -> bool:
        return False

    def isImportedValue(self) -> bool:
        return False

    def isImportedModuleValue(self) -> bool:
        return False

    def isImportedExternalValue(self) -> bool:
        return False

class HIRTypeValue(HIRValue):
    def  __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.memoryDescriptor: MemoryDescriptor = None

    def isType(self):
        return True
    
    def isPointerLikeType(self):
        return False

    def isVoidType(self):
        return False
    
    def canonicalizeResult(self, resultValue: HIRValue) -> HIRValue:
        return resultValue
    
    def buildMemoryDescriptor(self):
        return MemoryDescriptor(self.getSize(), self.getAlignment())

    def computeIndexedElementAccess(self, index: HIRValue) -> tuple[HIRValue, int, tuple[HIRValue, int] | None]:
        raise Exception("Not an aggregate or pointer type.")

    def getAlignedSize(self) -> int:
        alignment = self.getAlignment()
        return (self.getSize() + alignment - 1) & (-alignment)

    @abstractmethod
    def getSize(self) -> int:
        pass

    @abstractmethod
    def getAlignment(self) -> int:
        pass

    def getMemoryDescriptor(self) -> MemoryDescriptor:
        if self.memoryDescriptor is None:
            self.memoryDescriptor = self.buildMemoryDescriptor()
        return self.memoryDescriptor

class HIRTypeUniverse(HIRTypeValue):
    def  __init__(self, context: HIRContext, index) -> None:
        super().__init__(context)
        self.index = index

    def getType(self):
        return self.context.getTypeUniverse(self.index + 1)

    def getSize(self) -> int:
        return self.context.anySize

    def getAlignment(self) -> int:
        return self.context.anyAlignment
    
    def __str__(self) -> str:
        if self.index == 0:
            return 'Type'
        return 'Type@%d' % self.index

class HIRCompositeType(HIRTypeValue):
    def  __init__(self, context: HIRContext, elements: list[HIRTypeValue]) -> None:
        super().__init__(context)
        self.alignment = None
        self.size = None
        self.elements = elements

    @abstractmethod
    def computeLayout(self):
        pass

    def getAlignment(self) -> int:
        if self.alignment is None:
            self.computeLayout()
        return self.alignment
    
    def getSize(self) -> int:
        if self.size is None:
            self.computeLayout()
        return self.size

    def getType(self):
        return self.context.getTypeUniverse(0)

def alignedTo(offset, alignment):
    return (offset + alignment - 1) & (-alignment)

class HIRProductType(HIRCompositeType):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitProductType(self)

    def __str__(self) -> str:
        result = '('
        isFirst = True
        for element in self.elements:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(element)
        result += ')'
        return result

class HIRSumType(HIRCompositeType):
    def __init__(self, context: HIRContext, elements: list[HIRTypeValue]) -> None:
        super().__init__(context, elements)
        self.discriminantType = None
        self.discriminantAlignment = None
        self.discriminantSize = None

        self.variantDataOffset = None
        self.variantDataAlignment = None
        self.variantDataSize = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitSumType(self)
    
    def getVariantDataAlignment(self) -> int:
        if self.variantDataAlignment is None:
            self.computeLayout()

        return self.variantDataAlignment

    def getVariantDataSize(self) -> int:
        if self.variantDataSize is None:
            self.computeLayout()

        return self.variantDataSize
    
    def isStateless(self) -> bool:
        return self.getVariantDataSize() == 0
    
    def computeDiscriminantType(self):
        variantCount = len(self.elements)
        if variantCount <= 2:
            return self.context.booleanType
        elif variantCount <= 0xFF:
            return self.context.uint8Type
        elif variantCount <= 0xFFFF:
            return self.context.uint16Type
        else:
            assert variantCount <= 0xFFFFFFFF
            return self.context.uint32Type

    def computeLayout(self):
        self.discriminantType = self.computeDiscriminantType()
        self.discriminantAlignment = self.discriminantType.getAlignment()
        self.discriminantSize = self.discriminantType.getSize()

        self.variantDataSize = 0
        self.variantDataAlignment = 1
        for variant in self.elements:
            self.variantDataAlignment = max(self.variantDataAlignment, variant.getAlignment())
            self.variantDataSize = max(self.variantDataSize, variant.getSize())

        self.variantDataOffset = alignedTo(self.discriminantSize, self.variantDataAlignment)
        self.variantDataSize = alignedTo(self.variantDataSize, self.variantDataAlignment)
        self.alignment = max(self.discriminantAlignment, self.variantDataAlignment)
        self.size = alignedTo(self.variantDataOffset + self.variantDataSize, self.alignment)

    def __str__(self) -> str:
        result = '('
        isFirst = True
        for element in self.elements:
            if isFirst:
                isFirst = False
            else:
                result += ' | '
            result += str(element)
        result += ')'
        return result
    
class HIRDerivedType(HIRTypeValue):
    def  __init__(self, context: HIRContext, baseType: HIRTypeValue) -> None:
        super().__init__(context)
        self.baseType = baseType

    def getType(self):
        return self.baseType.getType()

class HIRArrayType(HIRDerivedType):
    def  __init__(self, context: HIRContext, baseType: HIRTypeValue, size: int, hasDependentSize: bool) -> None:
        super().__init__(context, baseType)
        self.size = size
        self.hasDependentSize = hasDependentSize

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitArrayType(self)

    def getAlignment(self) -> int:
        return self.baseType.getAlignment()
    
    def getSize(self) -> int:
        return self.baseType.getAlignedSize() * self.size
    
    def computeIndexedElementAccess(self, index: HIRValue) -> tuple[HIRValue, int, tuple[HIRValue, int] | None]:
        if index.isConstantPrimitiveInteger():
            return self.baseType, self.baseType.getAlignedSize() * index.value, None
        else:
            return self.baseType, 0, (index, self.baseType.getAlignedSize())

    def __str__(self) -> str:
        if self.hasDependentSize:
            return '%s[?]' % str(self.baseType)
        return '%s[%d]' % (str(self.baseType), self.size)
    
class HIRDecoratedType(HIRDerivedType):
    def  __init__(self, context: HIRContext, baseType: HIRTypeValue, decorations: int) -> None:
        super().__init__(context, baseType)
        self.decorations = decorations

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitDecoratedType(self)
    
    def computeIndexedElementAccess(self, index: HIRValue):
        return self.baseType.computeIndexedElementAccess(index)
    
    def getAlignedSize(self) -> int:
        return self.baseType.getAlignedSize()

    def getAlignment(self) -> int:
        return self.baseType.getAlignment()
    
    def getSize(self) -> int:
        return self.baseType.getSize()

    def isMutable(self) -> bool:
        return (self.decorations & DecoratedType.Mutable) != 0

    def isVolatile(self) -> bool:
        return (self.decorations & DecoratedType.Volatile) != 0
    
    def __str__(self) -> str:
        result = str(self.baseType)
        if self.isMutable():
            result += ' mutable'
        if self.isVolatile():
            result += ' volatile'
        return result
    
class HIRPointerLikeType(HIRDerivedType):
    def  __init__(self, context: HIRContext, baseType: HIRTypeValue) -> None:
        super().__init__(context, baseType)

    def isPointerLikeType(self):
        return True

    def computeIndexedElementAccess(self, index: HIRValue) -> tuple[HIRValue, int, tuple[HIRValue, int] | None]:
        if index.isConstantPrimitiveInteger():
            return self.baseType, self.baseType.getAlignedSize() * index.value, None
        else:
            return self.baseType, 0, (index, self.baseType.getAlignedSize())

    def getAlignment(self) -> int:
        return self.context.pointerAlignment
    
    def getSize(self) -> int:
        return self.context.pointerSize

class HIRPointerType(HIRPointerLikeType):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitPointerType(self)

    def __str__(self) -> str:
        return str(self.baseType) + ' pointer'

class HIRReferenceType(HIRPointerLikeType):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitReferenceType(self)

    def __str__(self) -> str:
        return str(self.baseType) + ' ref'

class HIRTemporaryReferenceType(HIRPointerLikeType):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitTemporaryReferenceType(self)

    def __str__(self) -> str:
        return str(self.baseType) + ' tempRef'
    
class HIRPrimitiveType(HIRTypeValue):
    def  __init__(self, context: HIRContext, name: str, size: int, alignment: int) -> None:
        super().__init__(context)
        self.name = name
        self.size = size
        self.alignment = alignment

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitPrimitiveType(self)

    def getAlignment(self) -> int:
        return self.alignment
    
    def getSize(self) -> int:
        return self.size

    def getType(self):
        return self.context.getTypeUniverse(0)
    
    def __str__(self) -> str:
        return self.name

class HIRAnyType(HIRPrimitiveType):
    pass

class HIRVoidType(HIRPrimitiveType):
    def __init__(self, context: HIRContext, name: str, size: int, alignment: int) -> None:
        super().__init__(context, name, size, alignment)
        self.singleton = None

    def canonicalizeResult(self, resultValue: HIRValue) -> HIRValue:
        return self.getSingleton()

    def getSingleton(self):
        if self.singleton is None:
            self.singleton = HIRConstantUnit(self.context, self)
        return self.singleton

    def isVoidType(self):
        return True

class HIRBasicBlockType(HIRPrimitiveType):
    pass

class HIRFunctionalDefinitionType(HIRPrimitiveType):
    pass

class HIRModuleType(HIRPrimitiveType):
    pass

class HIRImportedModuleType(HIRPrimitiveType):
    pass

class HIRPrimitiveBooleanType(HIRPrimitiveType):
    pass

class HIRPrimitiveCVarArgType(HIRPrimitiveType):
    pass

class HIRPrimitiveIntegerType(HIRPrimitiveType):
    def __init__(self, context: HIRContext, name: str, isSigned: bool, size: int, alignment: int) -> None:
        super().__init__(context, name, size, alignment)
        self.isSigned = isSigned

class HIRPrimitiveFloatType(HIRPrimitiveType):
    pass

class HIRPrimitiveVectorType(HIRPrimitiveType):
    def __init__(self, context: HIRContext, name: str, elementType: HIRPrimitiveType, elements: int, alignment: int) -> None:
        super().__init__(context, name, elementType.size*elements, alignment)
        self.elementType = elementType
        self.elements = elements

class HIRFunctionType(HIRTypeValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.argumentTypes = []
        self.isVariadic = False
        self.resultType: HIRValue = None
        self.callingConvention: str | None = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionType(self)

    def __str__(self) -> str:
        result = '('
        isFirst = True
        for arg in self.argumentTypes:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        if self.isVariadic:
            result += '...'
        result += ') -> '
        result += str(self.resultType)
        if self.callingConvention is not None:
            return '(%s) %s' % (result, self.callingConvention)
        return result
    
    def getAlignment(self) -> int:
        return self.context.functionTypeAlignment
    
    def getSize(self) -> int:
        return self.context.functionTypeSize

    def getType(self):
        return self.context.getTypeUniverse(0)    

class HIRConstant(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue) -> None:
        super().__init__(context)
        self.type = type

    def getType(self):
        return self.type

class HIRConstantPrimitiveFunction(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue, name: str, compileTimeImplementation = None) -> None:
        super().__init__(context, type)
        self.name = name
        self.compileTimeImplementation = compileTimeImplementation

    def isConstantPrimitiveFunction(self) -> bool:
        return True

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveFunction(self)

    def __str__(self) -> str:
        return '%s <%s>' % (str(self.type), self.name)

class HIRConstantPrimitive(HIRConstant):
    pass

class HIRConstantUnit(HIRConstantPrimitive):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantUnit(self)

    def __str__(self) -> str:
        return '%s()' % str(self.type)

class HIRConstantStringData(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: bytes, nullTerminated: bool = True) -> None:
        super().__init__(context, type)
        self.value = value
        self.nullTerminated = nullTerminated

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantStringData(self)

    def __str__(self) -> str:
        if self.nullTerminated:
            return '%s cstring(%s)' % (str(self.type), repr(self.value))
        else:
            return '%s string(%s)' % (str(self.type), repr(self.value))

class HIRConstantPrimitiveInteger(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: int) -> None:
        super().__init__(context, type)
        self.value = value

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveInteger(self)

    def isConstantPrimitiveInteger(self) -> bool:
        return True

    def __str__(self) -> str:
        return '%s(%d)' % (str(self.type), self.value)

class HIRConstantPrimitiveFloat(HIRConstantPrimitive):
    def __init__(self, context: HIRContext, type: HIRValue, value: float) -> None:
        super().__init__(context, type)
        self.value = value

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantPrimitiveFloat(self)

    def __str__(self) -> str:
        return '%s(%f)' % (str(self.type), self.value)
    
class HIRGlobalValue(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRValue, sourcePosition: SourcePosition) -> None:
        super().__init__(context, type)
        self.sourcePosition = sourcePosition
        self.name = None
        self.globalValueIndex = 0

    def __str__(self) -> str:
        if self.name is not None:
            return '@%s|%d' % (self.name, self.globalValueIndex)
        return '@%d' % self.globalValueIndex
    
    def fullPrintString(self) -> str:
        return str(self)

class HIRImportedModule(HIRGlobalValue):
    def __init__(self, context: HIRContext, parentModule, moduleName: str, sourcePosition: SourcePosition) -> None:
        super().__init__(context, context.importedModuleType, sourcePosition)
        self.parentModule: HIRModule = parentModule
        self.moduleName = moduleName
        self.name = moduleName
        self.importedValues: list[HIRImportedModuleValue] = []

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitImportedModule(self)
    
    def importValueWithType(self, name: str, type: HIRValue):
        for importedValue in self.importedValues:
            if importedValue.name == name and importedValue.getType() == type:
                return importedValue
        
        importedValue = HIRImportedModuleValue(self.context, type, self, name);
        self.parentModule.addGlobalValue(importedValue)
        return importedValue

    def fullPrintString(self) -> str:
        return '%s := import "%s"' % (str(self), self.moduleName)

class HIRImportedValue(HIRGlobalValue):
    def isImportedValue(self) -> bool:
        return True

class HIRImportedModuleValue(HIRImportedValue):
    def __init__(self, context: HIRContext, type: HIRValue, module: HIRImportedModule, valueName: str, sourcePosition: SourcePosition) -> None:
        super().__init__(context, type, sourcePosition)
        self.module = module
        self.valueName = valueName
        self.name = valueName

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitImportedModuleValue(self)
    
    def isImportedModuleValue(self) -> bool:
        return True

    def fullPrintString(self) -> str:
        return '%s := from %s import "%s" : %s' % (str(self), str(self.module), self.valueName, str(self.type))

class HIRImportedExternalValue(HIRImportedValue):
    def __init__(self, context: HIRContext, type: HIRValue, externalName: str, valueName: str, sourcePosition: SourcePosition) -> None:
        super().__init__(context, type, sourcePosition)
        self.externalName = externalName
        self.valueName = valueName
        self.name = valueName

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitImportedExternalValue(self)
    
    def isImportedExternalValue(self) -> bool:
        return True

    def fullPrintString(self) -> str:
        return '%s := from external %s import "%s" : %s' % (str(self), str(self.externalName), self.valueName, str(self.type))

class HIRFunctionalDefinition(HIRGlobalValue):
    def __init__(self, context: HIRContext, sourcePosition: SourcePosition) -> None:
        super().__init__(context, context.functionalDefinitionType, sourcePosition)
        self.captures = []
        self.arguments = []
        self.isVariadic = False
        self.firstBasicBlock: HIRBasicBlock = None
        self.lastBasicBlock: HIRBasicBlock = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalDefinitionValue(self)

    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBasicBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBasicBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def enumerateLocalValues(self):
        index = 0
        for localValue in self.allLocalValues():
            localValue.localValueIndex = index
            index += 1

    def allLocalValues(self):
        for capture in self.captures:
            yield capture
        for argument in self.arguments:
            yield argument
        for basicBlock in self.basicBlocks():
            yield basicBlock
            for instruction in basicBlock.instructions():
                yield instruction

    def basicBlocks(self):
        position = self.firstBasicBlock
        while position is not None:
            yield position
            position = position.nextBasicBlock

    def basicBlocksInReversePostOrder(self):
        visitedSet = set()
        visitedList = []

        def visit(basicBlock: HIRBasicBlock):
            if basicBlock in visitedSet:
                return
            
            visitedSet.add(basicBlock)
            for successor in reversed(basicBlock.successorBlocks()):
                visit(successor)
            visitedList.append(basicBlock)

        for basicBlock in self.basicBlocks():
            visit(basicBlock)

        return list(reversed(visitedList))

    def reachableBasicBlocksInReversePostOrder(self):
        visitedSet = set()
        visitedList = []

        def visit(basicBlock: HIRBasicBlock):
            if basicBlock in visitedSet:
                return
            
            visitedSet.add(basicBlock)
            for successor in reversed(basicBlock.successorBlocks()):
                visit(successor)
            visitedList.append(basicBlock)

        if self.firstBasicBlock is not None:
            visit(self.firstBasicBlock)

        return list(reversed(visitedList))

    def fullPrintString(self) -> str:
        self.enumerateLocalValues()
        result = str(self)
        result += ' := ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += capture.fullPrintString()

        result += '] ('
        isFirst = True
        for argument in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += argument.fullPrintString()

        if self.isVariadic:
            result += '...'

        result += ') : '
        result += str(self.type)
        result += ' {\n'
        for basicBlock in self.basicBlocks():
            result += basicBlock.fullPrintString()
        result += '}\n'
        return result

class HIRFunctionalLocalValue(HIRValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None, sourcePosition: SourcePosition = None) -> None:
        super().__init__(context)
        self.name: str = name
        self.sourcePosition = sourcePosition
        self.type = type
        self.localValueIndex = 0

    def isFunctionalLocalValue(self) -> bool:
        return True
    
    def getType(self):
        return self.type

    def __str__(self) -> str:
        if self.name is not None:
            return '$%s|%d' % (self.name, self.localValueIndex)
        return '$%d' % self.localValueIndex

class HIRFunctionalCaptureValue(HIRFunctionalLocalValue):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalCaptureValue(self)
    
    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRFunctionalArgumentValue(HIRFunctionalLocalValue):
    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitFunctionalArgumentValue(self)

    def fullPrintString(self) -> str:
        return '%s : %s' % (str(self), str(self.type)) 

class HIRBasicBlock(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, name: str = None, sourcePosition: SourcePosition = None) -> None:
        super().__init__(context, context.basicBlockType, name, sourcePosition)
        self.previousBasicBlock: HIRBasicBlock = None
        self.nextBasicBlock: HIRBasicBlock = None
        self.firstInstruction: HIRInstruction = None
        self.lastInstruction: HIRInstruction = None

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitBasicBlock(self)

    def addInstruction(self, instruction):
        if self.lastInstruction is None:
            self.firstInstruction = self.lastInstruction = instruction
        else:
            instruction.previousInstruction = self.lastInstruction
            self.lastInstruction.nextInstruction = instruction
            self.lastInstruction = instruction

    def instructions(self):
        position = self.firstInstruction
        while position is not None:
            yield position
            position = position.nextInstruction

    def fullPrintString(self) -> str:
        result = str(self)
        result += ':\n'
        for instruction in self.instructions():
            result += '    '
            result += instruction.fullPrintString()
            result += '\n'
        return result
    
    def successorBlocks(self):
        if self.lastInstruction is None:
            return []
        return self.lastInstruction.successorBlocks()

class HIRInstruction(HIRFunctionalLocalValue):
    def __init__(self, context: HIRContext, type: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.previousInstruction: HIRInstruction = None
        self.nextInstruction: HIRInstruction = None

    def successorBlocks(self) -> list[HIRBasicBlock]:
        return []

class HIRAllocaInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, valueType: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.valueType = valueType

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitAllocaInstruction(self)

    def fullPrintString(self) -> str:
        return '%s : %s := alloca %s (' % (str(self), str(self.type), str(self.valueType))
    
class HIRLoadInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, pointer: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.pointer = pointer
        self.isVolatile = False

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitLoadInstruction(self)

    def fullPrintString(self) -> str:
        if self.isVolatile:
            return '%s : %s := volatile load %s' % (str(self), str(self.type), str(self.pointer))
        return '%s : %s := load %s' % (str(self), str(self.type), str(self.pointer))

class HIRStoreInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, value: HIRValue, pointer: HIRValue, name: str = None) -> None:
        super().__init__(context, context.voidType, name)
        self.value = value
        self.pointer = pointer
        self.isVolatile = False

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitStoreInstruction(self)

    def fullPrintString(self) -> str:
        if self.isVolatile:
            return '%s : %s := volatile store %s in %s' % (str(self), str(self.type), str(self.value), str(self.pointer))
        return '%s : %s := store %s in %s' % (str(self), str(self.type), str(self.value), str(self.pointer))
    
class HIRCallInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, functional: HIRValue, arguments: list[HIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.functional = functional
        self.arguments = arguments

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitCallInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s : %s := call %s (' % (str(self), str(self.type), str(self.functional))
        isFirst = True
        for arg in self.arguments:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result

class HIRGetElementPointerInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, pointer: HIRValue, indices: list[HIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.pointer = pointer
        self.indices = indices

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitGetElementPointerInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s : %s := getElementPointer %s (' % (str(self), str(self.type), str(self.pointer))
        isFirst = True
        for arg in self.indices:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result
        
class HIRExtractValueInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, aggregate: HIRValue, indices: list[HIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.aggregate = aggregate
        self.indices = indices

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitExtractValueInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s : %s := extractValue %s at (' % (str(self), str(self.type), str(self.aggregate))
        isFirst = True
        for arg in self.indices:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result
    
class HIRExtractValueReferenceInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, aggregate: HIRValue, indices: list[HIRValue], name: str = None) -> None:
        super().__init__(context, type, name)
        self.aggregate = aggregate
        self.indices = indices

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitExtractValueReferenceInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s : %s := extractValueReference %s at (' % (str(self), str(self.type), str(self.aggregate))
        isFirst = True
        for arg in self.indices:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result
    
class HIRInsertValueInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, type: HIRValue, aggregate: HIRValue, indices: list[HIRValue], value: HIRValue, name: str = None) -> None:
        super().__init__(context, type, name)
        self.aggregate = aggregate
        self.indices = indices
        self.value = value

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitInsertValueInstruction(self)

    def fullPrintString(self) -> str:
        result = '%s : %s := insertValue %s in %s at (' % (str(self), str(self.type), str(self.value), str(self.aggregate))
        isFirst = True
        for arg in self.indices:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(arg)
        result += ')'
        return result
    
class HIRTerminatorInstruction(HIRInstruction):
    def __init__(self, context: HIRContext, name: str = None) -> None:
        super().__init__(context, context.voidType, name)
    
    def isTerminatorInstruction(self) -> bool:
        return True

class HIRBranchInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, destination: HIRBasicBlock) -> None:
        super().__init__(context)
        self.destination = destination

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitBranchInstruction(self)

    def successorBlocks(self) -> list[HIRBasicBlock]:
        return [self.destination]

    def fullPrintString(self) -> str:
        return 'branch %s' % str(self.destination)

class HIRCondBranchInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, condition: HIRValue, trueDestination: HIRBasicBlock, falseDestination: HIRBasicBlock) -> None:
        super().__init__(context)
        self.condition = condition
        self.trueDestination = trueDestination
        self.falseDestination = falseDestination

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitCondBranchInstruction(self)

    def successorBlocks(self) -> list[HIRBasicBlock]:
        return [self.trueDestination, self.falseDestination]

    def fullPrintString(self) -> str:
        return 'condBranch: %s ifTrue: %s ifFalse: %s' %  (str(self.condition), str(self.trueDestination), str(self.falseDestination))
    
class HIRReturnInstruction(HIRTerminatorInstruction):
    def __init__(self, context: HIRContext, result: HIRValue) -> None:
        super().__init__(context)
        self.result = result

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitReturnInstruction(self)

    def fullPrintString(self) -> str:
        return 'return %s' % str(self.result)

class HIRConstantLambda(HIRConstant):
    def __init__(self, context: HIRContext, type: HIRConstant, captures: list[HIRConstant], definition: HIRFunctionalDefinition) -> None:
        super().__init__(context, type)
        self.captures = captures
        self.definition = definition

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitConstantLambda(self)

    def isConstantLambda(self) -> bool:
        return True

    def __str__(self) -> str:
        result = 'lambda '
        result += str(self.definition)
        result += ' captures ['
        isFirst = True
        for capture in self.captures:
            if isFirst:
                isFirst = False
            else:
                result += ', '
            result += str(capture)
        result += '] : '
        result += str(self.type)
        return result

class HIRBuilder:
    def __init__(self, context: HIRContext, functional: HIRFunctionalDefinition) -> None:
        self.context = context
        self.functional = functional
        self.basicBlock = None
        self.sourcePosition: SourcePosition = None
    
    def newBasicBlock(self, name: str):
        return HIRBasicBlock(self.context, name, self.sourcePosition)

    def withSourcePositionDo(self, sourcePosition, aBlock):
        oldSourcePosition = self.sourcePosition
        self.sourcePosition = sourcePosition
        try:
            return aBlock()
        finally:
            self.sourcePosition = oldSourcePosition

    def beginBasicBlock(self, basicBlock: HIRBasicBlock) -> HIRBasicBlock:
        self.functional.addBasicBlock(basicBlock)
        self.basicBlock = basicBlock
        return basicBlock

    def beginNewBasicBlock(self, name: str) -> HIRBasicBlock:
        return self.beginBasicBlock(self.newBasicBlock(name))
    
    def isLastTerminator(self) -> bool:
        return self.basicBlock is not None and self.basicBlock.lastInstruction is not None and self.basicBlock.lastInstruction.isTerminatorInstruction()
    
    def addInstruction(self, instruction: HIRInstruction) -> HIRValue:
        instruction.sourcePosition = self.sourcePosition
        self.basicBlock.addInstruction(instruction)
        return instruction

    def alloca(self, resultType: HIRValue, valueType: HIRValue) -> HIRInstruction:
        return self.addInstruction(HIRAllocaInstruction(self.context, resultType, valueType))

    def load(self, resultType: HIRValue, pointer: HIRValue) -> HIRInstruction:
        return self.addInstruction(HIRLoadInstruction(self.context, resultType, pointer))

    def getElementPointer(self, resultType: HIRValue, pointer: HIRValue, indices: list[HIRValue]) -> HIRInstruction:
        return self.addInstruction(HIRGetElementPointerInstruction(self.context, resultType, pointer, indices))

    def extractValue(self, resultType: HIRValue, aggregate: HIRValue, indices: list[HIRValue]) -> HIRInstruction:
        return self.addInstruction(HIRExtractValueInstruction(self.context, resultType, aggregate, indices))

    def extractValueReference(self, resultType: HIRValue, aggregate: HIRValue, indices: list[HIRValue]) -> HIRInstruction:
        return self.addInstruction(HIRExtractValueReferenceInstruction(self.context, resultType, aggregate, indices))

    def insertValue(self, resultType: HIRValue, aggregate: HIRValue, indices: list[HIRValue], value: HIRValue) -> HIRInstruction:
        return self.addInstruction(HIRInsertValueInstruction(self.context, resultType, aggregate, indices, value))

    def store(self, value: HIRValue, pointer: HIRValue) -> HIRInstruction:
        return self.addInstruction(HIRStoreInstruction(self.context, value, pointer))

    def call(self, resultType: HIRValue, functional: HIRValue, arguments: list[HIRValue]) -> HIRInstruction:
        return self.addInstruction(HIRCallInstruction(self.context, resultType, functional, arguments))

    def condBranch(self, condition: HIRValue, trueDestination: HIRBasicBlock, falseDestination) -> HIRInstruction:
        return self.addInstruction(HIRCondBranchInstruction(self.context, condition, trueDestination, falseDestination))

    def branch(self, destination: HIRBasicBlock) -> HIRInstruction:
        return self.addInstruction(HIRBranchInstruction(self.context, destination))

    def returnValue(self, value) -> HIRInstruction:
        return self.addInstruction(HIRReturnInstruction(self.context, value))

class HIRModule(HIRValue):
    def __init__(self, context: HIRContext) -> None:
        super().__init__(context)
        self.importedModules = []
        self.importedModuleDictionary = dict()
        self.exportedValues: list[tuple[str, HIRValue, str]] = []
        self.entryPoint: HIRValue = None
        self.globalValues: list[HIRGlobalValue] = []
        self.name = ''

    def accept(self, visitor: HIRValueVisitor):
        return visitor.visitModule(self)

    def getType(self):
        return None
    
    def exportValue(self, name: str, value: HIRValue, externalName: str | None = None):
        self.exportedValues.append((name, value, externalName))

    def importModuleWithName(self, name: str):
        if name in self.importedModuleDictionary:
            return name
        
        importedModule = HIRImportedModule(self.context, self, name)
        self.importedModuleDictionary[name] = importedModule
        self.importedModules.append(importedModule)
        return importedModule
    
    def allGlobalValues(self):
        for importedModule in self.importedModules:
            yield importedModule
        for value in self.globalValues:
            yield value

    def addGlobalValue(self, globalValue: HIRGlobalValue):
        self.globalValues.append(globalValue)

    def enumerateGlobalValues(self):
        index = 0
        for globalValue in self.allGlobalValues():
            globalValue.globalValueIndex = index
            index += 1

    def prettyPrint(self) -> str:
        self.enumerateGlobalValues()

        result = ''
        for name, value, externalName in self.exportedValues:
            if externalName is not None:
                result += 'export "%s" external %s := %s\n' % (name, externalName, str(value))
            else:
                result += 'export "%s" := %s\n' % (name, str(value))
        if self.entryPoint is not None:
            result += 'entryPoint: %s\n' % str(self.entryPoint)

        if len(result) != 0:
            result += '\n'

        for globalValue in self.allGlobalValues():
            result += globalValue.fullPrintString()
            result += '\n'
        return result

class HIRModuleFrontend:
    def __init__(self) -> None:
        self.context = HIRContext()
        self.module = HIRModule(self.context)
        self.translatedValueDictionary = dict()
        self.translatedConstantValueDictionary = dict()
        self.valueTranslator = HIRModuleFrontendValueTranslator(self)
        self.runtimeDependencyChecker = GHIRRuntimeDependencyChecker()

        for baseType, targetType in [
            (VoidType, self.context.voidType),

            (BooleanType, self.context.booleanType),
            (FalseType, self.context.voidType),
            (TrueType, self.context.voidType),

            (Int8Type,  self.context.int8Type),
            (Int16Type, self.context.int16Type),
            (Int32Type, self.context.int32Type),
            (Int64Type, self.context.int64Type),

            (UInt8Type,  self.context.uint8Type),
            (UInt16Type, self.context.uint16Type),
            (UInt32Type, self.context.uint32Type),
            (UInt64Type, self.context.uint64Type),

            (Char8Type,  self.context.char8Type),
            (Char16Type, self.context.char16Type),
            (Char32Type, self.context.char32Type),

            (SizeType, self.context.sizeType),
            (SignedSizeType, self.context.signedSizeType),
            (UIntPointerType, self.context.uintPointerType),
            (IntPointerType, self.context.intPointerType),

            (Float32Type, self.context.float32Type),
            (Float64Type, self.context.float64Type),

            (CVarArgType, self.context.cvargArgType),

            (Float32x2Type, self.context.float32x2Type),
            (Float32x3Type, self.context.float32x3Type),
            (Float32x4Type, self.context.float32x4Type),
            (Float64x2Type, self.context.float64x2Type),
            (Float64x3Type, self.context.float64x3Type),
            (Float64x4Type, self.context.float64x4Type),

            (Int32x2Type, self.context.int32x2Type),
            (Int32x3Type, self.context.int32x3Type),
            (Int32x4Type, self.context.int32x4Type),
            (UInt32x2Type, self.context.uint32x2Type),
            (UInt32x3Type, self.context.uint32x3Type),
            (UInt32x4Type, self.context.uint32x4Type),
        ]:
            self.translatedConstantValueDictionary[baseType] = targetType

    def compileGraphModule(self, graphModule: GHIRModule) -> HIRModule:
        self.module.name = graphModule.name
        for name, value, externalName in graphModule.exportedValues:
            self.module.exportValue(name, self.translateGraphValue(value), externalName)
        if graphModule.entryPoint is not None:
            self.module.entryPoint = self.translateGraphValue(graphModule.entryPoint)
        return self.module

    def translateConstantTypedValue(self, typedValue: TypedValue) -> HIRValue:
        if typedValue in self.translatedConstantValueDictionary:
            return self.translatedConstantValueDictionary[typedValue]
        
        translatedValue = typedValue.acceptTypedValueVisitor(self.valueTranslator)
        self.translatedConstantValueDictionary[typedValue] = translatedValue
        return translatedValue

    def translateGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        if graphValue in self.translatedValueDictionary:
            return self.translatedValueDictionary[graphValue]
        
        translatedValue = graphValue.accept(self)
        self.translatedValueDictionary[graphValue] = translatedValue
        return translatedValue
    
    def visitConstantValue(self, graphValue: GHIRConstantValue) -> HIRValue:
        return self.translateConstantTypedValue(graphValue.value)

    def visitPrimitiveFunction(self, value: GHIRPrimitiveFunction) -> HIRValue:
        return HIRConstantPrimitiveFunction(self.context, self.translateGraphValue(value.type), value.name, value.compileTimeImplementation)

    def visitArrayType(self, value: GHIRArrayType) -> HIRValue:
        elementType = self.translateGraphValue(value.elementType)
        if self.runtimeDependencyChecker.checkValue(value.size):
            return HIRArrayType(self.context, elementType, 0, True)
        else:
            size = self.translateGraphValue(value.size)
            assert size.isConstantPrimitiveInteger()
            return HIRArrayType(self.context, elementType, size.value, False)

    def visitProductType(self, value: GHIRProductType) -> HIRValue:
        elements = list(map(self.translateGraphValue, value.elements))
        return HIRProductType(self.context, elements)

    def visitSumType(self, value: GHIRSumType) -> HIRValue:
        elements = list(map(self.translateGraphValue, value.elements))
        return HIRSumType(self.context, elements)

    def visitDecoratedType(self, value: GHIRDecoratedType) -> HIRValue:
        baseType = self.translateGraphValue(value.baseType)
        return HIRDecoratedType(self.context, baseType, value.decorations)

    def visitPointerType(self, value: GHIRPointerType) -> HIRValue:
        baseType = self.translateGraphValue(value.baseType)
        return HIRPointerType(self.context, baseType)

    def visitReferenceType(self, value: GHIRReferenceType) -> HIRValue:
        baseType = self.translateGraphValue(value.baseType)
        return HIRReferenceType(self.context, baseType)

    def visitTemporaryReferenceType(self, value: GHIRTemporaryReferenceType) -> HIRValue:
        baseType = self.translateGraphValue(value.baseType)
        return HIRTemporaryReferenceType(self.context, baseType)

    def visitLambdaValue(self, graphValue: GHIRLambdaValue) -> HIRValue:
        lambdaType = self.translateGraphValue(graphValue.type)
        definition = self.translateGraphValue(graphValue.definition)
        captures = list(map(self.translateGraphValue, graphValue.captures))
        return HIRConstantLambda(self.context, lambdaType, captures, definition)

    def visitFunctionalDefinitionValue(self, graphValue: GHIRFunctionalDefinitionValue) -> HIRValue:
        hirDefinition = HIRFunctionalDefinition(self.context, graphValue.sourcePosition)
        self.translatedValueDictionary[graphValue] = hirDefinition
        self.module.addGlobalValue(hirDefinition)
        HIRFunctionalDefinitionFrontend(self).translateFunctionDefinitionInto(graphValue, hirDefinition)
        return hirDefinition
    
    def visitSimpleFunctionType(self, graphValue: GHIRSimpleFunctionType) -> HIRValue:
        hirFunctionType = HIRFunctionType(self.context)

        self.translatedValueDictionary[graphValue] = hirFunctionType
        hirFunctionType.argumentTypes = list(map(self.translateGraphValue, graphValue.arguments))
        hirFunctionType.isVariadic = graphValue.isVariadic
        hirFunctionType.resultType = self.translateGraphValue(graphValue.resultType)
        hirFunctionType.callingConvention = graphValue.callingConvention
        return hirFunctionType

    def visitImportedModule(self, graphValue: GHIRImportedModule) -> HIRValue:
        return self.module.importModuleWithName(graphValue.name)

    def visitImportedModuleValue(self, graphValue: GHIRImportedModuleValue) -> HIRValue:
        module: HIRImportedModule = self.translateGraphValue(graphValue.module)
        type: HIRValue = self.translateGraphValue(graphValue.type)
        return module.importValueWithType(graphValue.name, type)
    
    def visitImportedExternalValue(self, graphValue: GHIRImportedExternalValue) -> HIRValue:
        type: HIRValue = self.translateGraphValue(graphValue.type)
        importedExternal = HIRImportedExternalValue(self.context, type, graphValue.externalName, graphValue.name, graphValue.sourcePosition);
        self.module.addGlobalValue(importedExternal)
        return importedExternal

class HIRModuleFrontendValueTranslator:
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.context = moduleFrontend.context
        self.moduleFrontend = moduleFrontend

    def translateConstantTypedValue(self, value: TypedValue):
        return self.moduleFrontend.translateConstantTypedValue(value)

    def visitDecoratedType(self, value: DecoratedType) -> HIRValue:
        baseType = self.translateConstantTypedValue(value.baseType)
        return HIRDecoratedType(self.context, baseType, value.decorations)

    def visitPointerType(self, value: PointerType) -> HIRValue:
        baseType = self.translateConstantTypedValue(value.baseType)
        return HIRPointerType(self.context, baseType)

    def visitVoidTypeValue(self, value: VoidTypeValue) -> HIRValue:
        return self.translateConstantTypedValue(value.type).getSingleton()
    
    def visitStringDataValue(self, value: StringDataValue):
        return HIRConstantStringData(self.context, self.translateConstantTypedValue(value.getType()), value.value, True)

    def visitPrimitiveIntegerValue(self, value: PrimitiveIntegerValue) -> HIRValue:
        return HIRConstantPrimitiveInteger(self.context, self.moduleFrontend.translatedConstantValueDictionary[value.type], value.value)

class HIRFunctionalDefinitionFrontend:
    def __init__(self, moduleFrontend: HIRModuleFrontend) -> None:
        self.context = moduleFrontend.context
        self.moduleFrontend = moduleFrontend
        self.functionalDefinition: HIRFunctionalDefinition = None
        self.localBindings = dict()
        self.translatedLocalValues = dict()
        self.builder: HIRBuilder = None
        self.currentBreak: HIRBasicBlock = None
        self.currentContinue: HIRBasicBlock = None
    
    def translateFunctionDefinitionInto(self, graphFunctionalDefinition: GHIRFunctionalDefinitionValue, hirDefinition: HIRFunctionalDefinition):
        self.functionalDefinition = hirDefinition
        for graphCapture in graphFunctionalDefinition.captures:
            capture = HIRFunctionalCaptureValue(self.context, self.moduleFrontend.translateGraphValue(graphCapture.type), graphCapture.name, graphCapture.sourcePosition)
            self.localBindings[graphCapture] = capture
            self.functionalDefinition.captures.append(capture)

        for graphArgument in graphFunctionalDefinition.arguments:
            argument = HIRFunctionalArgumentValue(self.context, self.moduleFrontend.translateGraphValue(graphArgument.type), graphArgument.name, graphArgument.sourcePosition)
            self.localBindings[graphArgument] = argument
            self.functionalDefinition.arguments.append(argument)

        self.builder = HIRBuilder(self.context, self.functionalDefinition)
        self.builder.sourcePosition = self.functionalDefinition.sourcePosition
        self.builder.beginNewBasicBlock('entry')

        resultValue = self.translateGraphValue(graphFunctionalDefinition.body)
        if not self.builder.isLastTerminator():
            self.builder.returnValue(resultValue)

    def translateGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        if graphValue in self.localBindings:
            return self.localBindings[graphValue]
        
        if not self.moduleFrontend.runtimeDependencyChecker.checkValue(graphValue):
            return self.moduleFrontend.translateGraphValue(graphValue)
        
        if graphValue in self.translatedLocalValues:
            return self.translatedLocalValues[graphValue]
        
        translatedValue = self.builder.withSourcePositionDo(graphValue.sourcePosition, lambda: graphValue.accept(self))
        self.translatedLocalValues[graphValue] = translatedValue
        return translatedValue
    
    def translateLocalGraphValue(self, graphValue: GHIRValue) -> HIRValue:
        oldTranslatedLocalValues = self.translatedLocalValues
        self.translatedLocalValues = dict(self.translatedLocalValues)
        result = self.translateGraphValue(graphValue)
        self.translatedLocalValues = oldTranslatedLocalValues
        return result
    
    def withBreakAndContinueDo(self, breakBlock: HIRBasicBlock, continueBlock: HIRBasicBlock, action):
        oldBreak = self.currentBreak
        oldContinue = self.currentContinue
        self.currentBreak = breakBlock
        self.currentContinue = continueBlock
        try:
            action()
        finally:
            self.currentBreak = oldBreak
            self.currentContinue = oldContinue

    def visitAllocaMutableWithValueExpression(self, allocaExpression: GHIRAllocaMutableWithValueExpression):
        pointerType = self.translateGraphValue(allocaExpression.type)
        valueType = self.translateGraphValue(allocaExpression.valueType)
        initialValue = self.translateGraphValue(allocaExpression.initialValue)
        alloca = self.builder.alloca(pointerType, valueType)
        self.builder.store(initialValue, alloca)
        return alloca

    def visitApplicationValue(self, application: GHIRApplicationValue) -> HIRValue:
        functional = self.translateGraphValue(application.functional)
        arguments = list(map(self.translateGraphValue, application.arguments))
        resultType = self.translateGraphValue(application.type)
        return resultType.canonicalizeResult(self.builder.call(resultType, functional, arguments))
    
    def visitIfExpression(self, ifExpression: GHIRIfExpression) -> HIRValue:
        ## Condition
        condition = self.translateGraphValue(ifExpression.condition)

        trueBlock = self.builder.newBasicBlock('ifTrue')
        falseBlock = self.builder.newBasicBlock('ifFalse')
        mergeBlock = self.builder.newBasicBlock('ifMerge')
        self.builder.condBranch(condition, trueBlock, falseBlock)

        ## True expression
        self.builder.beginBasicBlock(trueBlock)
        trueResult = self.translateLocalGraphValue(ifExpression.trueExpression)
        trueResultIncomingBlock = self.builder.basicBlock
        trueBlockTerminates = self.builder.isLastTerminator()
        if not trueBlockTerminates:
            self.builder.branch(mergeBlock)

        ## False expression
        self.builder.beginBasicBlock(falseBlock)
        falseResult = self.translateLocalGraphValue(ifExpression.falseExpression)
        falseResultIncomingBlock = self.builder.basicBlock
        falseBlockTerminates = self.builder.isLastTerminator()
        if not falseBlockTerminates:
            self.builder.branch(mergeBlock)

        ## Merge
        self.builder.beginBasicBlock(mergeBlock)

        resultType = self.translateGraphValue(ifExpression.getType())
        if resultType.isVoidType():
            return resultType.getSingleton()

        #if trueBlockTerminates and falseBlockTerminates:
        assert False

    def visitDoWhileExpression(self, doWhileExpression: GHIRDoWhileExpression) -> HIRValue:
        resultType = self.translateGraphValue(doWhileExpression.getType())
        assert resultType.isVoidType()

        bodyBlock = self.builder.newBasicBlock('doWhileBody')
        continueBlock = self.builder.newBasicBlock('doWhileContinue')
        conditionBlock = self.builder.newBasicBlock('doWhileCondition')
        mergeBlock = self.builder.newBasicBlock('doWhileMerge')

        # Enter the loop.
        self.builder.branch(bodyBlock)

        # Loop body.
        self.builder.beginBasicBlock(bodyBlock)
        self.withBreakAndContinueDo(mergeBlock, continueBlock, lambda: self.translateGraphValue(doWhileExpression.bodyExpression))
        if not self.builder.isLastTerminator():
            self.builder.branch(continueBlock)

        # Continue.
        self.builder.beginBasicBlock(continueBlock)
        self.translateLocalGraphValue(doWhileExpression.continueExpression)
        if not self.builder.isLastTerminator():
            self.builder.branch(conditionBlock)
        
        # Condition
        self.builder.beginBasicBlock(conditionBlock)
        condition = self.translateLocalGraphValue(doWhileExpression.condition)
        self.builder.condBranch(condition, bodyBlock, mergeBlock)

        # Merge
        self.builder.beginBasicBlock(mergeBlock)
        return resultType.getSingleton()

    def visitWhileExpression(self, whileExpression: GHIRWhileExpression) -> HIRValue:
        resultType = self.translateGraphValue(whileExpression.getType())
        assert resultType.isVoidType()

        headerBlock = self.builder.newBasicBlock('whileHeader')
        bodyBlock = self.builder.newBasicBlock('whileBody')
        continueBlock = self.builder.newBasicBlock('whileContinue')
        mergeBlock = self.builder.newBasicBlock('whileMerge')

        # Enter the loop.
        self.builder.branch(headerBlock)

        # Loop header
        self.builder.beginBasicBlock(headerBlock)
        condition = self.translateGraphValue(whileExpression.condition)
        self.builder.condBranch(condition, bodyBlock, mergeBlock)

        # Loop body.
        self.builder.beginBasicBlock(bodyBlock)
        self.withBreakAndContinueDo(mergeBlock, continueBlock, lambda: self.translateLocalGraphValue(whileExpression.bodyExpression))
        if not self.builder.isLastTerminator():
            self.builder.branch(continueBlock)

        # Continue.
        self.builder.beginBasicBlock(continueBlock)
        self.translateLocalGraphValue(whileExpression.continueExpression)
        if not self.builder.isLastTerminator():
            self.builder.branch(headerBlock)
        
        # Merge
        self.builder.beginBasicBlock(mergeBlock)
        return resultType.getSingleton()

    def visitArraySubscriptAtExpression(self, subscriptExpression: GHIRArraySubscriptAtExpression) -> HIRValue:
        resultType = self.translateGraphValue(subscriptExpression.getType())
        array = self.translateGraphValue(subscriptExpression.array)
        index = self.translateGraphValue(subscriptExpression.index)
        if array.getType().isPointerLikeType():
            gepIndices = [HIRConstantPrimitiveInteger(self.context, self.context.uintPointerType, 0), index]
            if subscriptExpression.loadResult:
                elementPointerType = HIRPointerType(self.context, resultType)
                elementPointer = self.builder.getElementPointer(elementPointerType, array, gepIndices)
                return self.builder.load(resultType, elementPointer)
            else:
                return self.builder.getElementPointer(resultType, array, gepIndices)
        else:
            if subscriptExpression.loadResult:
                return self.builder.extractValue(resultType, array, [index])
            else:
                return self.builder.extractValueReference(resultType, array, [index])

    def visitPointerLikeLoadExpression(self, loadExpression: GHIRPointerLikeLoadExpression) -> HIRValue:
        resultType = self.translateGraphValue(loadExpression.getType())
        pointer = self.translateGraphValue(loadExpression.pointer)
        load = self.builder.load(resultType, pointer)
        load.isVolatile = loadExpression.isVolatile
        return load

    def visitPointerLikeStoreExpression(self, storeExpression: GHIRPointerLikeStoreExpression) -> HIRValue:
        pointer = self.translateGraphValue(storeExpression.pointer)
        value = self.translateGraphValue(storeExpression.value)
        store = self.builder.store(value, pointer)
        store.isVolatile = storeExpression.isVolatile
        return store

    def visitSequenceExpression(self, sequence: GHIRSequence) -> HIRValue:
        result = self.moduleFrontend.translateConstantTypedValue(VoidType.getSingleton())
        for element in sequence.expressions:
            result = self.translateGraphValue(element)
        return result

    def visitPointerLikeSubscriptAtExpression(self, subscriptExpression: GHIRPointerLikeSubscriptAtExpression) -> HIRValue:
        resultType = self.translateGraphValue(subscriptExpression.getType())
        pointer = self.translateGraphValue(subscriptExpression.pointer)
        index = self.translateGraphValue(subscriptExpression.index)

        assert False
