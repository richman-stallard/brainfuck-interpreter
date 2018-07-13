#!/usr/bin/python2

import sys
import os

class TSyntaxElement:
    fStateMachine = None # This is set by TProgram.
    def __init__(self, aCode):
        self.fCode = aCode
        self.fElements = []
        self.fParsedLength = self.Parse()
    def Parse(self):
        """ TSyntaxElement.Parse
        Override this function!
        """
        return 0
    def Execute(self):
        """ TSyntaxElement.Execute
        Override this function!
        """
        return 0

class TProgram(TSyntaxElement):
    """ TProgram
    <CodeBlock>
    """
    def Parse(self):
        assert len(self.fCode) > 0, "Empty program."
        self.fElements = [TCodeBlock(self.fCode)]
        return 0
    def Execute(self):
        return self.fElements[0].Execute()
    def SetStateMachine(self, aStateMachine):
        TSyntaxElement.fStateMachine = aStateMachine
        
class TCodeBlock(TSyntaxElement):
    """ TCodeBlock
    [ <Expression> ]
    """
    def Parse(self):
        if len(self.fCode) == 0:
            self.fElements = []
        else:
            self.fElements = [TExpression(self.fCode)]
        return 0
    def Execute(self):
        return 0 if self.fElements == [] else self.fElements[0].Execute()
    
class TExpression(TSyntaxElement):
    """ TExpression
    ( <Command> <TCodeBlock> | <[> <TLoop> <]> <TCodeBlock> )
    """
    def Parse(self):
        assert len(self.fCode) > 0, "Empty expression."
        if not self.fCode[0] == '[': # Command
            self.fElements = [
                TCommand(self.fCode[0]),
                TCodeBlock(self.fCode[1:])
            ]
        else: # Loop
            vNestLevel = 0
            for (vLoopEndIdx, vChar) in enumerate(self.fCode):
                if vChar == '[':
                    vNestLevel += 1
                elif vChar == ']':
                    vNestLevel -= 1
                    if vNestLevel == 0:
                        break
            else:
                raise AssertionError("Missing closing bracket(s).")
            self.fElements = [
                TLoop(self.fCode[1:vLoopEndIdx]),
                TCodeBlock(self.fCode[vLoopEndIdx + 1:])
            ]
        return 0
    def Execute(self):
        return self.fElements[0].Execute() + self.fElements[1].Execute()
    
class TLoop(TSyntaxElement):
    """ TLoop
    <CodeBlock>
    """
    def Parse(self):
        self.fElements = [TCodeBlock(self.fCode)]
        return 0
    def Execute(self):
        Result = 0
        while not self.fStateMachine.GetCurrentMemVal() == 0:
            Result = Result + self.fElements[0].Execute()
        return Result
    
class TCommand(TSyntaxElement):
    """ TCommand
    ( < | > | , | . | - | + )
    """
    def Parse(self):
        assert len(self.fCode) == 1, "Command too long."
        assert self.fCode in "<>,.-+", "Unknown command: " + self.fCode
        self.fElements = [self.fCode]
        return 0
    def Execute(self):
        cmd = self.fElements[0]
        if cmd == '<':
            return self.fStateMachine.DecMemPtr()
        elif cmd == '>':
            return self.fStateMachine.IncMemPtr()
        elif cmd == ',':
            return self.fStateMachine.ReadInBuf()
        elif cmd == '.':
            return self.fStateMachine.WrtOutBuf()
        elif cmd == '-':
            return self.fStateMachine.DecMemVal()
        elif cmd == '+':
            return self.fStateMachine.IncMemVal()
        else:
            raise RuntimeError("Unknown command: " + cmd)

class TStateMachine:
    def __init__(self):
        self.fInputBuffer = u""
        self.fOutputBuffer = u""
        self.fMemory = [0]
        self.fMemPtr = 0
        
    # Getters
    def GetOutputBuffer(self):
        return self.fOutputBuffer
    def GetCurrentMemVal(self):
        return self.fMemory[self.fMemPtr]
        
    # Setters
    def SetInputBuffer(self, aInputBuffer):
        self.fInputBuffer = aInputBuffer[:]
        
    # Brainfuck commands.
    def IncMemPtr(self):
        self.fMemPtr += 1
        if self.fMemPtr == len(self.fMemory):
            self.fMemory.append(0)
        return 0
    def DecMemPtr(self):
        # Inefficient implementation but oh well.
        self.fMemPtr -= 1
        if self.fMemPtr < 0:
            self.fMemPtr = 0
            tmp = self.fMemory[:]
            self.fMemory = [0]
            for ele in tmp:
                self.fMemory.append(ele)
        return 0
    def IncMemVal(self):
        self.fMemory[self.fMemPtr] += 1
        return 0
    def DecMemVal(self):
        self.fMemory[self.fMemPtr] -= 1
        return 0
    def WrtOutBuf(self):
        self.fOutputBuffer += unichr(self.fMemory[self.fMemPtr])
        return 0
    def ReadInBuf(self):
        vInChar = 0
        if len(self.fInputBuffer) > 0:
            vInChar = ord(self.fInputBuffer[0])
            self.fInputBuffer = self.fInputBuffer[1:]
        self.Memory[self.fMemPtr] = vInChar
        return 0
        
def main(argv):
    # Handle CLI args.
    vDebug = False
    if "-h" in argv[1:]:
        # Load help text file.
        try:
            (vBrainfuckDir, vBrainfuckFile) = \
                os.path.split(os.path.normpath(argv[0]))
            (vBrainfuckBase, vDelim, vPostfix) = vBrainfuckFile.rpartition('.')
            vBrainfuckHelpFile = os.path.join(
                vBrainfuckDir,
                vBrainfuckBase  + ".man"
            )
            with open(vBrainfuckHelpFile, 'r') as fp:
                print fp.read()
        except IOError:
            # If not found, display default help text.
            print "Brainfuck interpreter"
            print
            print "Help file not found!"
        finally:
            return 0
    else:
        if "-v" in argv[1:]:
            vDebug = True
            argv.remove("-v")
        assert len(argv) == 3, "Missing or too many arguments. Use -h for help."
        (vInterpreterPath, vCode, vInput) = argv
    
    # Initialize state machine.
    vStateMachine = TStateMachine()
    vStateMachine.SetInputBuffer(vInput)
    if vInput[0] == '-': # Read from CLI.
        vInput = vInput[1:]
    else:
        vInput = os.path.normpath(vInput)
        assert os.path.isfile(vInput), "Could not find input file " + vInput
        with open(vInput, 'r') as fp:
            vInput = fp.read()
    vStateMachine.SetInputBuffer(vInput)
    
    # Read program.
    if vCode[0] == '-': # Read from CLI.
        vCode = vCode[1:]
    else: # Read from file.
        vCode = os.path.normpath(vCode)
        assert os.path.isfile(vCode), "Could not find program file " + vCode
        with open(vCode, 'r') as fp:
            vCode = fp.read()
    # Remove comments.
    vCode = vCode.split('\n')
    for (idx, line) in enumerate(vCode):
        if '#' in line:
            vCode[idx] = line[:line.find('#')]
    # Remove whitespace.
    vCode = ''.join(vCode) # newlines
    vCode = vCode.replace(' ', '') # spaces
    vCode = vCode.replace('\t', '') # tabs
    
    # Create new TProgram object (parse code).
    vProgram = TProgram(vCode)
    
    # Assign state machine to program and execute.
    vProgram.SetStateMachine(vStateMachine)
    vProgram.Execute()
    
    # Output to stdout.
    if vDebug:
        print "Memory after execution:"
        print vStateMachine.fMemory
    print vStateMachine.GetOutputBuffer()
    
if __name__ == "__main__":
    main(sys.argv)