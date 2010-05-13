#!/usr/bin/python

import sys
import os
import pyggy
import getopt

MODO_USO = """ Modo de uso:

    %s -c nome_arquivo
 -s
    especificar o nome do executavel gerado.
"""


template = """

.assembly %s{}
.class %s extends [mscorlib]System.Object
{
	.method static public void main() il managed
	{
		.entrypoint
		.locals(int32 aux_int,
%s)
%s
br fim_code

erro_leint:
ldstr "Erro ao ler um valor inteiro"
call void [mscorlib]System.Console::WriteLine(string)
fim_code:
		ret
	}
}
.field public static valuetype CharArray8 Format at FormatData
//----------- Data declaration
.data FormatData = bytearray(25 64 00 00 00 00 00 00) // d . . . . . .
//----------- Value type as placeholder
.class public explicit CharArray8 
              extends [mscorlib]System.ValueType { .size 8 }
//----------- Calling unmanaged code
.method public static pinvokeimpl("msvcrt.dll" cdecl) 
    vararg int32 sscanf(string,int8*) cil managed { }

"""

# build the lexer and parser
l,ltab = pyggy.getlexer("mpython_lex.pyl")
#
#  A instancia da especificacao gramatical onde fica todas as acoes eh 'ptab'
#
p,ptab = pyggy.getparser("mpython_grm.pyg")
p.setlexer(l)

def usage(n):
    print MODO_USO % n
    sys.exit(0)

def gerar_codigo(nomeArqEntrada):
    l.setinput(nomeArqEntrada)
    tree = None
    try:
        tree = p.parse()
    except pyggy.ParseError,e:
        print "parse error in '%s' tok '%s' lineno=%d" % (e.str, str(e.tok), ltab.lineno)
        print ptab.tabSimb
        sys.exit(0)
    else:
        pyggy.proctree(tree, ptab)
        localVars = []
        for loc in ptab.tabSimb:
            localVars.append("class[mscorlib]System.Object %s" % ptab.tabSimb[loc].nome)
        bufferSaida = template % ("saida", "saida", ",\n".join(localVars), ptab.out)
        return bufferSaida

def compilar(bufferSaida,nomeArquivoSaida):
    nomeArquivoSaida=nomeArquivoSaida+".il"
    arqSaida = open(nomeArquivoSaida, 'w')
    arqSaida.write(bufferSaida)
    arqSaida.close()
    # Chamando o MONO para compilar o codigo em IL
    pipe = os.popen("ilasm %s" % nomeArquivoSaida,'r')
    if pipe.close():
        print "Ocorreu um erro ao tentar compilar o programa."


if __name__ == '__main__':
    try:
        opts,args = getopt.getopt(sys.argv[1:], "s:c")
    except getopt.GetoptError:
        usage(sys.argv[0])

    if not("-c" in sys.argv[1:]):
        print " Eh obrigatoria a especificacao do arquivo de entrada."
        usage(sys.argv[0])
    else:
        nomeArquivoEntrada = None
        apenasObj = False
        nomeArquivoSaida = None
        i = 0
        comando = sys.argv[1:]
        for opt in comando:
            if opt == "-c":
                if comando[i+1] != None and comando[i+1] != '':
                    nomeArquivoEntrada = comando[i+1]
            elif opt == "-s":
                if not (comando[i+1] in (None, "")):
                    nomeArquivoSaida = comando[i+1]
            i=i+1
        if nomeArquivoSaida == None:
            nomeArquivoSaida = os.path.splitext(nomeArquivoEntrada)[0]
        bufferSaida = gerar_codigo(nomeArquivoEntrada)
        compilar(bufferSaida, nomeArquivoSaida)

