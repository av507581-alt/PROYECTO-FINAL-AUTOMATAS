#ifndef YY_YY_PARSER_TAB_H_INCLUDED
# define YY_YY_PARSER_TAB_H_INCLUDED

#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int yydebug;
#endif


#ifndef YYTOKENTYPE
# define YYTOKENTYPE
   
   enum yytokentype {
     END = 0,
     INCIDENTE = 258,
     SENSOR = 259,
     NIVEL = 260,
     REPORTAR = 261,
     LUZ = 262,
     TEMPERATURA = 263,
     SI = 264,
     ENTONCES = 265,
     ENCENDER = 266,
     APAGAR = 267,
     MOSTRAR = 268,
     FIN = 269,
     ON = 270,
     OFF = 271,
     SEMI = 272,
     GT = 273,
     LT = 274,
     GE = 275,
     LE = 276,
     EQ = 277,
     NE = 278,
     IDENT = 279,
     CADENA = 280,
     NUMERO = 281
   };
#endif


#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED
typedef union YYSTYPE
{

#line 108 "parser.y"

    char  *s;
    double num;
    int    ival;



#line 91 "parser.tab.h"
} YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define yystype YYSTYPE /* obsolescent; will be withdrawn */
# define YYSTYPE_IS_DECLARED 1
#endif

#if ! defined YYLTYPE && ! defined YYLTYPE_IS_DECLARED
typedef struct YYLTYPE
{
  int first_line;
  int first_column;
  int last_line;
  int last_column;
} YYLTYPE;
# define yyltype YYLTYPE /* obsolescent; will be withdrawn */
# define YYLTYPE_IS_DECLARED 1
# define YYLTYPE_IS_TRIVIAL 1
#endif

extern YYSTYPE yylval;
extern YYLTYPE yylloc;
#ifdef YYPARSE_PARAM
#if defined __STDC__ || defined __cplusplus
int yyparse (void *YYPARSE_PARAM);
#else
int yyparse ();
#endif
#else 
#if defined __STDC__ || defined __cplusplus
int yyparse (void);
#else
int yyparse ();
#endif
#endif 

#endif 
