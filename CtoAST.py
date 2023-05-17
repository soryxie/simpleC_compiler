from cfg import ContextFreeGrammar
from typeDef import TypeDefinition
from action import Action
from goto import Goto
from Ast import ASTNode, AbstractSyntaxTree
from parseTree import ParseTreeActionRegister
import scanner
import Parser

# 提前指定好simpleC的全局路径，在vscode下调试会使用到
path_to_simpleC = "/Users/MBP/Documents/compiler/javacompiler/newCompilerTest/simpleC/"

typedef = TypeDefinition.load(path_to_simpleC + "typedef")
cfg = ContextFreeGrammar.load(typedef, path_to_simpleC + "CFG")

# ------------------- 生成新语法的两张表 -------------------
# action, goto = Parser.genActionGoto(typedef, cfg)
# action.save(path_to_simpleC + "simpleCAction")
# goto.save(path_to_simpleC + "simpleCGoto")
# exit()

# ------------------- 读取已经生成的两张表 -------------------
action = Action.load(cfg, path_to_simpleC + "simpleCAction")
goto = Goto.load(cfg, path_to_simpleC + "simpleCGoto")
par = ParseTreeActionRegister(cfg)

# ------------------- 外部调用接口 -------------------
def create_AST(read_file: str) -> AbstractSyntaxTree:
    with open(read_file, "r") as f:
        src = f.read()
    tokenList = scanner.parse(typedef, src, ['line_comment', 'block_comment', 'space'])
    pt = Parser.parse(tokenList, typedef, cfg, action, goto)
    pt.evaluate(par)
    ast = AbstractSyntaxTree(pt.getRoot().node)
    return ast





# --------- 以下均为parser tree 转换到 AST 所需要的语义动作 ---------
@par.production("<Start> -> <语句串>")
def _start(program, stmtl):
    program.node = ASTNode("start", stmtl.node, actionID="start")


@par.production("<语句串> -> <语句串> <语句>")
def _stmtl0(stmtl, stmtl0, stmt):
    stmtl.node = stmtl0.node
    stmtl.node.addChild(stmt.node)

@par.production("<语句串> -> <语句>")
def _stmtl1(stmtl, stmt):
    stmtl.node = ASTNode("stmtList", stmt.node)

@par.production(
    "<语句> -> <声明>",
    "<语句> -> <表达式>",
    "<语句> -> <while语句>",
    "<语句> -> <if语句>",
    "<语句> -> <for语句>",
    "<语句> -> <返回语句>",
    "<语句> -> <控制语句>"
)
def _stmt2(stmt, other):
    stmt.node = other.node

@par.production("<表达式> -> <f0> ;")
def _expr0(expr, f0, semi):
    expr.node = f0.node

@par.production(
    "<c0> -> <c1>", "<c1> -> <c2>", "<c2> -> <c3>", "<c3> -> <e0>",
    "<e0> -> <e1>", "<e1> -> <e2>", "<e2> -> <e3>", "<e3> -> <e4>", "<f0> -> <c0>"
)
def _cxx(ca, cb):
    ca.node = cb.node

@par.production("<c1> -> <c1> and <c2>")
def _c00(c0, c00, and_, c1):
    c0.node = ASTNode("and", c00.node, c1.node)

@par.production("<c0> -> <c0> or <c1>")
def _c10(c1, c10, or_, c2):
    c1.node = ASTNode("or", c10.node, c2.node)

@par.production("<e3> -> not <e3>")
def _c20(c2, not_, c3):
    c2.node = ASTNode("not", c3.node)

@par.production("<c2> -> <c2> == <c3>")
def _c30(c3, c30, eq, c4):
    c3.node = ASTNode("eq", c30.node, c4.node)

@par.production("<c2> -> <c2> < <c3>")
def _c31(c3, c30, eq, c4):
    c3.node = ASTNode("lt", c30.node, c4.node)

@par.production("<c2> -> <c2> > <c3>")
def _c32(c3, c30, eq, c4):
    c3.node = ASTNode("gt", c30.node, c4.node)

@par.production("<c2> -> <c2> <= <c3>")
def _c33(c3, c30, eq, c4):
    c3.node = ASTNode("le", c30.node, c4.node)

@par.production("<c2> -> <c2> >= <c3>")
def _c34(c3, c30, eq, c4):
    c3.node = ASTNode("ge", c30.node, c4.node)

@par.production("<c2> -> <c2> != <c3>")
def _c35(c3, c30, eq, c4):
    c3.node = ASTNode("ne", c30.node, c4.node)

@par.production("<e3> -> ++ <e4>")
def _e00(e0, sp, e1):
    e0.node = ASTNode("sp", e1.node)  # self plus

@par.production("<e3> -> -- <e4>")
def _e01(e0, sm, e1):
    e0.node = ASTNode("sm", e1.node)  # self minus

@par.production("<e0> -> <e0> + <e1>")
def _e10(e1, e10, plus, e2):
    e1.node = ASTNode("add", e10.node, e2.node)

@par.production("<e0> -> <e0> - <e1>")
def _e11(e1, e10, minus, e2):
    e1.node = ASTNode("sub", e10.node, e2.node)

@par.production("<f0> -> <c0> += <f0>")
def _e30(e1, e2, iplus, e10):
    e1.node = ASTNode("iadd", e2.node, e10.node)

@par.production("<f0> -> <c0> -= <f0>")
def _e31(e1, e2, iminus, e10):
    e1.node = ASTNode("isub", e2.node, e10.node)

@par.production("<e1> -> <e1> * <e2>")
def _e20(e2, e20, mul, e3):
    e2.node = ASTNode("mul", e20.node, e3.node)

@par.production("<e1> -> <e1> / <e2>")
def _e21(e2, e20, mul, e3):
    e2.node = ASTNode("div", e20.node, e3.node)

@par.production("<f0> -> <c0> *= <f0>")
def _e32(e2, e3, mul, e20):
    e2.node = ASTNode("imul", e3.node, e20.node)

@par.production("<f0> -> <c0> /= <f0>")
def _e33(e2, e3, mul, e20):
    e2.node = ASTNode("idiv", e3.node, e20.node)

@par.production("<e1> -> <e1> % <e2>")
def _e22(e2, e20, mod, e3):
    e2.node = ASTNode("mod", e20.node, e3.node)

@par.production("<f0> -> <c0> %= <f0>")
def _e34(e2, e3, mul, e20):
    e2.node = ASTNode("imod", e3.node, e20.node)

@par.production("<f0> -> <c0> = <f0>")
def _f00(f0, f00, assg, f1):
    f0.node = ASTNode("assign", f00.node, f1.node)

@par.production("<e4> -> id [ <e0> ]")  
def _f11(f1, id_, lob, f2, rob):
    f1.node = ASTNode("getitem", ASTNode(id_.getContent(), actionID="id_var"), f2.node)

@par.production("<e4> -> ( <f0> )")
def _f20(e3, lp, f0, rp):
    e3.node = f0.node

@par.production("<e4> -> <值>")
def _f21(e3, value):
    e3.node = value.node

@par.production("<声明> -> <变量声明串> ;")
def _decl0(declaration, varDeclaration, semi):
    declaration.node = varDeclaration.node

@par.production("<声明> -> <函数声明>")
def _decl1(declaration, functionDeclaration):
    declaration.node = functionDeclaration.node

@par.production("<变量声明串> -> <类型> <变量串>")
def _vardecl0(vardec, type_, idList):
    vardec.node = ASTNode("varDec", type_.node, idList.node)

@par.production("<变量串> -> <变量串> , <变量>")
def _idl0(idl, idl0, comma, id_):
    idl.node = idl0.node
    idl.node.addChild(id_.node)

@par.production("<变量串> -> <变量>")
def _idl1(idl, id_):
    idl.node = ASTNode("idList", id_.node)

@par.production("<变量> -> id")
def _id0(id_, id_0):
    id_.node = ASTNode(id_0.getContent(), actionID="id_var")

@par.production("<变量> -> id = <f0>")
def _id1(id_, id_0, assg, c0):
    id_.node = ASTNode("assign", ASTNode(id_0.getContent(), actionID="id_var"), c0.node)

@par.production("<变量> -> id [ int_const ]")    #------------------------ 类型待填入
def _alloc0(id_, id_0, lo, int_const, ro):
    id_.node = ASTNode("assign", ASTNode(id_0.getContent(), actionID="noAction"), \
        ASTNode("newArr", ASTNode("int", actionID="type"), ASTNode(int_const.getContent(), actionID="noAction")))

@par.production("<变量> -> id [ int_const ] = { <参数列表> }")    #------------------------ 类型待填入
def _alloc1(id_, id_0, lo, int_const, ro , assg, lcb, pal, rcb):
    id_.node = ASTNode("assign", ASTNode(id_0.getContent(), actionID="noAction"), \
        ASTNode("newArr", ASTNode("int", actionID="type"), ASTNode(int_const.getContent(), actionID="noAction"), pal.node, actionID="noAction"))

@par.production("<函数声明> -> <类型> id ( <参数定义表> ) { <语句串> }")
def _funcdec0(funcDec, type_, id_, lp, defParamList, rp, lcb, stmtl, rcb):
    funcDec.node = ASTNode(
        "funcDec",
        type_.node,
        ASTNode(id_.getContent(), actionID="id_func"),
        defParamList.node,
        stmtl.node
    )

@par.production("<函数声明> -> <类型> id ( ) { <语句串> }")
def _funcdec1(funcDec, type_, id_, lp, rp, lcb, stmtl, rcb):
    funcDec.node = ASTNode(
        "funcDec",
        type_.node,
        ASTNode(id_.getContent(), actionID="id_func"),
        ASTNode('empty_param'), # 专门增加一个空的参数表
        stmtl.node
    )

@par.production("<参数定义表> -> <参数定义表> , <参数定义>")
def _defpl0(defpl, defpl0, comma, defp):
    defpl.node = defpl0.node
    defpl.node.addChild(defp.node)

@par.production("<参数定义表> -> <参数定义>")
def _defpl1(defpl, defp):
    defpl.node = ASTNode("defParamList", defp.node)

@par.production("<参数定义> -> <类型> id")
def _defp0(defp, type_, id_):
    defp.node = ASTNode("defParam", type_.node, ASTNode(id_.getContent(), actionID="id_func_var"))

@par.production("<while语句> -> while ( <c0> ) { <语句串> }")
def _whileBlock0(wb, while_, lp, c0, rp, lcb, sl, rcb):
    wb.node = ASTNode("whileBlock", c0.node, sl.node)

@par.production("<if语句> -> if ( <c0> ) { <语句串> }")
def _ifBlock0(ib, if_, lp, c0, rp, lcb, sl, rcb):
    if "node" not in ib:
        ib.node = ASTNode("ifBlock", c0.node, sl.node)
    else:
        ib.node.addChild(c0.node)
        ib.node.addChild(sl.node)

@par.production("<if语句> -> if ( <c0> ) { <语句串> } else { <语句串> }")
def _ifBlock1(ib, if_, lp, c0, rp, lcb, sl, rcb, else_, lcb0, sl0, rcb0):
    if "node" not in ib:
        ib.node = ASTNode("ifBlock", c0.node, sl.node, sl0.node)
    else:
        ib.node.addChild(c0.node)
        ib.node.addChild(sl.node)
        ib.node.addChild(sl0.node)

@par.production("<if语句> -> if ( <c0> ) { <语句串> } else <if语句>", index=8)
def _ifBlock1(ib, if_, lp, c0, rp, lcb, sl, rcb, else_, ib0):
    if "node" not in ib:
        ib.node = ASTNode("ifBlock", c0.node, sl.node)
    else:
        ib.node.addChild(c0.node)
        ib.node.addChild(sl.node)
    ib0.node = ib.node

@par.production("<for初始化> -> <变量声明串>", "<for初始化> -> <变量串>", "<for表达式> -> <c0>")
def _forinit0(forinit, b):
    forinit.node = b.node

@par.production("<for初始化> -> ''", "<for表达式> -> ''")
def _empty(a):
    a.node = ASTNode("none")

@par.production("<for语句> -> for ( <for初始化> ; <for表达式> ; <for表达式> ) { <语句串> }")
def _forblock0(forBlock, for_, lp, forinit, semi0, forexpr0, semi1, forexpr1, rp, lcb, stmtl, rcb):
    forBlock.node = ASTNode(
        "forBlock",
        forinit.node,
        forexpr0.node,
        stmtl.node,
        forexpr1.node
    )

@par.production("<返回语句> -> return <c0> ;")
def _rs0(rs, ret, c0, semi):
    rs.node = ASTNode("return", c0.node)

@par.production("<类型> -> <基本类型>")
def _type0(type_, basicType):
    type_.node = basicType.node
    type_.node.isArray = False
    type_.node.dim = 0

@par.production(
    "<基本类型> -> int",
    "<基本类型> -> float",
    "<基本类型> -> double",
    "<基本类型> -> long", 
    "<基本类型> -> char", 
    "<基本类型> -> bool", 
    "<基本类型> -> void", 
    "<基本类型> -> short"
)
def _basicType0(bt, typ):
    bt.node = ASTNode(typ.getContent(), actionID="type")

@par.production("<值> -> <函数调用>")
def _val0(value, functionCall):
    value.node = functionCall.node

@par.production("<函数调用> -> id ( <参数列表> )")
def _func0(func, id_, lp, pal, rp):
    func.node = ASTNode("functionCall", ASTNode(id_.getContent(), actionID="noAction"), pal.node)

@par.production("<函数调用> -> id ( )")
def _func0(func, id_, lp, rp):
    func.node = ASTNode("functionCall", ASTNode(id_.getContent(), actionID="noAction"))

@par.production("<参数列表> -> <参数列表> , <参数>")
def _pal0(paraml, paraml0, comma, param):
    paraml.node = paraml0.node
    paraml.node.addChild(param.node)

@par.production("<参数列表> -> <参数>")
def _pal1(paraml, param):
    paraml.node = ASTNode("parameterList", param.node)

@par.production("<参数> -> <c0>")
def _par0(par, c0):
    par.node = c0.node

@par.production("<值> -> <常量>")
def _val1(value, constant):
    value.node = ASTNode(constant.val, actionID="const")
    value.node.type = constant.type

@par.production("<值> -> id")
def _val2(value, id_):
    value.node = ASTNode(id_.getContent(), actionID="id_var")

@par.production("<常量> -> int_const")
def _const0(const, int_const):
    const.val = int_const.getContent()
    const.type = "int"

@par.production("<常量> -> str_literal")
def _const1(const, str_literal):
    const.val = str_literal.getContent()
    const.type = "String"

@par.production("<常量> -> char_literal")
def _const3(const, char):
    const.val = char.getContent()
    const.type = "char"

@par.production("<常量> -> true", "<常量> -> false")
def _const2(const, boolean):
    const.val = boolean.getContent()
    const.type = "bool"

@par.production("<常量> -> null")
def _const3(const, null):
    const.val = null.getContent()
    const.type = "null"

@par.production("<控制语句> -> continue ;")
def _continue0(flc, cont, semi):
    flc.node = ASTNode("continue")

@par.production("<控制语句> -> break ;")
def _continue1(flc, brk, semi):
    flc.node = ASTNode("break")

if __name__ == '__main__':
    ast = create_AST("simpleC/test.c")
    # print(ast) # 能直接得到字符树