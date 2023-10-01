import sys
from antlr4 import *
from stella.stellaParser import stellaParser
from stella.stellaLexer import stellaLexer


class Handler:

    def __init__(self):
        self.variables = {
            '0': 'Nat',
            '1': 'Nat',
            'true': 'Bool',
            'false': 'Bool',
        }
        self.functions = {}

    def handle_expr_context(
            self,
            ctx: stellaParser.ExprContext,
    ):
        """
        handles expression context, checks type consistency of expression.
        passes: stellaParser.ExprContext instance.
        returns: actual type of expression.
        """
        pass

    def handle_decl_context(self, ctx: stellaParser.DeclContext):
        """
        handles declaration context, checks type consistency of declaration and its return expression.
        passes: stellaParser.DeclContext instance.
        returns nothing if typecheck is successfully passed, raises corresponding log message otherwise.
        """
        print(vars(ctx))
        pass

    def handle_program_context(self, ctx: stellaParser.ProgramContext):
        """
        handles program context
        iterates through ctx.decl to typecheck every declaration
        passes: stellaParser.ProgramContext instance
        """

        for declaration in ctx.decls:
            self.handle_decl_context(declaration)


def main():

    from os import listdir
    from os.path import isfile, join

    well_path = 'C:\\Users\phili\PycharmProjects\\advanced_compiler\\tests\\core\\well-typed'
    ill_path = 'C:\\Users\phili\PycharmProjects\\advanced_compiler\\tests\\core\\ill-typed'

    well_files = [f'{well_path}\\{f}' for f in listdir(well_path) if isfile(join(well_path, f))]
    ill_files = [f'{ill_path}\\applying-non-function-1.stella']

    # files = well_files + ill_files
    files = [f'{well_path}\\factorial.stella']

    for file in files:

        print(f'---------------{file.replace(well_path, "").replace(ill_path, "")}---------------')

        input_stream = FileStream(file)

        lexer = stellaLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = stellaParser(stream)

        program = parser.program()
        handler = Handler()
        handler.handle_program_context(program)


if __name__ == '__main__':
    main()
