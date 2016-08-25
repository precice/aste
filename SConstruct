import os, sys

def uniqueCheckLib(conf, lib, header = None):
    """ Checks for a library and appends it to env if not already appended. """
    res = conf.CheckLibWithHeader(lib, header = header, autoadd=0, language="C++") if header \
          else conf.CheckLib(lib, autoadd=0, language="C++")
        
    conf.env.AppendUnique(LIBS = [lib])
    if res:
        return True
    else:
        print "ERROR: Library '" + lib + "' not found!"
        Exit(1)


vars = Variables(None, ARGUMENTS)

vars.Add(EnumVariable('build', 'Build type, either release or debug', "debug", allowed_values=('release', 'debug')))
vars.Add("compiler", "Compiler to use.", "g++")

env = Environment(variables = vars, ENV = os.environ)
conf = Configure(env)

Help(vars.GenerateHelpText(env))

preciceRoot = os.getenv("PRECICE_ROOT")
if preciceRoot == None:
    print("PRECICE_ROOT is not set.")
    Exit(1)

env.Append(CPPPATH = [os.path.join(preciceRoot, "src")])
env.Append(LIBPATH = [os.path.join(preciceRoot, "build/last")])
    
uniqueCheckLib(conf, "precice", header = "precice/SolverInterface.hpp")
uniqueCheckLib(conf, "boost_program_options", header = "boost/program_options.hpp")
    
env.Replace(CXX = env["compiler"])

env.Append(CCFLAGS = ['-Wall', '-std=c++11'])

if env["build"] == "debug":
    env.Append(CCFLAGS = ['-O0', '-g3'])
    env.Append(LINKFLAGS = ["-rdynamic"])
elif env["build"] == "release":
    env.Append(CCFLAGS = ['-O3'])

env = conf.Finish()
    
env.Program ( 'aste', ['main.cpp'] )
