import os, sys

vars = Variables(None, ARGUMENTS)

vars.Add(BoolVariable("petsc", "Enable use of the Petsc linear algebra library.", True))
vars.Add(BoolVariable("python", "Enable use of Python.", True))


env = Environment(variables = vars, ENV = os.environ)
Help(vars.GenerateHelpText(env))

preciceRoot = os.getenv("PRECICE_ROOT")
if preciceRoot == None:
    print("PRECICE_ROOT is not set.")
    Exit(1)

cpppath = [os.path.join(preciceRoot, 'src')]
libpath = [os.path.join(preciceRoot, 'build/last')]


if env["petsc"]:
    petscDir = env["ENV"]["PETSC_DIR"]
    petscArch = env["ENV"]["PETSC_ARCH"]
    cpppath.append(os.path.join(petscDir, "include"))
    cpppath.append(os.path.join(petscDir, petscArch, "include"))
    libpath.append(os.path.join(petscDir, petscArch, "lib"))
    libpath.append(os.path.join(petscDir, petscArch, "lib"))
    
cppdefines = [ ]   

libs = [ 
    'precice',
    'python2.7' if env["python"] else '',
    'petsc'     if env["petsc"]  else '', 
    'boost_system',
    'boost_filesystem',
    'boost_program_options'
]

# cxx = 'g++' # For systems offering mpicxx compiler
cxx = 'mpicxx'      # For systems offering mpic++ compiler

ccflags = []
ccflags.append(['-O0', '-g3'])
ccflags.append(['-Wall', '-std=c++11'])

#libpath.append (preciceRoot + '/build/' + buildmode + '-dim2-nompi/')
#libpath.append('/usr/lib/')

##### Setup build environment and issue builds

env = Environment ( 
    CPPDEFINES = cppdefines,  # defines for preprocessor (#define xyz)
    LIBPATH    = libpath,     # path to libraries used
    LIBS       = libs,        # libraries used (without prefix "lib" and suffix ".a"/".so"/...)
    CPPPATH    = cpppath,     # pathes where the preprocessor should look for files
    CCFLAGS    = ccflags,     # flags for the c/c++ compilers
    CXX        = cxx,         # the c++ compiler that should be used
    ENV        = os.environ,  # propagates environment variables to scons
)

env.Program ( 'aste', ['main.cpp'] )
