from collections import deque
from cfg import ContextFreeGrammar
from typeDef import TypeDefinition
from action import Action
from goto import Goto
from Ast import ASTNode, AbstractSyntaxTree, ASTActionRegister
from parseTree import ParseTreeActionRegister
from CtoAST import create_AST
from llvmlite import ir
import scanner
import Parser
import sys

ast = create_AST("simpleC/test.c")

funcbuilder = ASTActionRegister()

# 目前按照单文件编译的格式，只需要一个module，干脆设成全局试试
module = ir.Module()

def get_llvm_type(type_):
    if type_ == 'int':
        return ir.IntType(32)
    elif type_ == 'double':
        return ir.DoubleType()
    elif type_ == 'float':
        return ir.FloatType()
    else:
        print("error type")
        exit()

# @funcbuilder.action("start", index=0)
# def _program_dec(start, *stmtls): # 传播给下一层节点
#     module = ir.Module()
#     for child in stmtls:
#         child.module = module 
#     start.module = module

@funcbuilder.action("stmtList", index=0)
def _stmtl(stmtls, *stmts):
    if 'builder' in stmtls :
        # 只有当不具有builder的stmtls才是最外部的   
        glo_verible = []
        func = []
        for child in stmts:
            if child.var is not None:
                glo_verible.append(child.var)
            if child.llvm_func is not None:
                func.append(child.func)

@funcbuilder.action("funcDec")
def _funcDecl(func, type_, func_id, defpl, sl):
    # if 'module' not in func:
    #     assert func.module is not None
    funcName = str(func_id.getContent())
    retType = get_llvm_type(type_.getContent())
    funcType = ir.FunctionType(retType, ())
    func.llvm_func = ir.Function(module, funcType, funcName)
    sl.builder = func.llvm_func.append_basic_block(name = funcName+"_stmtl")



ast.evaluate(funcbuilder)


exit()
aar = ASTActionRegister()
@aar.action("varDec", index=0)
def _varDec(varDec, type_, idList):
    for node in idList.getChilds():
        # TODO 这里的逻辑是 child0=type child1=idList 下一层孩子才是变量 or 数组
        # 需要添加对应的变量声明IR 
        idList.builder.allocat(ir.IntType(32), name=node.getContent())
     
        


@aar.action("assign", index=0)
def _assign_begin(assg, l, r):
    # TODO 他出现在 idList 的孩子，要么是当具有初始值，就是assg,
    # 否则就是id_var
    # 这里的逻辑是 child0=var child1=expr
    pass


@aar.action("assign")
def _assign(assg, l, r):
    assg.cb.addILOC("mov", "ebx", r.var.getOP())
    assg.cb.addILOC("mov", l.var.getOP(), "ebx")
    assg.var = l.var
    '''不懂'''

@aar.action("const")
def _const(const):
    '''建立const变量'''
    val = str(const.getContent())
    if const.type[0].islower():
        const.var = ConstValue(getTempVarName(), const.type, val, const.ns)
    else:
        if const.type == "String":
            val += ", 0"
        const.var = ConstPointer(getTempVarName(), const.type, val, const.ns)

@aar.action("add")
def _add(add, l, r):
    '''＋逻辑'''
    add.cb.addILOC("push", "eax")
    add.cb.addILOC("mov", "eax", r.var.getOP())
    add.cb.addILOC("add", "eax", l.var.getOP())
    add.var = Variable(getTempVarName(), getType(l, r), add.ns)
    add.cb.addILOC("mov", add.var.getOP(), "eax")
    add.cb.addILOC("pop", "eax")

@aar.action("sub")
def _sub(sub, l, r):
    sub.cb.addILOC("push", "eax")
    sub.cb.addILOC("mov", "eax", l.var.getOP())
    sub.cb.addILOC("sub", "eax", r.var.getOP())
    sub.var = Variable(getTempVarName(), getType(l, r), sub.ns)
    sub.cb.addILOC("mov", sub.var.getOP(), "eax")
    sub.cb.addILOC("pop", "eax")

@aar.action("mul")
def _mul(mul, l, r):
    mul.cb.addILOC("push", "eax")
    mul.cb.addILOC("mov", "eax", l.var.getOP())
    mul.cb.addILOC("mul", r.var.getOP())
    mul.var = Variable(getTempVarName(), getType(l, r), mul.ns)
    mul.cb.addILOC("mov", mul.var.getOP(), "eax")
    mul.cb.addILOC("pop", "eax")

@aar.action("div")
def _div(div, l, r):
    div.cb.addILOC("push", "eax")
    div.cb.addILOC("push", "ebx")
    div.cb.addILOC("push", "edx")
    div.cb.addILOC("xor", "edx", "edx")
    div.cb.addILOC("mov", "eax", l.var.getOP())
    div.cb.addILOC("mov", "ebx", r.var.getOP())
    div.cb.addILOC("div", "ebx")
    div.var = Variable(getTempVarName(), getType(l, r), div.ns)
    div.cb.addILOC("mov", div.var.getOP(), "eax")
    div.cb.addILOC("pop", "edx")
    div.cb.addILOC("pop", "ebx")
    div.cb.addILOC("pop", "eax")

@aar.action("mod")
def _mod(mod, l, r):
    mod.cb.addILOC("push", "eax")
    mod.cb.addILOC("push", "ebx")
    mod.cb.addILOC("push", "edx")
    mod.cb.addILOC("xor", "edx", "edx")
    mod.cb.addILOC("mov", "eax", l.var.getOP())
    mod.cb.addILOC("mov", "ebx", r.var.getOP())
    mod.cb.addILOC("div", "ebx")
    mod.var = Variable(getTempVarName(), getType(l, r), mod.ns)
    mod.cb.addILOC("mov", mod.var.getOP(), "edx")
    mod.cb.addILOC("pop", "edx")
    mod.cb.addILOC("pop", "ebx")
    mod.cb.addILOC("pop", "eax")

@aar.action("sp")
def _sp(sp, l):
    sp.cb.addILOC("inc", l.var.getOP())
    sp.var = l.var

@aar.action("sm")
def _sm(sm, l):
    sm.cb.addILOC("dec", l.var.getOP())
    sm.var = l.var

@aar.action("iadd")
def _iadd(iadd, l, r):
    iadd.cb.addILOC("push", "eax")
    iadd.cb.addILOC("mov", "eax", l.var.getOP())
    iadd.cb.addILOC("add", "eax", r.var.getOP())
    iadd.cb.addILOC("mov", l.var.getOP(), "eax")
    iadd.cb.addILOC("pop", "eax")
    iadd.var = l.var

@aar.action("isub")
def _isub(isub, l, r):
    isub.cb.addILOC("push", "eax")
    isub.cb.addILOC("mov", "eax", l.var.getOP())
    isub.cb.addILOC("sub", "eax", r.var.getOP())
    isub.cb.addILOC("mov", l.var.getOP(), "eax")
    isub.cb.addILOC("pop", "eax")
    isub.var = l.var

@aar.action("imul")
def _imul(imul, l, r):
    imul.cb.addILOC("push", "eax")
    imul.cb.addILOC("mov", "eax", l.var.getOP())
    imul.cb.addILOC("mul", r.var.getOP())
    imul.cb.addILOC("mov", l.var.getOP(), "eax")
    imul.cb.addILOC("pop", "eax")
    imul.var = l.var

@aar.action("idiv")
def _idiv(idiv, l, r):
    idiv.cb.addILOC("push", "eax")
    idiv.cb.addILOC("push", "ebx")
    idiv.cb.addILOC("push", "edx")
    idiv.cb.addILOC("xor", "edx", "edx")
    idiv.cb.addILOC("mov", "eax", l.var.getOP())
    idiv.cb.addILOC("mov", "ebx", r.var.getOP())
    idiv.cb.addILOC("div", "ebx")
    idiv.cb.addILOC("mov", l.var.getOP(), "eax")
    idiv.cb.addILOC("pop", "edx")
    idiv.cb.addILOC("pop", "ebx")
    idiv.cb.addILOC("pop", "eax")
    idiv.var = l.var

@aar.action("imod")
def _imod(imod, l, r):
    imod.cb.addILOC("push", "eax")
    imod.cb.addILOC("push", "ebx")
    imod.cb.addILOC("push", "edx")
    imod.cb.addILOC("xor", "edx", "edx")
    imod.cb.addILOC("mov", "eax", l.var.getOP())
    imod.cb.addILOC("mov", "ebx", r.var.getOP())
    imod.cb.addILOC("div", "ebx")
    imod.cb.addILOC("mov", l.var.getOP(), "edx")
    imod.cb.addILOC("pop", "edx")
    imod.cb.addILOC("pop", "ebx")
    imod.cb.addILOC("pop", "eax")
    imod.var = l.var

@aar.action("eq")
def _eq(eq, l, r):
    eq.cb.addILOC("push", "eax")
    eq.cb.addILOC("xor", "eax", "eax")
    eq.cb.addILOC("push", "ebx")
    eq.cb.addILOC("mov", "ebx", l.var.getOP())
    eq.cb.addILOC("cmp", "ebx", r.var.getOP())
    eq.cb.addILOC("lahf")
    eq.cb.addILOC("shr", "eax", "14")
    eq.cb.addILOC("and", "eax", "1")
    eq.var = Variable(getTempVarName(), "int", eq.ns)
    eq.cb.addILOC("mov", eq.var.getOP(), "eax")
    eq.cb.addILOC("pop", "ebx")
    eq.cb.addILOC("pop", "eax")

@aar.action("ne")
def _ne(ne, l, r):
    ne.cb.addILOC("push", "eax")
    ne.cb.addILOC("xor", "eax", "eax")
    ne.cb.addILOC("push", "ebx")
    ne.cb.addILOC("mov", "ebx", l.var.getOP())
    ne.cb.addILOC("cmp", "ebx", r.var.getOP())
    ne.cb.addILOC("lahf")
    ne.cb.addILOC("shr", "eax", "14")
    ne.cb.addILOC("and", "eax", "1")
    ne.cb.addILOC("xor", "eax", "1")
    ne.var = Variable(getTempVarName(), "int", ne.ns)
    ne.cb.addILOC("mov", ne.var.getOP(), "eax")
    ne.cb.addILOC("pop", "ebx")
    ne.cb.addILOC("pop", "eax")

@aar.action("lt")
def _lt(lt, l, r):
    # l < r -> l - r < 0 -> sign = 1
    lt.cb.addILOC("push", "eax")
    lt.cb.addILOC("xor", "eax", "eax")
    lt.cb.addILOC("push", "ebx")
    lt.cb.addILOC("mov", "ebx", l.var.getOP())
    lt.cb.addILOC("cmp", "ebx", r.var.getOP())
    lt.cb.addILOC("lahf")
    lt.cb.addILOC("shr", "eax", "15")
    lt.cb.addILOC("and", "eax", "1")
    lt.var = Variable(getTempVarName(), "int", lt.ns)
    lt.cb.addILOC("mov", lt.var.getOP(), "eax")
    lt.cb.addILOC("pop", "ebx")
    lt.cb.addILOC("pop", "eax")

@aar.action("gt")
def _gt(gt, l, r):
    # l > r -> r - l < 0 -> sign = 1
    gt.cb.addILOC("push", "eax")
    gt.cb.addILOC("xor", "eax", "eax")
    gt.cb.addILOC("push", "ebx")
    gt.cb.addILOC("mov", "ebx", r.var.getOP())
    gt.cb.addILOC("cmp", "ebx", l.var.getOP())
    gt.cb.addILOC("lahf")
    gt.cb.addILOC("shr", "eax", "15")
    gt.cb.addILOC("and", "eax", "1")
    gt.var = Variable(getTempVarName(), "int", gt.ns)
    gt.cb.addILOC("mov", gt.var.getOP(), "eax")
    gt.cb.addILOC("pop", "ebx")
    gt.cb.addILOC("pop", "eax")

@aar.action("le")
def _le(le, l, r):
    # l <= r -> not l > r
    le.cb.addILOC("push", "eax")
    le.cb.addILOC("xor", "eax", "eax")
    le.cb.addILOC("push", "ebx")
    le.cb.addILOC("mov", "ebx", r.var.getOP())
    le.cb.addILOC("cmp", "ebx", l.var.getOP())
    le.cb.addILOC("lahf")
    le.cb.addILOC("shr", "eax", "15")
    le.cb.addILOC("and", "eax", "1")
    le.cb.addILOC("xor", "eax", "1")  # boolean not
    le.var = Variable(getTempVarName(), "int", le.ns)
    le.cb.addILOC("mov", le.var.getOP(), "eax")
    le.cb.addILOC("pop", "ebx")
    le.cb.addILOC("pop", "eax")

@aar.action("ge")
def _ge(ge, l, r):
    # l >= r -> not l < r
    ge.cb.addILOC("push", "eax")
    ge.cb.addILOC("xor", "eax", "eax")
    ge.cb.addILOC("push", "ebx")
    ge.cb.addILOC("mov", "ebx", l.var.getOP())
    ge.cb.addILOC("cmp", "ebx", r.var.getOP())
    ge.cb.addILOC("lahf")
    ge.cb.addILOC("shr", "eax", "15")
    ge.cb.addILOC("and", "eax", "1")
    ge.cb.addILOC("xor", "eax", "1")  # boolean not
    ge.var = Variable(getTempVarName(), "int", ge.ns)
    ge.cb.addILOC("mov", ge.var.getOP(), "eax")
    ge.cb.addILOC("pop", "ebx")
    ge.cb.addILOC("pop", "eax")

@aar.action("not")
def _not(not_, l):
    not_.cb.addILOC("push", "ebx")
    not_.cb.addILOC("mov", "ebx", l.var.getOP())
    not_.cb.addILOC("xor", "ebx", "1")
    not_.var = Variable(getTempVarName(), "int", not_.ns)
    not_.cb.addILOC("mov", not_.var.getOP(), "ebx")
    not_.cb.addILOC("pop", "ebx")

@aar.action("or")
def _or(or_, l, r):
    or_.cb.addILOC("push", "ebx")
    or_.cb.addILOC("mov", "ebx", l.var.getOP())
    or_.cb.addILOC("or", "ebx", r.var.getOP())
    or_.var = Variable(getTempVarName(), "int", or_.ns)
    or_.cb.addILOC("mov", or_.var.getOP(), "ebx")
    or_.cb.addILOC("pop", "ebx")

@aar.action("and")
def _and(and_, l, r):
    and_.cb.addILOC("push", "ebx")
    and_.cb.addILOC("mov", "ebx", l.var.getOP())
    and_.cb.addILOC("and", "ebx", r.var.getOP())
    and_.var = Variable(getTempVarName(), "int", and_.ns)
    and_.cb.addILOC("mov", and_.var.getOP(), "ebx")
    and_.cb.addILOC("pop", "ebx")

@aar.action("ifBlock")
def _ifBlock(ifb, *childs):
    # TODO 需要根据结果写if的跳转
    for i in range(1, len(childs), 2):
        c0, sl = childs[i - 1], childs[i]
        ifb.cb.addILOC("if", c0.var, "1", sl.cb, ("cur", "next"))
    if len(childs) & 1:
        sl = childs[-1]
        ifb.cb.addILOC("goto", sl.cb, ("cur", "next"))
    else:
        ifb.cb.addILOC("goto", ("cur", "next"))
    ifb.cb.addILOC("seg")

'''这里不太懂'''
def updateBreakBlock(cur, childs):
    for child in childs:
        child.bb = cur.bb
        child.run(updateBreakBlock)

def updateContinueBlock(cur, childs):
    for child in childs:
        child.lb = cur.lb
        child.run(updateContinueBlock)

@aar.action("whileBlock", index=0)
def _while_0(while_, c0, sl):
    # TODO 需要根据结果写while的跳转
    c0.cb = sl.cb

@aar.action("whileBlock", index=1)
def _while_1(while_, c0, sl):
    sl.lb = sl.cb
    sl.run(updateContinueBlock)
    sl.bb = while_.cb
    sl.run(updateBreakBlock)
    sl.cb.addILOC("if", c0.var, "0", (while_.cb, "next"))

@aar.action("whileBlock")
def _while(while_, c0, sl):
    sl.cb.next = (while_.cb, "next")
    while_.cb.addILOC("goto", sl.cb)
    while_.cb.addILOC("seg")
    sl.cb.addILOC("goto", sl.cb)

@aar.action("forBlock", index=0)
def _for_0(for_, init, expr0, stmtl, expr1):
    # TODO 需要根据结果写for的跳转
    expr0.cb = stmtl.cb
    expr1.cb = stmtl.cb
    stmtl.bb = for_.cb
    stmtl.run(updateBreakBlock)
    stmtl.lb = stmtl.cb
    stmtl.run(updateContinueBlock)

@aar.action("forBlock", index=2)
def _for_2(for_, init, expr0, stmtl, expr1):
    stmtl.cb.addILOC("if", expr0.var, "0", (for_.cb, "next"))

@aar.action("forBlock")
def _for(for_, init, expr0, stmtl, expr1):
    stmtl.cb.next = (for_.cb, "next")
    for_.cb.addILOC("goto", stmtl.cb)
    for_.cb.addILOC("seg")
    stmtl.cb.addILOC("goto", stmtl.cb)

@aar.action("break")
def _break(break_):
    # TODO break的逻辑
    break_.cb.addILOC("goto", (break_.bb, "next"))

@aar.action("continue")
def _continue(continue_):
    # TODO continue的逻辑
    continue_.cb.addILOC("goto", continue_.lb)


declaredFunctions = {}

class Function:

    def __init__(self, returnType, name, parameters, sl):
        self.returnType = returnType
        self.name = name
        self.parameters = parameters
        self.sl = sl
    
    def __str__(self):
        return "%s(%s)" % (self.name, ", ".join("%s %s" % (var.type, var.name) for var in self.parameters))

    def __repr__(self):
        return repr(str(self))


@aar.action("defParam")
def _defParam(defp, type_, id_):
    # TODO 函数参数定义
    varName = "__v_%d_%d_%s" % (id_.ns[0], id_.ns[1], id_.getContent())
    if type_.getContent()[0].islower():
        defp.var = Variable(varName, type_.getContent(), defp.ns)

@aar.action("defParamList")
def _defParamList(defpl, *defps):
    defpl.list = [_.var for _ in defps]

@aar.action("funcDec", index=0)
# TODO 函数定义
def _funcDec_0(func, type_, func_id, defpl, sl):
    defpl.ns = sl.ns
    defpl.run(updateNS)

@aar.action("funcDec", index=3)
def _funcDec_3(func, type_, func_id, defpl, sl):
    offset = 4  # return address need 4 bytes
    for var in defpl.list:
        sl.cb.addILOC("mov", "ebx", "[esp + %d]" % offset)
        sl.cb.addILOC("mov", var.getOP(), "ebx")
        offset += var.size

@aar.action("funcDec")
def _funcDec(func, type_, func_id, defpl, sl):
    funcName = str(func_id.getContent())
    declaredFunctions[funcName] = \
        Function(
            str(type_.getContent()),
            funcName,
            defpl.list,
            sl.cb
        )


builtinFunctions = {}

def builtin(functionName):
    def decorate(function):
        builtinFunctions[functionName] = function
        return function
    return decorate

@aar.action("return")
def _return(return_, c0):
    # TODO return 逻辑
    return_.cb.addILOC("mov", "eax", c0.var.getOP())
    return_.cb.addILOC("ret")

def match(var1, var2):
    return var1.type == var2.type

@aar.action("parameterList")
def _pml(pml, *childs):
    # TODO 函数调用参数列表
    pml.list = [_.var for _ in childs]

@aar.action("functionCall")
def _funcCall(funcCall, funcName, paramList):
    # TODO 函数调用
    if str(funcName) in builtinFunctions:
        builtinFunctions[str(funcName)](paramList)
    else:
        func = declaredFunctions[str(funcName)]
        if len(paramList.getChilds()) != len(func.parameters):
            print("[ERROR] Function call: Parameter number don't match.")
            exit()
        funcCall.cb.addILOC("push", "eax")
        funcCall.cb.addILOC("push", "ebx")
        totSize = 0
        for i in range(len(func.parameters) - 1, -1, -1):
            if not match(func.parameters[i], paramList.list[i]):
                print("[ERROR] Function call: Parameter %d don't match." % i)
                exit()
            var = paramList.list[i]
            funcCall.cb.addILOC("push", var.getOP())
            totSize += var.size
        funcCall.cb.addILOC("call", func.sl.name)
        funcCall.cb.addILOC("add", "esp", str(totSize))
        funcCall.var = Variable(getTempVarName(), func.returnType, funcCall.ns)
        funcCall.cb.addILOC("mov", funcCall.var.getOP(), "eax")
        funcCall.cb.addILOC("pop", "ebx")
        funcCall.cb.addILOC("pop", "eax")


ast.evaluate(aar)
