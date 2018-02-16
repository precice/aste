import os, sys

def checkAdd(lib = None, header = None, usage = ""):
    """ Checks for a library and/or header and appends it to env if not already appended. """

    usage = " (needed for " + usage + ") " if usage else ""
    if lib and header:
        if not conf.CheckLibWithHeader(lib, header = header, autoadd=0, language="C++"):
            print("ERROR: Library '" + lib + "' or header '" + header + "'" + usage + "not found.")
            Exit(1)
        conf.env.AppendUnique(LIBS = [lib])
    elif lib:
        if not conf.CheckLib(lib, autoadd=0, language="C++"):
            print("ERROR: Library '" + lib + "'" + usage + "not found!")
            Exit(1)
        conf.env.AppendUnique(LIBS = [lib])
    elif header:
        if not conf.CheckCXXHeader(header):
            print("ERROR: Header '" + header + "'" + usage + "not found!")
            Exit(1)

    
vars = Variables(None, ARGUMENTS)

vars.Add(EnumVariable('build', 'Build type', "Debug", allowed_values=('Release', 'ReleaseWithDebug', 'Debug')))
vars.Add("compiler", "Compiler to use.", "mpicxx")
vars.Add(EnumVariable('platform', 'Special configuration for certain platforms', "none", allowed_values=('none', 'HazelHen')))


env = Environment(variables = vars, ENV = os.environ)
conf = Configure(env)

Help(vars.GenerateHelpText(env))

preciceRoot = os.getenv("PRECICE_ROOT")
if preciceRoot == None:
    print("PRECICE_ROOT is not set.")
    Exit(1)

env.Replace(CXX = env["compiler"])

env.Append(CCFLAGS = ['-Wall', '-std=c++11'])

if env["build"] == "Debug":
    env.Append(CCFLAGS = ['-O0', '-g3'])
    env.Append(LINKFLAGS = ["-rdynamic"])
elif env["build"] == "ReleaseWithDebug":
    env.Append(CCFLAGS = ['-O3', '-g3', '-fno-omit-frame-pointer'])
elif env["build"] == "Release":
    env.Append(CCFLAGS = ['-O3'])


env.Append(CPPPATH = [os.path.join(preciceRoot, "src")])
env.Append(LIBPATH = [os.path.join(preciceRoot, "build/last")])


if env["platform"] == "HazelHen":
    env.Append(CPPPATH = [os.environ['BOOST_ROOT'] + '/include'])
    env.Append(LIBPATH = [os.environ['BOOST_ROOT'] + '/lib'])
    env.Append(LINKFLAGS = ['-dynamic']) # Needed for correct linking against boost.log
    


checkAdd("precice", header = "precice/SolverInterface.hpp")
checkAdd("boost_program_options", header = "boost/program_options.hpp")


env = conf.Finish()

env.Program ( 'aste', ['main.cpp'] )
env.Program ( 'readMesh', ['readMesh.cpp'] )
