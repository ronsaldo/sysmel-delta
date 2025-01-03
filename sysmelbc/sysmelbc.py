#!/usr/bin/env python3

import sys
import json
import os.path
from sysmel.target import *
from sysmel.module import *

class FrontEndDriver:
    def __init__(self) -> None:
        self.module = None
        self.moduleName = None
        self.topFolder = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
        self.inputSourceFiles = []
        self.includeDirectories = [
            os.path.join(self.topFolder, 'module-sources')
        ]
        self.typecheckedSources = []
        self.outputFileName = 'a.out'
        self.verbose = False
        self.isDone = False
        self.emitSdvm = False
        self.emitObjectFile = False
        self.targetTriple = None
        self.compilationTarget = DefaultCompilationTarget
        self.sdvmModule = None
        self.keepIntermediates = False
        if sys.platform.startswith('win32'):
            self.sdvmPath = os.path.join(self.topFolder, 'build/bin/sdvm.exe')
        else:
            self.sdvmPath = os.path.join(self.topFolder, 'build/bin/sdvm')
        self.linkerCommand = 'clang'

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
-keep-intermediate          Keep the intermediate files.
-asg                        Use ASG based pipeline.
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
                elif arg in ['-keep-intermediate']:
                    self.keepIntermediates = True
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
                elif arg in ['-module-dir']:
                    if i >= len(argv):
                        self.printHelp()
                        return False

                    moduleDirectory = argv[i]
                    dirBaseName = os.path.basename(moduleDirectory)
                    self.moduleName = dirBaseName
                    moduleInputSource = os.path.join(moduleDirectory, 'module.sysmel')
                    self.inputSourceFiles.append(moduleInputSource)
                    i += 1
            else:
                self.inputSourceFiles.append(arg)
        return True

    def parseAndTypecheckSourceFile(self, sourceFile):
        from sysmel.parser import parseFileNamed
        from sysmel.parsetree import ParseTreeErrorVisitor
        from sysmel.syntax import ASGParseTreeFrontEnd
        from sysmel.analysis import expandAndTypecheck
        from sysmel.visualizations import asgToDotFileNamed, asgWithDerivationsToDotFileNamed
        from sysmel.environment import makeScriptAnalysisEnvironment
        from sysmel.mop import asgPredecessorTopoSortDo
        from sysmel.gcm import lambdaGCM

        parseTree = parseFileNamed(sourceFile)
        if not ParseTreeErrorVisitor().checkAndPrintErrors(parseTree):
            return False

        asgSyntax = ASGParseTreeFrontEnd().visitNode(parseTree)
        asgToDotFileNamed(asgSyntax, 'asgSyntax.dot')

        asgAnalyzed, asgTypecheckingErrors = expandAndTypecheck(makeScriptAnalysisEnvironment(self.compilationTarget, self.module, asgSyntax.sourceDerivation.getSourcePosition(), sourceFile, self), asgSyntax)
        asgToDotFileNamed(asgAnalyzed, 'asgAnalyzed.dot')
        asgWithDerivationsToDotFileNamed(asgAnalyzed, 'asgAnalyzedWithDerivation.dot')
        for error in asgTypecheckingErrors:
            sys.stderr.write('%s\n' % error.prettyPrintError())
        self.typecheckedSources.append(asgAnalyzed)

        #exportedValueSet = asgAnalyzed.findExportedValueSet()
        #for exportedValue in exportedValueSet:
        #    if exportedValue.isLambda():
        #        lambdaGcm = lambdaGCM(exportedValue)
        #        interpretableLambda = lambdaGcm.asInterpretableInstructions()
        #        interpretableLambda.dumpDotToFileNamed('interpretableLambda.dot')

        return len(asgTypecheckingErrors) == 0

    def parseAndTypecheckSourceFiles(self):
        if self.moduleName is None:
            self.moduleName, ext = os.path.splitext(os.path.basename(self.inputSourceFiles[0]))
            self.module = Module(self.moduleName, self.compilationTarget)
        elif self.moduleName is not None and self.module is None:
            self.module = Module(self.moduleName, self.compilationTarget)
        success = True
        for inputSource in self.inputSourceFiles:
            if not self.parseAndTypecheckSourceFile(inputSource):
                success = False
        return success

    def evaluateTypecheckedSource(self, typecheckedSource):
        from sysmel.gcm import topLevelScriptGCM
        gcm = topLevelScriptGCM(typecheckedSource)
        interpretableScript = gcm.asInterpretableInstructions()
        scriptResult = interpretableScript.evaluateInModuleWithArguments(self.module)
        return scriptResult

    def evaluateTypecheckedSources(self):
        for typecheckedSource in self.typecheckedSources:
            evalResult = self.evaluateTypecheckedSource(typecheckedSource)
            if self.verbose and evalResult is not None:
                print(evalResult)
        return True
    
    def generateMIR(self):
        from sysmel.mir import expandModuleIntoMir
        from sysmel.visualizations import asgToDotFileNamed, asgWithDerivationsToDotFileNamed
        mir, mirExpansionErrors = expandModuleIntoMir(DefaultCompilationTarget, self.module)
        for error in mirExpansionErrors:
            sys.stderr.write('%s\n' % error.prettyPrintError())

        asgToDotFileNamed(mir, 'asgMir.dot')
        asgWithDerivationsToDotFileNamed(mir, 'asgMirWithDerivation.dot')
        return len(mirExpansionErrors) == 0

    def compileSDVMModule(self):
        from sysmel.sdvmFrontend import SDVMModuleFrontEnd
        self.sdvmModule = SDVMModuleFrontEnd(self.compilationTarget).compileModule(self.module)
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
        
        # Generate the MIR
        if not self.generateMIR():
            return False

        if not self.compileSDVMModule():
            return False

        # Save the sdvm module.
        sdvmModuleFile = self.outputFileName + '.sdvm'
        objectFileName = self.outputFileName + '.o'
        if self.emitSdvm:
            self.sdvmModule.saveToFileNamed(self.outputFileName)
            return True

        self.sdvmModule.saveToFileNamed(sdvmModuleFile)
        # Compile the sdvm module into an object file.
        if self.emitObjectFile:
            objectFileName = self.outputFileName

        if self.targetTriple is not None:
            sdvmCommand = '%s -target %s -o %s %s' % (self.sdvmPath, self.targetTriple, objectFileName, sdvmModuleFile)
        else:
            sdvmCommand = '%s -o %s %s' % (self.sdvmPath, objectFileName, sdvmModuleFile)
        sdvmExitCode = os.system(sdvmCommand)
        if not self.keepIntermediates:
            os.unlink(sdvmModuleFile)
        if sdvmExitCode != 0:
            return False

        if self.emitObjectFile:
            return True

        # Link the executable.
        linkCommand = '%s -o %s %s' % (self.linkerCommand, self.outputFileName, objectFileName)
        sdvmExitCode = os.system(linkCommand)

        if not self.keepIntermediates:
            os.unlink(objectFileName)
        if sdvmExitCode != 0:
            return False

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
