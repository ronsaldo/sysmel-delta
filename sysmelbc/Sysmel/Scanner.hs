module Sysmel.Scanner
(
    SourceCode(..),
    ScanChar(..),
    scanSourceCode
) where
    
import Data.Char

data SourceCode = SourceCode {name :: String, contents :: String } deriving(Show)
data SourcePosition = SourcePosition {
    sourceCode :: SourceCode,
    startPosition :: Int, startLine :: Int, startColumn :: Int,
    endPosition :: Int, endLine :: Int, endColumn :: Int
} deriving(Show)
data CharPosition = CharPosition {position :: Int, line :: Int, column :: Int} deriving(Show)

data ScanChar = ScanChar { scanChar :: Char, scanCharPosition :: CharPosition} deriving(Show)
data ScanCharState = ScanCharState {scanCharStatePosition :: CharPosition, scanCharStateIsPreviousCR :: Bool }

advanceScanCharState :: ScanCharState -> Char -> ScanCharState
advanceScanCharState ScanCharState{scanCharStatePosition=CharPosition{position=position, line=line, column=column}, scanCharStateIsPreviousCR= _} '\r'
    = ScanCharState{scanCharStatePosition=CharPosition{position=position + 1, line=line + 1, column=1}, scanCharStateIsPreviousCR=True}

advanceScanCharState ScanCharState{scanCharStatePosition=CharPosition{position=position, line=line, column=column}, scanCharStateIsPreviousCR=False} '\n'
    = ScanCharState{scanCharStatePosition=CharPosition{position=position + 1, line=line + 1, column=1}, scanCharStateIsPreviousCR=False}
advanceScanCharState ScanCharState{scanCharStatePosition=CharPosition{position=position, line=line, column=column}, scanCharStateIsPreviousCR=True} '\n'
    = ScanCharState{scanCharStatePosition=CharPosition{position=position + 1, line=line, column=column}, scanCharStateIsPreviousCR=False}

advanceScanCharState ScanCharState{scanCharStatePosition=CharPosition{position=position, line=line, column=column}, scanCharStateIsPreviousCR= _} '\t'
    = ScanCharState{scanCharStatePosition=CharPosition{position=position + 1, line=line, column=column + 1}, scanCharStateIsPreviousCR=False}

advanceScanCharState ScanCharState{scanCharStatePosition=CharPosition{position=position, line=line, column=column}, scanCharStateIsPreviousCR= _} _
    = ScanCharState{scanCharStatePosition=CharPosition{position=position + 1, line=line, column=column + 1}, scanCharStateIsPreviousCR=False}

scanCharsWithState :: [Char] -> ScanCharState -> [ScanChar]
scanCharsWithState [] _ = []
scanCharsWithState (c:tail) state
    = ScanChar{scanChar = c, scanCharPosition=position} : scanCharsWithState tail (advanceScanCharState state c)
    where ScanCharState{scanCharStatePosition = position, scanCharStateIsPreviousCR = isPreviousCR} = state

scanChars :: [Char] -> [ScanChar]
scanChars chars = scanCharsWithState chars ScanCharState{scanCharStatePosition=CharPosition{position=0, line=1, column=1}, scanCharStateIsPreviousCR=False}

scanSourceCode :: SourceCode -> [ScanChar]
scanSourceCode SourceCode{name=name, contents=contents} = scanChars contents
