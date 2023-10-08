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


def repr_type(ctx) -> str:

    def represent(fun_ctx):

        if isinstance(fun_ctx, stellaParser.TypeParensContext):
            return represent(fun_ctx.type_)

        elif not isinstance(fun_ctx, stellaParser.TypeFunContext):
            return f'{fun_ctx.__repr__()}'

        else:
            return f'(fn({fun_ctx.paramTypes[0].__repr__()})->{represent(fun_ctx.returnType)})'

    answer = represent(ctx)

    if answer[0] == '(':
        return answer[1:-1]
    return answer


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
        """

        # print(ctx.getText(), type(ctx))
        # print(repr_type(ctx_type))
        # print('\n')

        if isinstance(ctx, stellaParser.VarContext):
            """
            handles variables context
            passes: stellaParser.VarContext
            """

            try:
                ctx_type = ctx_type.type_
            except AttributeError:
                pass

            actual_type = repr_type(variables[ctx.name.text]['return_type'])
            expected_type = repr_type(ctx_type)

            if not expected_type == actual_type:
                raise RuntimeError(f'[TYPE ERROR] At {ctx.name.line}:{ctx.name.column} - expected variable type: '
                                   f'{expected_type}, actual type: {actual_type}\n'
                                   f'{highlight_error(self.file_name, ctx.name.line, ctx.name.column)}')

        elif isinstance(ctx, stellaParser.ParamDeclContext):
            """
            ---
            """

            if not repr_type(ctx_type) == repr_type(ctx.paramType):
                raise RuntimeError(f'[TYPE ERROR] At {ctx.name.line}:{ctx.name.column} - expected variable type: '
                                   f'{repr_type(ctx_type)}, actual type: {repr_type(ctx.paramType)}\n'
                                   f'{highlight_error(self.file_name, ctx.name.line, ctx.name.column)}')

        elif isinstance(ctx, stellaParser.SuccContext):
            """
            handles succ() context
            passes: stellaParser.SuccContext instance
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
            """
            ---
            """

            # print(f'ABSTRACTION: {vars(ctx)}')

            variables.update({
                ctx.paramDecls[0].name.text: {
                    'return_type': ctx.paramDecls[0].paramType,
                },
            })

            if isinstance(ctx_type, stellaParser.TypeParensContext):
                ctx_type = ctx_type.type_

            self.handle_expr_context(
                ctx=ctx.paramDecls[0],
                ctx_type=ctx_type.paramTypes[0],
                variables=variables,
            )

            self.handle_expr_context(
                ctx=ctx.returnExpr,
                ctx_type=ctx_type.returnType,
                variables=variables
            )

        elif isinstance(ctx, stellaParser.ApplicationContext):
            """
            ---
            """

            print(ctx.getText())
            print(vars(ctx))
            print(ctx.args[0].getText())
            print(repr_type(ctx_type))
            print('\n')

            function_type = variables[ctx.fun.getText().split('(')[0]]
            # print(f'ABOBA: {repr_type(variables[ctx.fun.getText().split("(")[0]]["return_type"])}')
            # print(repr_type(ctx_type))
            # print(f'ABOBA: {ctx.getText()}, {ctx.args[0].getText()}, {ctx.fun.getText()}, {repr_type(ctx_type)}')
            # print(repr_type(function_type['param_type']))

            self.handle_expr_context(
                ctx=ctx.args[0],
                ctx_type=ctx_type,
                variables=variables,
            )

            self.handle_expr_context(
                ctx=ctx.fun,
                ctx_type=function_type['return_type']
            )

        elif isinstance(ctx, stellaParser.NatRecContext):

            self.handle_expr_context(
                ctx=ctx.n,
                ctx_type=stellaParser.TypeNatContext(
                    ctx=ctx,
                    parser=ctx.parser,
                ),
                variables=variables,
            )

            self.handle_expr_context(
                ctx=ctx.initial,
                ctx_type=ctx_type,
                variables=variables,
            )

            initial_type = variables[ctx.initial.getText()]['return_type']

            expected_step_return_expr_type = stellaParser.TypeFunContext(
                parser=initial_type.parser,
                ctx=ctx.initial,
            )

            expected_step_return_expr_type.paramTypes = [initial_type]
            expected_step_return_expr_type.returnType = initial_type

            expected_step_type = stellaParser.TypeFunContext(
                parser=initial_type.parser,
                ctx=ctx.initial,
            )

            expected_step_type.paramTypes = [initial_type]
            expected_step_type.returnType = expected_step_return_expr_type

            self.handle_expr_context(
                ctx.step,
                ctx_type=expected_step_type,
                variables=variables,
            )

        elif isinstance(ctx, stellaParser.ConstIntContext):
            if not 'Nat' == repr_type(ctx_type):
                raise RuntimeError(
                    f'[TYPE ERROR] {ctx.n.line}:{ctx.n.column} - expected variable type: '
                    f'{repr_type(ctx_type)}, actual type: Nat\n'
                    f'{highlight_error(self.file_name, ctx.n.line, ctx.n.column)}'
                )

        elif isinstance(ctx, stellaParser.ConstTrueContext):
            if not 'Bool' == repr_type(ctx_type):
                raise RuntimeError(
                    f'[TYPE ERROR] {ctx.name.line}:{ctx.name.column} - expected variable type: '
                    f'{repr_type(ctx_type)}, actual type: Bool\n'
                    f'{highlight_error(self.file_name, ctx.name.line, ctx.name.column)}'
                )

        elif isinstance(ctx, stellaParser.ConstFalseContext):
            if not 'Bool' == repr_type(ctx_type):
                raise RuntimeError(
                    f'[TYPE ERROR] {ctx.name.line}:{ctx.name.column} - expected variable type: '
                    f'{repr_type(ctx_type)}, actual type: Bool\n'
                    f'{highlight_error(self.file_name, ctx.name.line, ctx.name.column)}'
                )

        elif isinstance(ctx, stellaParser.IfContext):
            print(vars(ctx))

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

            self.functions.update({
                ctx.name.text: {
                    'param_type': ctx.paramDecls[0].paramType,
                    'return_type': ctx.returnType,
                }
            })

            variables = {}

            for parameter in ctx.paramDecls:
                if isinstance(parameter.paramType, stellaParser.TypeFunContext):
                    variables[parameter.name.text] = {
                        'return_type': parameter.paramType.returnType,
                        'param_type': parameter.paramType.paramTypes[0],
                    }
                else:
                    variables[parameter.name.text] = {
                        'return_type': parameter.paramType
                    }

            variables.update(self.functions)
            variables.update({

                '0': {
                    'return_type': stellaParser.TypeNatContext(
                        ctx=ctx,
                        parser=ctx.parser,
                    )
                },

                '1': {
                    'return_type': stellaParser.TypeNatContext(
                        ctx=ctx,
                        parser=ctx.parser,
                    )
                },

                'true': {
                    'return_type': stellaParser.TypeBoolContext(
                        ctx=ctx,
                        parser=ctx.parser,
                    )
                },

                'false': {
                    'return_type': stellaParser.TypeBoolContext(
                        ctx=ctx,
                        parser=ctx.parser,
                    )
                },
            })

            self.handle_expr_context(
                ctx=ctx.returnExpr,
                ctx_type=ctx.returnType,
                variables=variables,
            )

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
