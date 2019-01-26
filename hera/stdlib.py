TIGER_STDLIB_STACK = """
LABEL(printint)
  __eval("print(vm.access_memory(vm.registers[14]+3), end='')")
  RETURN(FP_alt, PC_ret)


LABEL(print)
  __eval("addr = vm.access_memory(vm.registers[14]+3); n = vm.access_memory(addr)\nfor i in range(n):\n  print(chr(vm.access_memory(addr+i+1)), end='')")
  RETURN(FP_alt, PC_ret)


LABEL(exit)
  __eval("vm.pc = float('inf')")
  RETURN(FP_alt, PC_ret)


LABEL(concat)
// vars & reg: s1ptr/s2ptr(1), nptr(2), n(3), tmp(4), tmp2(5)

// store needed registers
     STORE(PC_ret, 0,FP)
     STORE(FP_alt,1,FP)
     INC(SP,9) // space for registers and calling functions

     STORE(R1,5,FP)
     STORE(R2,6,FP)
     STORE(R3,7,FP)
     STORE(R4,8,FP)
     STORE(R5,9,FP)

     MOVE(FP_alt,SP)

// malloc length(s1)+length(s2)+1
     LOAD(R3,3,FP)
     LOAD(R3,0,R3)	// get s1's length
     LOAD(R2,4,FP)
     LOAD(R2,0,R2)	// get s2's length
     ADD(R3,R2,R3)
     INC(R3,1)
     STORE(R3, 3,FP_alt)
     CALL(FP_alt,malloc)     // get space

     LOAD(R2, 3,FP_alt)     // allocated space
     DEC(R3,1)   	// sum of the lengths again
     STORE(R3, 0,R2)    // Set result's size
     LOAD(R1, 3,FP)	// s1
     STORE(R2, 3,FP)    // SAVE RESULT, AND KILL S1
     INC(R2,1)  	// R2 now next available space

     LOAD(R3, 0,R1)	// s1's size
     INC(R1,1)  	// sptr is now s1's initial character

// memcpy(nptr,s1ptr,length(s1))
     CALL(FP_alt,tstdlib_label_local_memcpy_reg)   // memcpy(sptr,nptr,n)
// memcpy(nptr,s2ptr,length(s2))
     LOAD(R1,4,FP)
     LOAD(R3,0,R1)	// get s2's length
     INC(R1,1)		// sptr is now s2's initial character
     CALL(FP_alt,tstdlib_label_local_memcpy_reg)   // memcpy(sptr,nptr,n)

     LOAD(R1,5,FP)
     LOAD(R2,6,FP)
     LOAD(R3,7,FP)
     LOAD(R4,8,FP)
     LOAD(R5,9,FP)
     LOAD(PC_ret, 0,FP)
     LOAD(FP_alt,1,FP)
     DEC(SP, 9)
     RETURN(FP_alt, PC_ret)		// value saved a while ago


LABEL(malloc)
     STORE(PC_ret, 0,FP)
     STORE(FP_alt,1,FP)
     INC(SP,3)
     STORE(R1,4,FP)
     STORE(R2,5,FP)
     STORE(R3,6,FP)

     LOAD(R1,3,FP) // Reg 1 <-- argument (number of cells needed)
     SET(R3,first_space_for_fsheap)
     LOAD(R2,0,R3) // R2 is address of first free
   BNZ(fsheap_already_initialized)
     MOVE(R2, R3)
     INC(R2, 1)    // initialize fs heap to its first free element then allocate from there
     STORE(R2,0,R3) // defensive programming --- this should be overwritten later and thus dead
   LABEL(fsheap_already_initialized)
     STORE(R2,3,FP)// RETURN VALUE DEFINED HERE

     ADD(R2,R2,R1) // ALLOCATE -- FAIL BELOW IF WRAPPED PAST END OF ADDRESS SPACE OR "last_space_for_heap"
     BC(malloc_give_up)
     SET(R1,last_space_for_fsheap)
     CMP(R2, R1)   // want (unsigned) R2 < R1, so R2-R1 should BORROW, i.e. NOT carry!
     BC(malloc_give_up)
     STORE(R2,0,R3)   // STORE BACK THE NEXT FREE SPACE

     LOAD(R1,4,FP)
     LOAD(R2,5,FP)
     LOAD(R3,6,FP)
     LOAD(PC_ret, 0,FP)
     LOAD(FP_alt,1,FP)
     DEC(SP, 3)
     RETURN(FP_alt, PC_ret)	// Normal return from malloc


   LABEL(malloc_inconsistent)
     SET(R1, malloc_inconsistent_error)
     BR(malloc_exit)
   LABEL(malloc_give_up)
     SET(R1,malloc_out_of_memory_error)
   LABEL(malloc_exit)

    MOVE(FP_alt,SP)
    INC(SP,4)

     STORE(R1,3,FP_alt)
     CALL(FP_alt,print)
     CALL(FP_alt,exit)
    DEC(SP, 4) // just to match


LABEL(tstdlib_label_local_memcpy_reg)
     // move n(reg 3) bytes from location sptr(reg 1) to location nptr (reg 2)
     // modifies registers 1, 2, 3, and 4
     //  (after end, r2 and r1 have been increased by original r3)
     ADD(R4,Rt,R0)
// while(n>0)
     LABEL(tstdlib_label_memcpy_while_begin)
     OR(R0,R0,R3)  // set flags for R3
     BZR(tstdlib_label_memcpy_while_end)
//   *(nptr++) = *(sptr++)
     LOAD(Rt,0,R1)
     INC(R1,1)
     STORE(Rt,0,R2)
     INC(R2,1)
//   n--
     DEC(R3,1)
     BR(tstdlib_label_memcpy_while_begin)
     LABEL(tstdlib_label_memcpy_while_end)
     ADD(Rt,R4,R0)
     RETURN(FP_alt, PC_ret)
"""


TIGER_STDLIB_STACK_DATA = """
CONSTANT(first_space_for_fsheap, 0x4000)
CONSTANT(last_space_for_fsheap, 0xbfff)


DLABEL(tiger_stdlib_endl)  /* manually build an "end-of-line" string */
INTEGER(1)
INTEGER(10)  /* control-j -- an end-of-line */

DLABEL(tiger_stdlib_hex_prefix)
TIGER_STRING("0x")
DLABEL(tiger_stdlib_printing_one_char_tmp)
TIGER_STRING(" ")
DLABEL(tiger_stdlib_ungetchar_one_char_tmp)  // size = defined; char = the char
INTEGER(0)  // 0=undefined; 1=defined
INTEGER(0)  // the character

DLABEL(malloc_inconsistent_error)
TIGER_STRING("internal inconsistency in malloc -- program terminated\n")

DLABEL(malloc_out_of_memory_error)
TIGER_STRING("out of memory in malloc -- program terminated\n")

DLABEL(substring_got_bad_params)
TIGER_STRING("bad parameters to substring -- program terminated\n")

DLABEL(tstdlib_not_implemented)
TIGER_STRING("this function is not yet implemented in tiger standard libarry; halting\n")
DLABEL(tstdlib_not_tested)
TIGER_STRING("WARNING: Entering untested territory in tiger stdlib\n")
"""
