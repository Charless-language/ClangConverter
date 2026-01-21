package compiler

// Charless v3 opcodes
const (
	OP_HALT          = "000"
	OP_PRINT_STR     = "010"
	OP_PRINT_NUM     = "020"
	OP_PRINT_CHAR    = "040"
	OP_INPUT_CHAR    = "100"
	OP_INPUT_NUM     = "101"
	OP_PRINT_NEWLINE = "210"
	OP_PUSH          = "500"
	OP_POP           = "501"
	OP_STORE         = "510"
	OP_LOAD          = "511"
	OP_ADD           = "600"
	OP_SUB           = "601"
	OP_MUL           = "602"
	OP_DIV           = "603"
	OP_MOD           = "604"
	OP_JUMP          = "700"
	OP_JZ            = "701" // Jump if zero
	OP_JNZ           = "702"
	OP_EQN           = "801"
	OP_GT            = "802"
	OP_LT            = "803"
	OP_GTE           = "804"
	OP_LTE           = "805"

	SEP        = "200"
	PREFIX_NUM = "990"
)
