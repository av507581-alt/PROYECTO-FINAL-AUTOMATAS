
%locations
%error-verbose

%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>

extern FILE *yyin;
extern int   yylex(void);
extern int   cur_line, prev_line, at_eof;

void yyerror(const char *msg);
void report_error(const char *tipo, int line, const char *fmt, ...);

int err_lex = 0, err_sin = 0, err_sem = 0;

/* ---------------- Tabla de símbolos ---------------- */
typedef enum { T_INCIDENTE, T_SENSOR, T_LUZ } Tipo;

typedef struct {
    char nombre[64];
    Tipo tipo;
    int  linea;
    int  nivel;          /* incidente: 0 = sin asignar, 1..5          */
    int  reportado;      /* incidente                                 */
    char sensor[64];     /* incidente: sensor asociado                */
    int  estado;         /* luz: 1 = ON, 0 = OFF                      */
} Simbolo;

#define MAX_SIM 512
static Simbolo tabla[MAX_SIM];
static int nsim = 0;
static int incidente_actual = -1;   /* último INCIDENTE declarado     */
static int    temp_declarada = 0;
static double temp_valor = 0;

#define TEMP_MIN (-50)
#define TEMP_MAX 100

static const char *nombre_tipo(Tipo t) {
    switch (t) {
        case T_INCIDENTE: return "INCIDENTE";
        case T_SENSOR:    return "SENSOR";
        default:          return "LUZ";
    }
}

static int buscar(const char *n) {
    int i;
    for (i = 0; i < nsim; i++)
        if (strcmp(tabla[i].nombre, n) == 0) return i;
    return -1;
}

/* Declara un identificador; devuelve su índice o -1 si hubo error */
static int declarar(const char *n, Tipo t, int linea) {
    int i = buscar(n);
    Simbolo *s;
    if (i >= 0) {
        report_error("SEMANTICO", linea,
            "Identificador '%s' ya declarado en la línea %d como %s",
            n, tabla[i].linea, nombre_tipo(tabla[i].tipo));
        return -1;
    }
    if (nsim >= MAX_SIM) {
        report_error("SEMANTICO", linea, "Tabla de símbolos llena");
        return -1;
    }
    s = &tabla[nsim];
    memset(s, 0, sizeof(Simbolo));
    strncpy(s->nombre, n, sizeof(s->nombre) - 1);
    s->tipo  = t;
    s->linea = linea;
    return nsim++;
}

/* Exige que 'n' exista y sea del tipo 't'; devuelve índice o -1 */
static int exigir(const char *n, Tipo t, int linea, const char *instr) {
    int i = buscar(n);
    if (i < 0) {
        report_error("SEMANTICO", linea,
            "Identificador '%s' no declarado (usado en %s)", n, instr);
        return -1;
    }
    if (tabla[i].tipo != t) {
        report_error("SEMANTICO", linea,
            "Tipo incompatible: '%s' es %s pero %s requiere %s",
            n, nombre_tipo(tabla[i].tipo), instr, nombre_tipo(t));
        return -1;
    }
    return i;
}
%}

%union {
    char  *s;
    double num;
    int    ival;
}

%destructor { free($$); } <s>

%token END 0 "fin de archivo"
%token INCIDENTE "INCIDENTE"
%token SENSOR "SENSOR"
%token NIVEL "NIVEL"
%token REPORTAR "REPORTAR"
%token LUZ "LUZ"
%token TEMPERATURA "TEMPERATURA"
%token SI "SI"
%token ENTONCES "ENTONCES"
%token ENCENDER "ENCENDER"
%token APAGAR "APAGAR"
%token MOSTRAR "MOSTRAR"
%token FIN "FIN"
%token ON "ON"
%token OFF "OFF"
%token SEMI ";"
%token GT ">"
%token LT "<"
%token GE ">="
%token LE "<="
%token EQ "=="
%token NE "!="
%token <s>   IDENT  "identificador"
%token <s>   CADENA "cadena"
%token <num> NUMERO "número"

%type <ival> estado

%%

programa
    : /* vacío */ {
          report_error("SINTACTICO", 1,
              "El programa está vacío: se requiere al menos una instrucción");
      }
    | sentencias
    ;

sentencias
    : sentencia
    | sentencias sentencia
    ;

sentencia
    : decl_incidente
    | decl_sensor
    | decl_nivel
    | reportar
    | decl_luz
    | decl_temp
    | condicional
    | accion
    | error SEMI { yyerrok; }
    ;

/* INCIDENTE fuga_gas; */
decl_incidente
    : INCIDENTE IDENT SEMI {
          int i = declarar($2, T_INCIDENTE, @2.first_line);
          if (i >= 0) incidente_actual = i;
          free($2);
      }
    ;

/* SENSOR sensor_03; */
decl_sensor
    : SENSOR IDENT SEMI {
          int i;
          if (incidente_actual < 0)
              report_error("SEMANTICO", @1.first_line,
                  "SENSOR declarado sin un INCIDENTE previo");
          i = declarar($2, T_SENSOR, @2.first_line);
          if (i >= 0 && incidente_actual >= 0) {
              if (tabla[incidente_actual].sensor[0])
                  report_error("SEMANTICO", @1.first_line,
                      "El incidente '%s' ya tiene el sensor '%s' asignado",
                      tabla[incidente_actual].nombre,
                      tabla[incidente_actual].sensor);
              else
                  strncpy(tabla[incidente_actual].sensor, $2,
                          sizeof(tabla[incidente_actual].sensor) - 1);
          }
          free($2);
      }
    ;

/* NIVEL 4; */
decl_nivel
    : NIVEL NUMERO SEMI {
          if (incidente_actual < 0)
              report_error("SEMANTICO", @1.first_line,
                  "NIVEL declarado sin un INCIDENTE previo");
          else if ((int)$2 != $2 || $2 < 1 || $2 > 5)
              report_error("SEMANTICO", @2.first_line,
                  "Nivel %g inválido: debe ser un entero entre 1 y 5", $2);
          else
              tabla[incidente_actual].nivel = (int)$2;
      }
    ;

/* REPORTAR fuga_gas; */
reportar
    : REPORTAR IDENT SEMI {
          int i = exigir($2, T_INCIDENTE, @2.first_line, "REPORTAR");
          if (i >= 0) {
              if (tabla[i].nivel == 0)
                  report_error("SEMANTICO", @2.first_line,
                      "El incidente '%s' no tiene NIVEL asignado antes de reportarlo", $2);
              else if (tabla[i].reportado)
                  report_error("SEMANTICO", @2.first_line,
                      "El incidente '%s' ya fue reportado", $2);
              else
                  tabla[i].reportado = 1;
          }
          free($2);
      }
    ;

/* LUZ luz_principal ON; */
decl_luz
    : LUZ IDENT estado SEMI {
          int i = declarar($2, T_LUZ, @2.first_line);
          if (i >= 0) tabla[i].estado = $3;
          free($2);
      }
    ;

estado
    : ON  { $$ = 1; }
    | OFF { $$ = 0; }
    ;

/* TEMPERATURA 22; */
decl_temp
    : TEMPERATURA NUMERO SEMI {
          if ($2 < TEMP_MIN || $2 > TEMP_MAX)
              report_error("SEMANTICO", @2.first_line,
                  "Temperatura %g fuera del rango permitido (%d a %d)",
                  $2, TEMP_MIN, TEMP_MAX);
          else { temp_declarada = 1; temp_valor = $2; }
      }
    ;

/* SI TEMPERATURA > 28 ENTONCES APAGAR luz_principal; FIN */
condicional
    : SI TEMPERATURA operador NUMERO ENTONCES accion FIN {
          if (!temp_declarada)
              report_error("SEMANTICO", @2.first_line,
                  "TEMPERATURA usada en la condición sin haber sido declarada antes");
          if ($4 < TEMP_MIN || $4 > TEMP_MAX)
              report_error("SEMANTICO", @4.first_line,
                  "Valor %g de la condición fuera del rango (%d a %d)",
                  $4, TEMP_MIN, TEMP_MAX);
      }
    | SI error FIN { yyerrok; }
    ;

operador
    : GT | LT | GE | LE | EQ | NE
    ;

accion
    : ENCENDER IDENT SEMI {
          exigir($2, T_LUZ, @2.first_line, "ENCENDER");
          free($2);
      }
    | APAGAR IDENT SEMI {
          exigir($2, T_LUZ, @2.first_line, "APAGAR");
          free($2);
      }
    | MOSTRAR IDENT SEMI {
          if (buscar($2) < 0)
              report_error("SEMANTICO", @2.first_line,
                  "Identificador '%s' no declarado (usado en MOSTRAR)", $2);
          free($2);
      }
    | MOSTRAR CADENA SEMI {
          free($2);
      }
    ;

%%

/* ---------------- Manejo de errores ---------------- */

void report_error(const char *tipo, int line, const char *fmt, ...) {
    char buf[512];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if      (strcmp(tipo, "LEXICO") == 0)     err_lex++;
    else if (strcmp(tipo, "SINTACTICO") == 0) err_sin++;
    else                                      err_sem++;
    printf("ERROR|%s|%d|%s\n", tipo, line, buf);
}

/* Reemplaza todas las apariciones de 'from' por 'to' */
static void reemplazar(const char *src, const char *from, const char *to,
                       char *out, size_t outsz) {
    size_t lf = strlen(from), lt = strlen(to), n = 0;
    const char *p = src, *q;
    out[0] = '\0';
    while ((q = strstr(p, from)) != NULL) {
        size_t pre = (size_t)(q - p);
        if (n + pre + lt + 1 >= outsz) break;
        memcpy(out + n, p, pre);  n += pre;
        memcpy(out + n, to, lt);  n += lt;
        p = q + lf;
    }
    if (n + strlen(p) + 1 < outsz) { strcpy(out + n, p); }
    else out[n] = '\0';
}

void yyerror(const char *msg) {
    char a[512], b[512];
    int  line = cur_line;
    const char *esp = strstr(msg, "expecting");

    /* Si falta ';', el error se reporta en la línea de la instrucción
       anterior (donde realmente falta), no en la del siguiente token. */
    if (!at_eof && esp && strchr(esp, ';') && cur_line > prev_line)
        line = prev_line;

    reemplazar(msg, "syntax error, ", "", a, sizeof(a));
    reemplazar(a, "syntax error", "Error de sintaxis", b, sizeof(b));
    reemplazar(b, "unexpected ", "token inesperado: ", a, sizeof(a));
    reemplazar(a, ", expecting ", "; se esperaba: ", b, sizeof(b));
    reemplazar(b, " or ", " o ", a, sizeof(a));
    if (a[0]) a[0] = (char)toupper((unsigned char)a[0]);

    report_error("SINTACTICO", line, "%s", a);
}

/* ---------------- Programa principal ---------------- */

int main(int argc, char **argv) {
    int i;
    FILE *f;

    if (argc < 2) {
        fprintf(stderr, "Uso: %s archivo_fuente\n", argv[0]);
        return 2;
    }
    f = fopen(argv[1], "r");
    if (!f) {
        perror("No se pudo abrir el archivo");
        return 2;
    }
    yyin = f;
    yyparse();
    fclose(f);

    for (i = 0; i < nsim; i++) {
        Simbolo *s = &tabla[i];
        if (s->tipo == T_INCIDENTE)
            printf("SYM|%s|INCIDENTE|%d|nivel=%d; sensor=%s; reportado=%s\n",
                   s->nombre, s->linea, s->nivel,
                   s->sensor[0] ? s->sensor : "-", s->reportado ? "si" : "no");
        else if (s->tipo == T_LUZ)
            printf("SYM|%s|LUZ|%d|estado inicial=%s\n",
                   s->nombre, s->linea, s->estado ? "ON" : "OFF");
        else
            printf("SYM|%s|SENSOR|%d|-\n", s->nombre, s->linea);
    }
    if (temp_declarada)
        printf("SYM|TEMPERATURA|TEMPERATURA|0|valor=%g\n", temp_valor);

    printf("SUMMARY|%d|%d|%d\n", err_lex, err_sin, err_sem);
    fflush(stdout);
    return (err_lex + err_sin + err_sem) ? 1 : 0;
}
