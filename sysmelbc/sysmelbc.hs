import Sysmel.Scanner
import System.Environment  
import Data.List
import Data.Tuple

main = do
    args <- getArgs
    inputFileContents <- mapM readFile args
    putStrLn "The inputFiles are"
    mapM (print . scanSourceCode . uncurry SourceCode) (zip args inputFileContents)
