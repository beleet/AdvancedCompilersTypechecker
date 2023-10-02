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
        """

        if isinstance(ctx, stellaParser.VarContext):
            """
            handles variables context
            passes: stellaParser.VarContext
            """

            try:
                ctx_type = ctx_type.type_
            except AttributeError:
                pass

            actual_type = variables[ctx.name.text].getText()
            expected_type = ctx_type.getText()

            if not expected_type == actual_type:
                raise RuntimeError(f'[TYPE ERROR] At {ctx.name.line}:{ctx.name.column} - expected variable type: '
                                   f'{expected_type}, actual type: {actual_type}\n'
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

            try:
                ctx_type = ctx_type.type_
            except AttributeError:
                pass
            #
            # print(ctx_type.getText(), ctx.getText())

            ctx_type_param = ctx_type.paramTypes[0].getText()
            abstraction_param_type = ctx.paramDecls[0].paramType.getText()

            if not ctx_type_param == abstraction_param_type:
                raise RuntimeError(
                    f'[TYPE ERROR] At {ctx.paramDecls[0].name.line}:{ctx.paramDecls[0].name.column} -'
                    f' expected parameter type: '
                    f'{abstraction_param_type}, actual type: {ctx_type_param}\n'
                    f'{highlight_error(self.file_name, ctx.paramDecls[0].name.line, ctx.paramDecls[0].name.column)}'
                )

            variables.update({
                ctx.paramDecls[0].name.text: ctx.paramDecls[0].paramType,
            })

            self.handle_expr_context(
                ctx=ctx.returnExpr,
                ctx_type=ctx_type.returnType,
                variables=variables,
            )

        elif isinstance(ctx, stellaParser.ApplicationContext):
            """
            ---
            """

            application_function = ctx.fun.getText()
            expected_application_param_type = self.functions[application_function]['param_type'].getText()
            expected_application_return_type = self.functions[application_function]['return_type'].getText()

            application_param_name = ctx.args[0].getText()
            actual_application_param_type = variables[application_param_name].getText()
            actual_application_return_type = ctx_type.getText()

            if not expected_application_param_type == actual_application_param_type:
                raise RuntimeError(
                    f'[TYPE ERROR] At {ctx.args[0].name.line}:{ctx.args[0].name.column} - expected parameter type: '
                    f'{expected_application_param_type}, actual type: {actual_application_param_type}\n'
                    f'{highlight_error(self.file_name, ctx.args[0].name.line, ctx.args[0].name.column)}'
                )

            if not expected_application_return_type == actual_application_return_type:
                raise RuntimeError(
                    f'[TYPE ERROR] At {ctx.args[0].name.line}:{ctx.args[0].name.column} - expected return type: '
                    f'{expected_application_return_type}, actual type: {actual_application_return_type}\n'
                    f'{highlight_error(self.file_name, ctx.args[0].name.line, ctx.args[0].name.column)}'
                )

        elif isinstance(ctx, stellaParser.NatRecContext):

            if not variables[ctx.n.name.text].getText() == 'Nat':
                raise RuntimeError(
                    f'[TYPE ERROR] At Nat::rec expression {ctx.n.name.line}:{ctx.n.name.column} - expected return type: '
                    f'Nat, actual type: {variables[ctx.n.name.text].getText()}\n'
                    f'{highlight_error(self.file_name, ctx.n.name.line, ctx.n.name.column)}'
                )

            initial_variable_type = variables[ctx.initial.name.text]
            expected_step_param_type = initial_variable_type
            expected_step_return_type = initial_variable_type

            if not expected_step_param_type.getText() == ctx.step.paramDecls[0].paramType.getText():
                parameter = ctx.step.paramDecls[0]
                raise RuntimeError(
                    f'[TYPE ERROR] At Nat::rec expression {parameter.name.line}:'
                    f'{parameter.name.column} - expected parameter type: '
                    f'{expected_step_param_type.getText()}, actual type: {parameter.paramType.getText()}\n'
                    f'{highlight_error(self.file_name, parameter.name.line, parameter.name.column)}'
                )

            variables.update({
                ctx.step.paramDecls[0].name.text: ctx.step.paramDecls[0].paramType,
            })

            expected_step_type = stellaParser.TypeFunContext(
                ctx=ctx,
                parser=initial_variable_type.parser,
            )

            expected_step_type.paramTypes = [expected_step_param_type]
            expected_step_type.returnType = expected_step_return_type

            self.handle_expr_context(
                ctx=ctx.step.returnExpr,
                ctx_type=expected_step_type,
                variables=variables,
            )

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
