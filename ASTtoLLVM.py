from Ast import ASTActionRegister
from CtoAST import create_AST
from llvmlite import ir
import sys

if len(sys.argv) < 3:
    print("Usage: python3 ASTtoLLVM.py <C file> <output file>")
    exit()

# 创建AST
ast = create_AST(sys.argv[1]) 

# 全局module
module = ir.Module()

# builder 汇总表
builder_list = [] 

# 局部变量表
local_var = []

class varelem:
    def __init__(self):
        self.ptr = None
        self.load = None
        self.array = False


# -----------------实现原理-------------------------
# 通过对AST的节点进行两遍后序遍历的扫描  (AST.evaluate())
# 根据不同AST节点的语义动作，完成不同的llvm ir 语句生成



# ----------------------------第一遍扫描-----------------------------------
# 创建注册器funcbuilder，这次扫描只做函数声明的工作
# 好处是可以提前得到每个函数的llvm ir builder, 简化我们第二次扫描的工作
funcbuilder = ASTActionRegister()

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
    funcName = str(func_id.getContent())
    retType = get_llvm_type(type_.getContent())
    arg_types = []
    arg_names = []
    for arg in defpl.getChilds():
        attr = arg.getChilds()
        type = get_llvm_type(attr[0].getContent())
        arg_name = attr[1].getContent()
        if 'dim' in attr[1]:        # 是数组
            dims = attr[1].dim
            tmp_type = []
            for array_dim in dims:
                array_dim = int(array_dim)
                if len(tmp_type) == 0:
                    type_arr = ir.ArrayType(type, array_dim)
                else:
                    type_arr = ir.ArrayType(tmp_type[-1], array_dim)
                tmp_type.append(type_arr)
            type = tmp_type[-1].as_pointer() # 最终是这个对应类型的指针
        else :                      # 不是数组
            pass
        arg_types.append(type)
        arg_names.append(arg_name)

    # 声明完毕，开始定义函数
    funcType = ir.FunctionType(retType, tuple(arg_types))

    # 构建基本块和Buidler
    func.llvm_func = ir.Function(module, funcType, funcName)
    for arg in func.llvm_func.args:     # 函数参数绑定名称
        arg.name = arg_names.pop(0)

    primary_block = func.llvm_func.append_basic_block(funcName+'primary')
    builder = ir.IRBuilder(primary_block)
    global builder_list
    builder_list.append(builder)        # 导入Budiler列表           

    # 创建局部变量表
    local_var.append({})


ast.evaluate(funcbuilder)

# ----------------------------第二遍扫描-----------------------------------
# 几个关键的概念，关于如何生成llvmlite库所定义的语句(基本与llvm ir一致)
# module 文件概念，其中包含着全局变量，全局函数的声明和定义
# function 函数概念，其中包含着多个block，函数参数，函数返回值
# block 基本块，是一条主干语句的集合，每个基本块都有一个唯一的入口和出口
# builder 基本块的构造器，本程序默认一个函数拥有一个Builder，他可以指向function中的任意block的任意位置，并生成新的代码
# 诸如 builder_now.load() builder_now.add() builder_now.branch() ...


# 一些全局数据，在不同的注册函数间共享信息

# func和block定位
func_no = 0
block_no = 0

# builder_now 表示当前处理的第一个函数的builder，后序不断更新
builder_now = builder_list[0]


# 第二遍扫描的注册器
# 这一遍包含了所有语句的生成，block的跳转，变量声明，函数调用
# 理解它们的实现原理，可以关注装饰器的信号量，以及对应的AST节点的语义动作

aar = ASTActionRegister()

def append_block(name: str):
    global builder_now, block_no
    if len(builder_now.block.instructions) == 0:
        return
    name = module.get_unique_name(name)
    new_blk = builder_now.append_basic_block(name)
    block_no += 1
    builder_now.position_at_start(new_blk)
    return new_blk

@aar.action("varDec")
def _varDec(varDec, type_, idList):
    global builder_now
    append_block('var')
    type = get_llvm_type(type_.getContent())
    vname = ''
    var = None
    for node in idList.getChilds():
        if node.getContent() == 'assign':
            vname = node.getChilds()[0].getContent()
            var = builder_now.alloca(type, name=vname)
            builder_now.store(node.getChilds()[1].value, var)
        elif node.__actionID == 'id_var':
            vname = node.getContent()  
            var = builder_now.alloca(type, name=vname)
        elif node.__actionID == 'array':
            vname = node.getContent()
            tmp_type = []
            for array_dim in node.dim:
                array_dim = int(array_dim)
                if len(tmp_type) == 0:
                    type_arr = ir.ArrayType(type, array_dim)
                else:
                    type_arr = ir.ArrayType(tmp_type[-1], array_dim)
                tmp_type.append(type_arr)
            var = builder_now.alloca(tmp_type[-1], name=vname)

        if vname not in local_var[func_no]:
            local_var[func_no][vname] = varelem()
        if node.__actionID == 'array':
            local_var[func_no][vname].array = True
        local_var[func_no][vname].ptr = var

@aar.action("assign")
def _assign_begin(assg, l, r):
    if 'value' in l:
        if l.__actionID == 'id_var':
            ptr = local_var[func_no][l.getContent()].ptr
            builder_now.store(r.value, ptr, align=4)
            local_var[func_no][l.getContent()].load = None
            l.value = ptr
        elif isinstance(l.value, ir.LoadInstr):
            builder_now.store(r.value, l.value.operands[0], align=4)
        else:
            builder_now.store(r.value, l.value)

        assg.value = l.value
    else:
        print("%s的赋值推后到声明时完成" % l.getContent())

@aar.action("id_var")
def _id_var(id_):
    global builder_now
    name = id_.getContent()

    # 在全局变量表中查找
    # for var in module.global_variables:
    #     if var.name == name:
    #         id_.var = var
    #         return

    # 在局部变量表中查找
    if name in local_var[func_no]:
        if local_var[func_no][name].array:
            id_.value = local_var[func_no][name].ptr
            return
        if local_var[func_no][name].load == None:
            ptr = local_var[func_no][name].ptr
            local_var[func_no][name].load = builder_now.load(ptr, name=name)
        id_.value = local_var[func_no][name].load
        return
    
    # 在函数的args中查找
    for arg in builder_now.function.args:
        if arg.name == name:
            id_.value = arg
            return
    
    # 未找到，不做处理
    print("没有找到变量：%s，将在本语句声明" % name)

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

@aar.action("stmtList", index=0)
def _stmtl(stmtl, *rest):
    # 仅仅作为block的切换函数
    stmtl.block = append_block('stmt')

@aar.action("ifBlock", index = 0)
def _ifBlock_prestore(ifb, *childs):
    ifb.start_block = append_block('if')

break_block_list = []
con_block_list = []

def try_branch_block_to(block, dst):
    global builder_now
    if block.is_terminated:
        if block not in break_block_list and \
            block not in con_block_list: # TODO return block
            builder_now.position_at_end(block)
            print(block.instructions[-1])
            block.replace(block.instructions[-1], builder_now.branch(dst))
        return
    else:
        builder_now.position_at_end(block)
        builder_now.branch(dst)

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
        try_branch_block_to(childs[1].block, ifend)
        try_branch_block_to(childs[2].block, ifend)
    else:
        assert False # TODO not implement
        for i in range(0, len(childs), 2):

            builder_now.cbranch(childs[i].value, childs[i+1].block, childs[i+2].block)
            builder_now.position_at_end(childs[i+1].block)
            builder_now.branch(ifend)
    builder_now.position_at_end(ifend)

@aar.action("whileBlock", index = 0)
def _whileBlock_prestore(while_, c0, sl):
    while_.start_block = append_block('while')

@aar.action("whileBlock")
def _while(while_, c0, sl):
    global block_no
    block_no += 1
    while_end = builder_now.append_basic_block('while_end_' + sl.block.name)
    builder_now.position_at_end(while_.start_block)
    builder_now.cbranch(c0.value, sl.block, while_end)
    builder_now.position_at_end(sl.block)
    builder_now.branch(while_.start_block)

    for block in break_block_list:
        if block.is_terminated:
            block.replace(block.instructions[-1], builder_now.branch(while_end))
        else:
            builder_now.position_at_end(block)
            builder_now.branch(while_end)
    break_block_list.clear()

    for block in con_block_list:
        if block.is_terminated:
            block.replace(block.instructions[-1], builder_now.branch(while_.start_block))
        else:
            builder_now.position_at_end(block)
            builder_now.branch(while_.start_block)
    con_block_list.clear()

    builder_now.position_at_end(while_end)

@aar.action("forexpr", index = 0) 
def _forexpr_prestore(forexpr_, expr):
    forexpr_.block = append_block('forexpr')
   
@aar.action("forexpr") 
def _forexpr(forexpr_, expr):
    if 'value' in expr:
        if expr.__actionID == 'assign':
            name = expr.getChilds()[0].getContent()
            local_var[func_no][name].load = None
        forexpr_.value = expr.value

@aar.action("forBlock")
def _for(for_, init, expr1, expr0, stmtl):
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

    for block in break_block_list:
        if block.is_terminated:
            block.replace(block.instructions[-1], builder_now.branch(for_end))
        else:
            builder_now.position_at_end(block)
            builder_now.branch(for_end)
    break_block_list.clear()

    for block in con_block_list:
        if block.is_terminated:
            block.replace(block.instructions[-1], builder_now.branch(expr0.block))
        else:
            builder_now.position_at_end(block)
            builder_now.branch(expr0.block)
    con_block_list.clear()

    builder_now.position_at_end(for_end)

@aar.action("break")
def _break(break_):
    global break_block_list, builder_now
    break_block = builder_now.function.basic_blocks[block_no]
    break_block_list.append(break_block)

    append_block('brea_n')

@aar.action("continue")
def _continue(continue_):
    global con_block_list, builder_now, block_no
    continue_block = builder_now.function.basic_blocks[block_no]
    con_block_list.append(continue_block)

    append_block('con_n')

@aar.action("return")
def _return(return_, c0):
    # TODO return;
    # TODO conflicts with if_branch, for_branch, while_branch
    global builder_now
    type = builder_now.function.ftype.return_type
    funcName = builder_now.function.name
    builder_now.ret(builder_now.zext(c0.value, type))

@aar.action("parameterList")
def _pml(pml, *childs):
    pml.list = [_.value for _ in childs]

@aar.action("functionCall")
def _funcCall(funcCall, funcName, paramList):
    name = funcName.getContent()
    for func in module.functions:
        if func.name == name:
            funcCall.value = builder_now.call(func, paramList.list)
            return
    print('no function %s' % name)
    assert False

@aar.action("getitem")
def _getitem(getitem, array_, *childs):
    array = array_.value
    dims = [ir.Constant(ir.IntType(32), 0)]
    for dim_node in childs:
        if isinstance(dim_node, ir.Constant):
            dims.append(dim_node)
        else:
            dims.append(dim_node.value)

    global builder_now
    ptr = builder_now.gep(array, dims, name='ptr_' + array_.getContent())
    getitem.value = builder_now.load(ptr, name=array.name, align=4)
    
ast.evaluate(aar)

def check_block_endding():
    for builder in builder_list:
        for i, block in enumerate(builder.function.blocks):
            if not block.is_terminated:
                builder.position_at_end(block)
                builder.branch(builder.function.blocks[i+1])

check_block_endding()

with open(sys.argv[2], 'w') as f:
    f.write(str(module))
