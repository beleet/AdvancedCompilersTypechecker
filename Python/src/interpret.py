import sys
import antlr4.Token
from antlr4 import *
from stella.stellaParser import stellaParser
from stella.stellaLexer import stellaLexer


def highlight_error(
        file_name: str,
        line: int,
        column: int,
):
    with open(file_name, 'r') as file:

        error_string = None

        for _ in range(line):
            error_string = file.readline()

        return error_string + '\n' + ' ' * column + '^'


class Handler:

    def __init__(self, file_name: str):

        self.variables = {
            '0': 'Nat',
            '1': 'Nat',
            'true': 'Bool',
            'false': 'Bool',
        }

        self.functions = {}

        self.file_name = file_name

    def handle_expr_context(
            self,
            ctx: stellaParser.ExprContext,
            ctx_type,
            variables: dict,
    ):
        """
        handles expression context, checks type consistency of expression.
        passes: stellaParser.ExprContext instance.
        returns: actual type of expression.
        """

        if isinstance(ctx, stellaParser.VarContext):
            """
            ---
            """

            actual_type = variables[ctx.name.text].__repr__()
            expected_type = ctx_type.__repr__()

            if not expected_type == actual_type:
                raise RuntimeError(f'[TYPE ERROR] At {ctx.name.line}:{ctx.name.column} - expected type: '
                                   f'{expected_type}, actual type: {actual_type}\n'
                                   f'{highlight_error(self.file_name, ctx.name.line, ctx.name.column)}')

        elif isinstance(ctx, stellaParser.SuccContext):
            """
            ---
            """

            self.handle_expr_context(
                ctx=ctx.n,
                ctx_type=ctx_type,
                variables=variables,
            )

        elif isinstance(ctx, stellaParser.SequenceContext):
            """
            ---
            """
            return self.handle_expr_context(
                ctx=ctx.expr1,
                ctx_type=ctx_type,
                variables=variables,
            )

        elif isinstance(ctx, stellaParser.AbstractionContext):
            # TODO: check paramTypes
            param_types = ctx_type.type_.paramTypes
            # print(type(param_types[0]))

            print(type(ctx_type.type_.returnType))

        else:
            raise RuntimeError(f'{ctx.__class__.__name__} is not implemented')

    def handle_decl_context(
            self,
            ctx: stellaParser.DeclContext,
    ):
        """
        handles declaration context, checks type consistency of declaration and its return expression.
        passes: stellaParser.DeclContext instance.
        returns nothing if typecheck is successfully passed, raises corresponding log message otherwise.
        """

        if isinstance(ctx, stellaParser.DeclFunContext):

            self.handle_expr_context(
                ctx=ctx.returnExpr,
                ctx_type=ctx.returnType,
                variables={
                    parameter.name.text: parameter.paramType for parameter in ctx.paramDecls
                }
            )

            # print(ctx.name.text, ctx.paramDecls, ctx.returnType, ctx.returnExpr)
            # print({parameter.name.text: parameter.paramType for parameter in ctx.paramDecls})
            # print('\n')

    def handle_program_context(
            self,
            ctx: stellaParser.ProgramContext,
    ):
        """
        handles program context
        iterates through ctx.decl to typecheck every declaration
        passes: stellaParser.ProgramContext instance
        """

        for declaration in ctx.decls:
            try:
                self.handle_decl_context(declaration)
            except RuntimeError as type_error:
                print(type_error)


def main():

    from os import listdir
    from os.path import isfile, join

    well_path = 'C:\\Users\phili\PycharmProjects\\advanced_compiler\\tests\\core\\well-typed'
    ill_path = 'C:\\Users\phili\PycharmProjects\\advanced_compiler\\tests\\core\\ill-typed'

    well_files = [f'{well_path}\\{f}' for f in listdir(well_path) if isfile(join(well_path, f))]
    ill_files = [f'{ill_path}\\applying-non-function-1.stella']

    # files = well_files + ill_files
    files = [f'{well_path}\\simple-program.stella']

    for file in files:

        print(f'---------------{file.replace(well_path, "").replace(ill_path, "")}---------------')

        input_stream = FileStream(file)

        lexer = stellaLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = stellaParser(stream)

        program = parser.program()
        handler = Handler(
            file_name=file,
        )
        handler.handle_program_context(
            ctx=program,
        )


if __name__ == '__main__':
    main()
