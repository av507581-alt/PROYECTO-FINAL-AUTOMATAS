# Linux / macOS (requiere flex, bison >= 3 y gcc)
compilador: lex.yy.c parser.tab.c
	gcc -o compilador lex.yy.c parser.tab.c

parser.tab.c parser.tab.h: parser.y
	bison -d -o parser.tab.c parser.y

lex.yy.c: lexer.l parser.tab.h
	flex -o lex.yy.c lexer.l

clean:
	rm -f compilador lex.yy.c parser.tab.c parser.tab.h
