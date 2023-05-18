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

ast = create_AST("simpleC/test_only_op.c")

funcbuilder = ASTActionRegister()

'''
按照这个逻辑，AST遍历也是按后序遍历处理，所以也是一个一个函数处理
因此，可以使用builder_list 存放所有函数的builder ， 并用一个builder_no表示进行到第几个函数了
'''
# 全局module
module = ir.Module()

# builder 汇总表
builder_list = [] 

# 局部变量表
local_var = []

# ----------------------------第一遍扫描-----------------------------------
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

@funcbuilder.action("funcDec")
def _funcDecl(func, type_, func_id, defpl, sl):
    # if 'module' not in func:
    #     assert func.module is not None
    funcName = str(func_id.getContent())
    retType = get_llvm_type(type_.getContent())
    arg_types = []
    arg_names = []
    for arg in defpl.getChilds():
        attr = arg.getChilds()
        arg_types.append(get_llvm_type(attr[0].getContent()))
        arg_names.append(attr[1].getContent())

    # 声明完毕，开始定义函数
    funcType = ir.FunctionType(retType, tuple(arg_types))

    # 构建基本块和Buidler
    func.llvm_func = ir.Function(module, funcType, funcName)
    for arg in func.llvm_func.args:     # 函数参数绑定名称
        arg.name = arg_names.pop(0)

    primary_block = func.llvm_func.append_basic_block()
    builder = ir.IRBuilder(primary_block)
    global builder_list
    builder_list.append(builder)        # 导入Budiler列表           

    # 创建局部变量表
    local_var.append({})


ast.evaluate(funcbuilder)

# ----------------------------第二遍扫描-----------------------------------

# func_block定位
func_no = 0
block_no = 0

# builder_now 表示当前处理的第一个函数的builder，后序不断更新
builder_now = builder_list[0]

aar = ASTActionRegister()

@aar.action("varDec")
def _varDec(varDec, type_, idList):
    global builder_now, block_no
    # 相当于一条主干语句的结束，切换到一个新的block
    new_blk = builder_now.append_basic_block()
    block_no += 1
    builder_now.position_at_start(new_blk)

    for node in idList.getChilds():
        if node.getContent() == 'assign':
            var_name = node.getChilds()[0].getContent()
            variable = builder_now.alloca(get_llvm_type(type_.getContent()), var_name)
            builder_now.store(node.getChilds()[1].value, variable)
            local_var[func_no][var_name] = builder_now.load(variable)   # 可运算的类型 - load
        else:
            var_name = node.getContent()
            variable = builder_now.alloca(get_llvm_type(type_.getContent()), var_name)
            local_var[func_no][var_name] = builder_now.load(variable)   # 可运算的类型 - load

@aar.action("assign")
def _assign_begin(assg, l, r):
    if 'value' in l:
        if isinstance(l.value, ir.LoadInstr):# l.value is None:
            builder_now.store(r.value, l.value.operands[0])
        else:
            builder_now.store(r.value, l.value)
        assg.value = l.value
    else:
        print("l.value not found, wait for defination")
    # assg.cb.addILOC("mov", "ebx", r.var.getOP())
    # assg.cb.addILOC("mov", l.var.getOP(), "ebx")
    # assg.var = l.var

@aar.action("id_var")
def _id_var(id_):
    name = id_.getContent()

    # 在全局变量表中查找
    # for var in module.global_variables:
    #     if var.name == name:
    #         id_.var = var
    #         return

    # 在局部变量表中查找
    if name in local_var[func_no]:
        id_.value = local_var[func_no][name]
        return
    
    # 在函数的args中查找
    for arg in builder_now.function.args:
        if arg.name == name:
            id_.value = arg
            return
    
    # 未找到，不做处理
    print("var %s not found, can't get value" % name)

@aar.action("const")
def _const(const):
    val = const.getContent()
    if const.type == "int":
        const.value = ir.Constant(ir.IntType(32), int(val))
    elif const.type == "double":
        const.value = ir.Constant(ir.DoubleType(), float(val))
    elif const.type == "float":
        const.value = ir.Constant(ir.FloatType(), float(val))
    elif const.type == "String":
        val += ", 0" # not sure
        const.value = ir.Constant.literal_array(val)
    else:
        print('not implemented type %s' % const.type)
        assert False

@aar.action("add")
def _add(add, l, r):
    add.value = builder_now.add(l.value, r.value)

@aar.action("sub")
def _sub(sub, l, r):
    sub.value = builder_now.sub(l.value, r.value)

@aar.action("mul")
def _mul(mul, l, r):
    mul.value = builder_now.mul(l.value, r.value)

@aar.action("div")
def _div(div, l, r):
    # TODO assert r.value != 0
    div.value = builder_now.sdiv(l.value, r.value)

@aar.action("mod")
def _mod(mod, l, r):
    # TODO assert r.value != 0
    mod.value = builder_now.srem(l.value, r.value)

@aar.action("splus")
def _sp(sp, l):
    l.value = builder_now.add(l.value, ir.Constant(l.value.type, 1))
    sp.value = l.value
    
@aar.action("sminus")
def _sm(sm, l):
    l.value = builder_now.sub(l.value, ir.Constant(l.value.type, 1))
    sm.value = l.value

@aar.action("iadd")
def _iadd(iadd, l, r):
    l.value = builder_now.add(l.value, r.value)
    iadd.value = l.value

@aar.action("isub")
def _isub(isub, l, r):
    l.value = builder_now.sub(l.value, r.value)
    isub.value = l.value

@aar.action("imul")
def _imul(imul, l, r):
    l.value = builder_now.mul(l.value, r.value)
    imul.value = l.value

@aar.action("idiv")
def _idiv(idiv, l, r):
    # TODO assert r.value != 0
    l.value = builder_now.sdiv(l.value, r.value)
    idiv.value = l.value

@aar.action("imod")
def _imod(imod, l, r):
    # TODO assert r.value != 0
    l.value = builder_now.srem(l.value, r.value)
    imod.value = l.value

@aar.action("eq")
def _eq(eq, l, r):
    eq.value = builder_now.icmp_signed('==', l.value, r.value)

@aar.action("ne")
def _ne(ne, l, r):
    ne.value = builder_now.icmp_signed('!=', l.value, r.value)

@aar.action("lt")
def _lt(lt, l, r):
    lt.value = builder_now.icmp_signed('<', l.value, r.value)

@aar.action("gt")
def _gt(gt, l, r):
    gt.value = builder_now.icmp_signed('>', l.value, r.value)

@aar.action("le")
def _le(le, l, r):
    le.value = builder_now.icmp_signed('<=', l.value, r.value)

@aar.action("ge")
def _ge(ge, l, r):
    ge.value = builder_now.icmp_signed('>=', l.value, r.value)

@aar.action("not")
def _not(not_, l):
    not_.value = builder_now.not_(l)

@aar.action("or")
def _or(or_, l, r):
    or_.value = builder_now.or_(l, r)

@aar.action("and")
def _and(and_, l, r):
    and_.value = builder_now.and_(l, r)

@aar.action("funcDec")
def _funcDecl(func, type_, func_id, defpl, sl):
    # 仅仅作为builder的切换函数
    global func_no, builder_now, block_no
    func_no += 1
    block_no = 0
    if func_no < len(builder_list):
        builder_now = builder_list[func_no]
    else:
        print('the last func')

@aar.action("stmtList", index=0)
def _stmtl(stmtl, *rest):
    # 仅仅作为block的切换函数
    global block_no, builder_now
    block_no += 1
    new_blk = builder_now.append_basic_block()
    stmtl.block = builder_now.function.basic_blocks[block_no]
    builder_now.position_at_end(new_blk)

@aar.action("ifBlock", index = 0)
def _ifBlock_prestore(ifb, *childs):
    global block_no, builder_now
    block_no += 1
    new_blk = builder_now.append_basic_block()
    ifb.start_block = new_blk
    builder_now.position_at_end(new_blk)

@aar.action("ifBlock")
def _ifBlock(ifb, *childs):
    # 0: eq 1: slist (2: cond, 3: slist)... 4: slist
    global block_no
    block_no += 1
    ifend = builder_now.append_basic_block('if_end_' + ifb.start_block.name)

    builder_now.position_at_end(ifb.start_block)

    if len(childs) == 2:
        builder_now.cbranch(childs[0].value, childs[1].block, ifend)
    elif len(childs) == 3:
        builder_now.cbranch(childs[0].value, childs[1].block, childs[2].block)
        builder_now.position_at_end(childs[1].block)
        builder_now.branch(ifend)
        builder_now.position_at_end(childs[2].block)
        builder_now.branch(ifend)
    else:
        assert False # TODO not implement
        for i in range(0, len(childs), 2):

            builder_now.cbranch(childs[i].value, childs[i+1].block, childs[i+2].block)
            builder_now.position_at_end(childs[i+1].block)
            builder_now.branch(ifend)
    builder_now.position_at_end(ifend)

@aar.action("whileBlock", index = 0)
def _whileBlock_prestore(while_, c0, sl):
    global block_no, builder_now
    block_no += 1
    new_blk = builder_now.append_basic_block()
    while_.start_block = new_blk
    builder_now.position_at_end(new_blk)

@aar.action("whileBlock")
def _while(while_, c0, sl):
    global block_no
    block_no += 1
    while_end = builder_now.append_basic_block('while_end_' + sl.block.name)
    builder_now.position_at_end(while_.start_block)
    builder_now.cbranch(c0.value, sl.block, while_end)
    builder_now.position_at_end(sl.block)
    builder_now.branch(while_.start_block)

    builder_now.position_at_end(while_end)

# @aar.action("forBlock", index=0)
# def _for_prestore(for_, init, expr0, stmtl, expr1):
#     global block_no, builder_now
#     block_no += 1
#     new_blk = builder_now.append_basic_block()
#     for_.start_block = new_blk
#     builder_now.position_at_end(new_blk)

@aar.action("forexpr", index = 0) 
def _forexpr_prestore(forexpr_, expr):
    global block_no, builder_now
    block_no += 1
    new_blk = builder_now.append_basic_block()
    forexpr_.block = new_blk
    builder_now.position_at_end(new_blk)
   
@aar.action("forexpr") 
def _forexpr(forexpr_, expr):
    if 'value' in expr:
        forexpr_.value = expr.value

@aar.action("forBlock")
def _for(for_, init, expr0, stmtl, expr1):
    global block_no
    block_no += 1
    for_end = builder_now.append_basic_block('for_end_' + stmtl.block.name)
    builder_now.position_at_end(init.block)
    builder_now.branch(expr0.block)
    builder_now.position_at_end(expr0.block)
    builder_now.cbranch(expr0.value, stmtl.block, for_end)
    builder_now.position_at_end(stmtl.block)
    if expr1.getContent() != 'none':
        builder_now.branch(expr1.block)
        builder_now.position_at_end(expr1.block)
        builder_now.branch(expr0.block)

    builder_now.position_at_end(for_end)


ast.evaluate(aar)
print(module)

exit()

'''
@aar.action("break")
def _break(break_):
    # TODO break的逻辑
    break_.cb.addILOC("goto", (break_.bb, "next"))

@aar.action("continue")
def _continue(continue_):
    # TODO continue的逻辑
    continue_.cb.addILOC("goto", continue_.lb)
'''

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
