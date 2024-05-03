#!/usr/bin/env python3

import sys
import json
import os.path

class FrontEndDriver:
    def __init__(self) -> None:
        self.module = None
        self.moduleName = None
        self.inputSourceFiles = []
        self.includeDirectories = []
        self.typecheckedSources = []
        self.outputFileName = 'a.out'
        self.verbose = False
        self.isDone = False
        self.emitSdvm = False
        self.emitObjectFile = False
        self.targetTriple = ''
        self.ghirModule = None
        self.hirModule = None
        self.mhirModule = None
        self.sdvmModule = None

    def printHelp(self):
        print(
"""sysmelbc.py [options] <input files>* [-- <evaluation args> ]
-h -help --help             Prints this message.
-version --version          Prints the version information.
-v                          Enable the verbosity in the output.
-target <triple>            Sets the target platform
-emit-sdvm                  Emits the sdvm module.
-module <name>              Sets the module name. By default is the first source basename.
-I<Dir>                     Adds an include directory.
-c                          Emits object file.
-o                          Sets the output file name.
"""
        )

    def printVersion(self):
        print("sysmelbc.py version 0.1")

    def parseCommandLineArguments(self, argv):
        i = 1
        while i < len(argv):
            arg = argv[i]
            i += 1
            if len(arg) > 0 and arg[0] == '-':
                if arg in ['-h', '-help', '--help']:
                    self.printHelp()
                    self.isDone = True
                    return True
                elif arg in ['-version', '--version']:
                    self.printVersion()
                    self.isDone = True
                    return True
                elif arg in ['-v']:
                    self.verbose = True
                elif arg in ['-c']:
                    self.emitObjectFile = True
                elif arg in ['-emit-sdvm']:
                    self.emitSdvm = True
                elif arg in ['-o']:
                    if i >= len(argv):
                        self.printHelp()
                        return False

                    self.outputFileName = argv[i]
                    i += 1
                elif arg in ['-target']:
                    if i >= len(argv):
                        self.printHelp()
                        return False

                    self.targetTriple = argv[i]
                    i += 1
                elif arg in ['-module']:
                    if i >= len(argv):
                        self.printHelp()
                        return False

                    self.moduleName = argv[i]
                    i += 1
            else:
                self.inputSourceFiles.append(arg)
        return True

    def parseAndTypecheckSourceFile(self, sourceFile):
        from sysmel.parser import parseFileNamed
        from sysmel.ast import ASTErrorVisitor
        from sysmel.typechecker import Typechecker
        from sysmel.environment import makeScriptAnalysisEnvironment
        ast = parseFileNamed(sourceFile)
        if not ASTErrorVisitor().checkASTAndPrintErrors(ast):
            return False

        typechecked, typecheckedSucceeded = Typechecker(makeScriptAnalysisEnvironment(self.module, ast.sourcePosition, sourceFile)).typecheckASTAndPrintErrors(ast)
        self.typecheckedSources.append(typechecked)
        return typecheckedSucceeded

    def parseAndTypecheckSourceFiles(self):
        from sysmel.value import Symbol, Module
        if self.moduleName is None:
            self.moduleName, ext = os.path.splitext(os.path.basename(self.inputSourceFiles[0]))
            self.module = Module(Symbol.intern(self.moduleName))

        success = True
        for inputSource in self.inputSourceFiles:
            if not self.parseAndTypecheckSourceFile(inputSource):
                success = False
        return success

    def evaluateTypecheckedSource(self, typecheckedSource):
        from sysmel.environment import FunctionalActivationEnvironment
        from sysmel.eval import ASTEvaluator
        return ASTEvaluator(FunctionalActivationEnvironment()).evaluate(typecheckedSource)

    def evaluateTypecheckedSources(self):
        for typecheckedSource in self.typecheckedSources:
            evalResult = self.evaluateTypecheckedSource(typecheckedSource)
            if self.verbose:
                print(evalResult.prettyPrint())
        return True
    
    def compileGHIRModule(self):
        from sysmel.ghir import GHIRModuleFrontend
        self.ghirModule = GHIRModuleFrontend().compileModule(self.module)
        if self.verbose:
            print('-'*60)
            print('GHIR:')
            print('-'*60)
            print(self.ghirModule.prettyPrint())

        return True

    def compileHIRModule(self):
        from sysmel.hir import HIRModuleFrontend
        self.hirModule = HIRModuleFrontend().compileGraphModule(self.ghirModule)
        if self.verbose:
            print('-'*60)
            print('HIR:')
            print('-'*60)
            print(self.hirModule.prettyPrint())

        return True

    def compileMIRModule(self):
        from sysmel.mir import MIRModuleFrontend
        self.mirModule = MIRModuleFrontend().compileHIRModule(self.hirModule)
        if self.verbose:
            print('-'*60)
            print('MIR:')
            print('-'*60)
            print(self.mirModule.prettyPrint())

        return True

    def compileSDVMModule(self):
        from sysmel.sdvmFrontend import SDVMModuleFrontEnd
        self.sdvmModule = SDVMModuleFrontEnd().compileMIRModule(self.mirModule)
        if self.verbose:
            print('-'*60)
            print('SDVM:')
            print('-'*60)
            print(self.sdvmModule.prettyPrint())

        return True

    def runPipeline(self):
        if not self.parseAndTypecheckSourceFiles():
            return False
        if not self.evaluateTypecheckedSources():
            return False

        if not self.compileGHIRModule():
            return False
        if not self.compileHIRModule():
            return False
        if not self.compileMIRModule():
            return False
        if not self.compileSDVMModule():
            return False
        
        self.sdvmModule.saveToFileNamed(self.outputFileName)
        return True
    
    def main(self, argv):
        if not self.parseCommandLineArguments(argv):
            return False
        if len(self.inputSourceFiles) == 0:
            self.printHelp()
            return True
        return self.runPipeline()    

if __name__ == "__main__":
    if not FrontEndDriver().main(sys.argv):
        sys.exit(1)
