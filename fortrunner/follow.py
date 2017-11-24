from typing import Iterator, Union, List, Callable, Dict, Tuple
import re

'''
Simple flow interpretation of Fortran programs. Means: The interpreter does NOT understand Fortran
except for its flow syntax. It can generate the sequence of Fortran statements occuring in a specific
path through the program including subroutine calls, gotos, etc.
'''


class Event:
    '''
    One of

    - finite junction start (if, select)
    - finite junction end (end if, end select)
    - infinite junction start (do)
    - infinite junction end (do)
    - goto
    - cycle
    - exit
    - call (call, function call)
    - end of call (end subroutine, end function)
    - anything else
    '''

    def __init__(self, statement: str):
        '''
        :param statement: The Fortran statement causing the event (can span multiple lines)
        '''
        self.statement = statement

    def __str__(self) -> str:
        return self.statement + " |=| " + str(type(self))

class Use(Event):
    '''
    A USE statement
    '''
    def __init__(self, statement: str, modname: str):
        super().__init__(statement)
        self.modname = modname

class Block(Event):
    def __init__(self, statement: str, finite: bool):
        '''

        :param statement:
        :param finite: True for if & select, False for do and while
        '''
        super().__init__(statement)
        self.finite = finite


class EndOfBlock(Event):
    def __init__(self, statement: str):
        '''

        :param statement:
        '''


class LoopJump(Event):
    '''
    Jump to the end of the loop, optionally repeat loop (cycle)
    or leave it (exit)
    '''

    def __ini__(self, leave: bool):
        self.leave = leave


class Call:
    def __init__(self, target_name: str):
        self.target_name = target_name


class Goto:
    def __init__(self, label_name: str):
        self.label_name = label_name


JumpTarget = Union[Call, Goto, LoopJump]


class Jump(Event):
    def __init__(self, statement: str, target: JumpTarget):
        super().__init__(statement)
        self.target = target


def interpret_statement(statement: str, func_names: List[str]) -> Iterator[Event]:
    '''
    Interprets a single statement. Can yield one or more events.
    For example, if a statement contains multiple function calls, it will
    yield multiple events

    :param statement:
    :param func_names: lowercase names of all known functions in the current context
    :return:
    '''
    statement = statement.lower().strip()

    # check for function calls
    matches = re.searchiter(r"([0-9A-z_%]+)\s*\(")
    for match in matches:
        name = match.group(1)
        if name in func_names:
            yield match.group(1)

    if re.search(r"^(if|select\s+case)\s*(") is not None:
        yield Block(statement, finite=True)
    if re.search(r"^do") is not None:
        yield Block(statement, finite=False)
    match = re.search(r"^call ([^(]+)")
    if match is not None:
        yield Jump(statement, Call(match.group(1)))
    match = re.search(r"^goto ([0-9]+)")
    if match is not None:
        yield Jump(statement, Goto(match.group(1)))
    if re.search(r"^end ") is not None:
        yield EndOfBlock(statement)
    if re.search(r"^cycle ") is not None:
        yield Jump(statement, LoopJump(False))
    if re.search(r"^exit ") is not None:
        yield Jump(statement, LoopJump(True))
    match = re.search("^use ([0-9A-z]+)", line)
    if match is not None:
        yield Use(statement, match.group(1))

    # Anything else
    yield Event(statement)


def iter_statements(content: List[str]) -> Iterator[str]:
    '''
    Iterates over lines, yields statements

    :param content:
    :return:
    '''
    buffer = ""
    for line in content:
        line = line.split("!")[0].strip()
        if line.endswith("&"):
            buffer += line[:-1]
        else:
            buffer += line
            yield buffer
            buffer = ""

    yield buffer


def collect_routines(filename: str) -> Tuple[str, Optional[str], List[Tuple[str, int, int]]]:
    '''
    Reads fortran file, decides whether it is a "program", a "module" or a "flat" sequence of subroutines.
    Returns names and first & last line of each subroutine/function in the file
    :param filename:
    :return:
    '''
    with open(filename, "rt") as f:
        lines = f.readlines()

    fname = None # Default
    for line in lines:
        line = line.split("!")[0].lower().strip()

        match = re.search(r"^program\s+([0-9A-z_]+)", line)
        if match is not None:
            ftype = "program"
            fname = match.group(1)
            break

        match = re.search(r"^module\s+([0-9A-z_]+)", line)
        if match is not None:
            ftype = "module"
            fname = match.group(1)
            break

        if line.startswith("subroutine"):
            ftype = "flat"
            break

    def iter_routines():
        for i, line in enumerate(lines):
            line = line.split("!")[0].lower().strip()
            match = re.search(r"^subroutine\s+([A-z0-9_]+)", line)
            if match is not None:
                start = i
                routine_name = match.group(1)
            else:
                match = re.search(r"^([A-z0-9_()]+\s+)?function\s+([A-z0-9_]+)", line)
                if match is not None:
                    start = i
                    routine_name = match.group(2)

            if re.match(r"^end(\s+(subroutine|function))?$", line) is not None:
                yield routine_name, start, i

    return ftype, fname, list(iter_routines())

def follow_flow(routines: Callable[[str, int, int], List[str]],
                start_routine: str, line: int) -> Iterator[str]:
    '''
    Follows the program flow, always takes the first choice at junctions.
    :param routines: On calls, the callable asked for a list of program lines for subroutine/function of said name
    :param start_routine: Name of the subroutine/function to start exeuction at
    :param line: file line number to start execution at. Must lay inside start_routine block
    :return:
    '''
    raise Exception("not implemented")

