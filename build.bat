@echo off
REM Windows: requiere WinFlexBison (win_flex / win_bison) y MinGW (gcc) en el PATH
win_bison -d -o parser.tab.c parser.y || goto :error
win_flex -o lex.yy.c lexer.l || goto :error
gcc -o compilador.exe lex.yy.c parser.tab.c || goto :error
echo.
echo Compilacion terminada: compilador.exe generado.
goto :eof
:error
echo Ocurrio un error durante la construccion.
exit /b 1
