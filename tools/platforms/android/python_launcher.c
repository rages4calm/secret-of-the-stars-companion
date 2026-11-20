/* Start the bundled Android CPython distribution from nativeLibraryDir.
 * Setting home through PyConfig keeps isolated (-I) child invocations working.
 */
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <unistd.h>

int main(int argc, char **argv) {
    pid_t parent = getppid();
    if (prctl(PR_SET_PDEATHSIG, SIGTERM) != 0 || getppid() != parent) return 2;
    const char *home = getenv("SOTS_PYTHON_HOME");
    if (!home || home[0] != '/') {
        fputs("Missing private Python home\n", stderr);
        return 2;
    }
    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    config.write_bytecode = 0;
    PyStatus status = PyConfig_SetBytesString(&config, &config.home, home);
    if (!PyStatus_Exception(status)) {
        status = PyConfig_SetBytesString(&config, &config.program_name, argv[0]);
    }
    if (!PyStatus_Exception(status)) {
        status = PyConfig_SetBytesArgv(&config, argc, argv);
    }
    if (!PyStatus_Exception(status)) status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);
    if (PyStatus_Exception(status)) Py_ExitStatusException(status);
    return Py_RunMain();
}
