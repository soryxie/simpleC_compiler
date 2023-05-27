	.text
	.globl	binarySearch            # -- Begin function binarySearch
	.ent	binarySearch
binarySearch:                           # @binarySearch
	.frame	$fp,56,$ra
	.mask 	0xc0000000,-4
	.set	noreorder
	.set	nomacro
	.set	noat
# %bb.0:                                # %binarySearchprimary
	addiu	$sp, $sp, -56
	sw	$ra, 52($sp)            # 4-byte Folded Spill
	sw	$fp, 48($sp)            # 4-byte Folded Spill
	move	$fp, $sp
	sw	$6, 36($fp)             # 4-byte Folded Spill
	sw	$5, 32($fp)             # 4-byte Folded Spill
	sw	$4, 28($fp)             # 4-byte Folded Spill
	j	$BB0_1
	nop
$BB0_1:                                 # %forexpr
	sw	$zero, 44($fp)
	lw	$1, 32($fp)             # 4-byte Folded Reload
	sw	$1, 40($fp)
	j	$BB0_2
	nop
$BB0_2:                                 # %forexpr.1
	lw	$1, 44($fp)
	lw	$2, 40($fp)
	slt	$3, $1, $2
	sw	$1, 24($fp)             # 4-byte Folded Spill
	sw	$2, 20($fp)             # 4-byte Folded Spill
	beqz	$3, $BB0_11
	nop
# %bb.3:                                # %forexpr.1
	j	$BB0_4
	nop
$BB0_4:                                 # %stmt
	lw	$1, 20($fp)             # 4-byte Folded Reload
	lw	$2, 24($fp)             # 4-byte Folded Reload
	subu	$3, $1, $2
	srl	$4, $3, 31
	addu	$3, $3, $4
	sra	$3, $3, 1
	addu	$3, $2, $3
	sw	$3, 16($fp)             # 4-byte Folded Spill
	j	$BB0_5
	nop
$BB0_5:                                 # %var
	move	$1, $sp
	addiu	$2, $1, -8
	move	$sp, $2
	lw	$3, 16($fp)             # 4-byte Folded Reload
	sw	$3, -8($1)
	sw	$2, 12($fp)             # 4-byte Folded Spill
	j	$BB0_6
	nop
$BB0_6:                                 # %if
	lw	$1, 12($fp)             # 4-byte Folded Reload
	lw	$2, 0($1)
	sll	$3, $2, 2
	lw	$4, 28($fp)             # 4-byte Folded Reload
	addu	$3, $4, $3
	lw	$3, 0($3)
	lw	$5, 36($fp)             # 4-byte Folded Reload
	slt	$3, $3, $5
	sw	$2, 8($fp)              # 4-byte Folded Spill
	beqz	$3, $BB0_9
	nop
# %bb.7:                                # %if
	j	$BB0_8
	nop
$BB0_8:                                 # %stmt.1
	lw	$1, 8($fp)              # 4-byte Folded Reload
	addiu	$2, $1, 1
	sw	$2, 44($fp)
	j	$BB0_10
	nop
$BB0_9:                                 # %stmt.2
	lw	$1, 8($fp)              # 4-byte Folded Reload
	sw	$1, 40($fp)
	j	$BB0_10
	nop
$BB0_10:                                # %if_end_if
	j	$BB0_11
	nop
$BB0_11:                                # %for_end_stmt
	lw	$1, 44($fp)
	lw	$2, 40($fp)
	xor	$1, $1, $2
	sltiu	$2, $1, 1
	move	$sp, $fp
	lw	$fp, 48($sp)            # 4-byte Folded Reload
	lw	$ra, 52($sp)            # 4-byte Folded Reload
	addiu	$sp, $sp, 56
	jr	$ra
	nop
	.set	at
	.set	macro
	.set	reorder
	.end	binarySearch

	.globl	main                    # -- Begin function main
	.ent	main
main:                                   # @main
# %bb.0:                                # %mainprimary
	addiu	$sp, $sp, -40
	sw	$ra, 36($sp)            # 4-byte Folded Spill
	sw	$fp, 32($sp)            # 4-byte Folded Spill
	move	$fp, $sp
	addiu	$1, $zero, 10
	sw	$1, 28($fp)
	j	$BB1_1
	nop
$BB1_1:                                 # %var
	move	$1, $sp
	addiu	$1, $1, -40
	move	$sp, $1
	sw	$1, 24($fp)             # 4-byte Folded Spill
	j	$BB1_2
	nop
$BB1_2:                                 # %forexpr
	move	$1, $sp
	addiu	$2, $1, -8
	move	$sp, $2
	sw	$zero, -8($1)
	sw	$2, 20($fp)             # 4-byte Folded Spill
	j	$BB1_4
	nop
$BB1_3:                                 # %forexpr.1
                                        #   in Loop: Header=BB1_4 Depth=1
	lw	$1, 20($fp)             # 4-byte Folded Reload
	lw	$2, 0($1)
	addiu	$2, $2, 1
	sw	$2, 0($1)
	j	$BB1_4
	nop
$BB1_4:                                 # %forexpr.2
                                        # =>This Inner Loop Header: Depth=1
	lw	$1, 20($fp)             # 4-byte Folded Reload
	lw	$2, 0($1)
	lw	$3, 28($fp)
	slt	$3, $2, $3
	sw	$2, 16($fp)             # 4-byte Folded Spill
	beqz	$3, $BB1_7
	nop
# %bb.5:                                # %forexpr.2
                                        #   in Loop: Header=BB1_4 Depth=1
	j	$BB1_6
	nop
$BB1_6:                                 # %stmt
                                        #   in Loop: Header=BB1_4 Depth=1
	lw	$1, 16($fp)             # 4-byte Folded Reload
	sll	$2, $1, 2
	lw	$3, 24($fp)             # 4-byte Folded Reload
	addu	$2, $3, $2
	sw	$1, 0($2)
	j	$BB1_3
	nop
$BB1_7:                                 # %for_end_stmt
	move	$1, $sp
	addiu	$2, $1, -8
	move	$sp, $2
	addiu	$2, $zero, 8
	sw	$2, -8($1)
	lw	$6, -8($1)
	addiu	$sp, $sp, -16
	addiu	$5, $zero, 10
	lw	$4, 24($fp)             # 4-byte Folded Reload
	jal	binarySearch
	nop
	addiu	$sp, $sp, 16
	sw	$2, 12($fp)             # 4-byte Folded Spill
	j	$BB1_8
	nop
$BB1_8:                                 # %var.1
	move	$1, $sp
	addiu	$2, $1, -8
	move	$sp, $2
	lw	$3, 12($fp)             # 4-byte Folded Reload
	sw	$3, -8($1)
	sw	$2, 8($fp)              # 4-byte Folded Spill
	j	$BB1_9
	nop
$BB1_9:                                 # %var.2
	move	$1, $sp
	addiu	$1, $1, -8
	move	$sp, $1
	sw	$1, 4($fp)              # 4-byte Folded Spill
	j	$BB1_10
	nop
$BB1_10:                                # %if
	lw	$1, 8($fp)              # 4-byte Folded Reload
	lw	$2, 0($1)
	bnez	$2, $BB1_13
	nop
# %bb.11:                               # %if
	j	$BB1_12
	nop
$BB1_12:                                # %stmt.1
	lw	$1, 4($fp)              # 4-byte Folded Reload
	sw	$zero, 0($1)
	j	$BB1_14
	nop
$BB1_13:                                # %stmt.2
	addiu	$1, $zero, 1
	lw	$2, 4($fp)              # 4-byte Folded Reload
	sw	$1, 0($2)
	j	$BB1_14
	nop
$BB1_14:                                # %if_end_if
	lw	$1, 4($fp)              # 4-byte Folded Reload
	lw	$2, 0($1)
	move	$sp, $fp
	lw	$fp, 32($sp)            # 4-byte Folded Reload
	lw	$ra, 36($sp)            # 4-byte Folded Reload
	addiu	$sp, $sp, 40
	jr	$ra
	nop
	.set	at
	.set	macro
	.set	reorder
	.end	main
