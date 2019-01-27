# flake8: noqa


TIGER_STDLIB_STACK = """
LABEL(printint)
  __eval("print(vm.access_memory(vm.registers[14]+3), end='')")
  RETURN(FP_alt, PC_ret)


LABEL(print)
  __eval("addr = vm.access_memory(vm.registers[14]+3); n = vm.access_memory(addr)\\nfor i in range(n):\\n  print(chr(vm.access_memory(addr+i+1)), end='')")
  RETURN(FP_alt, PC_ret)


LABEL(println)
  __eval("addr = vm.access_memory(vm.registers[14]+3); n = vm.access_memory(addr)\\nfor i in range(n):\\n  print(chr(vm.access_memory(addr+i+1)), end='')\\nprint()")
  RETURN(FP_alt, PC_ret)


LABEL(exit)
  __eval("vm.pc = float('inf')")
  RETURN(FP_alt, PC_ret)


LABEL(div)
  __eval("left = vm.access_memory(vm.registers[14]+3); right = vm.access_memory(vm.registers[14]+4); vm.assign_memory(vm.registers[14]+3, left // right)")
  RETURN(FP_alt, PC_ret)


LABEL(size)
     INC(SP,1)
     STORE(R1,4,FP)
     LOAD(R1,3,FP) // Reg 1 <-- argument (address of string)
     LOAD(R1,0,R1)  // Reg 1 now has the size of string
     STORE(R1,3,FP) // put it (the size) into return area
     LOAD(R1,4,FP)
     DEC(SP,1)
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


// ** tstrcmp(s1:string, s2:string) : int
LABEL(tstrcmp)  // tiger strcmp -- like C strcmp
		// tstrcmp(a,b) returns neg # if a < b, 0 if =, pos # if a > b
		//  Note that this is also similar to doing CMP(a,b)
// Get some space, save some registers
     STORE(PC_ret, 0,FP) // For good practice
     STORE(FP_alt,1,FP)
     INC(SP,6)
     STORE(R1,10,FP)
     STORE(R2,5,FP)
     STORE(R3,6,FP)
     STORE(R4,7,FP)
     STORE(R5,8,FP)
     STORE(R6,9,FP)

// r3 = min(size(a), size(b))
     LOAD(R1,3,FP)	// r1 points to size of a
     LOAD(R2,4,FP)
     LOAD(R5,0,R1)		// r5 has size of a
     LOAD(R6,0,R2)		// r6 has size of b
     CMP(R5,R6)
     BLR(tstdlib_label_b_was_longer)
     ADD(R3,R5,R0)	// r3 = r5
     BR(tstdlib_label_got_min)
     LABEL(tstdlib_label_b_was_longer)
     ADD(R3,R6,R0)	// r3 = r6
     LABEL(tstdlib_label_got_min)  // now r3 is min. size
// r1 = address of 1st "real" char of a,
     INC(R1,1)
// r2 = address of 1st "real" char of b
// could also use this first:  LOAD(R2,4,FP)
     INC(R2,1)
// r4 = 0
     ADD(R4,R0,R0)
// while(r4<r3) {
     LABEL(tstdlib_label_start_of_while_in_tstrcmp)
     CMP(R4,R3)
     BGER(tstdlib_label_get_out_of_while_in_tstrcmp)
//  if (a[r4] < b[r4])  // add *(r4 + a) < *(r4 + b)
     ADD(R5,R4,R1)  // r5 = r4+a
     LOAD(R5,0,R5) // r5 = *(r4+a)
     ADD(R6,R4,R2)
     LOAD(R6,0,R6)
     CMP(R5,R6)
     BGER(tstdlib_label_not_a_smaller)
//  	return -1
     SET(R5,-1)
     STORE(R5,3,FP)
     BR(tstdlib_label_do_return)
     LABEL(tstdlib_label_not_a_smaller)
//  if (a[r4] > b[r4])
     CMP(R6,R5)
     BGER(tstdlib_label_not_b_smaller)
//		return 1
     SET(R5,1)
     STORE(R5,3,FP)
     BR(tstdlib_label_do_return)
     LABEL(tstdlib_label_not_b_smaller)
// 	r4++;
     INC(R4,1)
// }
     BR(tstdlib_label_start_of_while_in_tstrcmp)
     LABEL(tstdlib_label_get_out_of_while_in_tstrcmp)
// return size(a) - size(b)
     LOAD(R1,3,FP)	// r1 points to size of a
     LOAD(R2,4,FP)
     LOAD(R5,0,R1)		// r5 has size of a
     LOAD(R6,0,R2)		// r6 has size of b
     SUB(R5,R5,R6)		// r5 has size of a - size of b
     STORE(R5,3,FP)
     LABEL(tstdlib_label_do_return)
     LOAD(R1,10,FP)
     LOAD(R2,5,FP)
     LOAD(R3,6,FP)
     LOAD(R4,7,FP)
     LOAD(R5,8,FP)
     LOAD(R6,9,FP)
     LOAD(PC_ret, 0,FP)
     LOAD(FP_alt,1,FP)
     DEC(SP,6)
     RETURN(FP_alt, PC_ret)


//   substring(s:string, first:int, n:int) : string
LABEL(substring)
// vars & reg: sptr(1), nptr(2), n(3), tmp(4)
// store needed registers
     STORE(PC_ret, 0,FP)
     STORE(FP_alt,1,FP)
     INC(SP,9) // Space for registers and all function calls done by substring, in one fell swoop
     STORE(R1,6,FP)
     STORE(R2,7,FP)
     STORE(R3,8,FP)
     STORE(R4,9,FP)

     MOVE(FP_alt,SP)

// first check parameters
     LOAD(R1,3,FP)	// address of s  (points to its size)
     LOAD(R3,5,FP)      // R3 now "n" from here on

     LOAD(R4,4,FP)	// "first"
     ADD(R0,R4,R0)
     BS(substring_bad_params)   // check for first <0
     
     ADD(R0,R3,R0)
     BS(substring_bad_params)   // check for n<0

     ADD(R4,R4,R3)      // first+n
     LOAD(R2,0,R1)      // size of s
     CMP(R2,R4)
     BL(substring_bad_params)  // check for size(s)<first+n
     
// nptr = next free address   (allocate n+1 cells, save address for later)
     ADD(R4,R3,R0)      // R4 = n
     INC(R4,1)
     STORE(R4,3,FP_alt)
     CALL(FP_alt,malloc)
     LOAD(R2,3,FP_alt)	// R2 now nptr from here on

// save result of malloc (nptr) as return value   AND KILL "s"
     STORE(R2,3,FP)

// sptr = &s[first]
     INC(R1,1)  	// R1 is sptr from here on
     LOAD(R4,4,FP)	// "first"
     ADD(R1,R4,R1) 	// sptr now points to 1st char to grab
// *(nptr++) = n
     STORE(R3,0,R2)
     INC(R2,1)
     CALL(FP_alt,tstdlib_label_local_memcpy_reg)   // memcpy(sptr,nptr,n)
     LOAD(R1,6,FP)
     LOAD(R2,7,FP)
     LOAD(R3,8,FP)
     LOAD(R4,9,FP)
     LOAD(PC_ret, 0,FP)
     LOAD(FP_alt,1,FP)
     DEC(SP, 9)
     RETURN(FP_alt, PC_ret)		// value saved a while ago

     LABEL(substring_bad_params)
     SET(R1,substring_got_bad_params)
     STORE(R1,3,FP_alt)
     CALL(FP_alt,print)
     CALL(FP_alt,exit)


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
     BZ(tstdlib_label_memcpy_while_end)
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
TIGER_STRING("internal inconsistency in malloc -- program terminated\\n")

DLABEL(malloc_out_of_memory_error)
TIGER_STRING("out of memory in malloc -- program terminated\\n")

DLABEL(substring_got_bad_params)
TIGER_STRING("bad parameters to substring -- program terminated\\n")

DLABEL(tstdlib_not_implemented)
TIGER_STRING("this function is not yet implemented in tiger standard libarry; halting\\n")
DLABEL(tstdlib_not_tested)
TIGER_STRING("WARNING: Entering untested territory in tiger stdlib\\n")
"""
