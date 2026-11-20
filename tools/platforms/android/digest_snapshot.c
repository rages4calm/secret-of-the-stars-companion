#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <marshal.h>
#include <math.h>

/* Encode only exact builtin trees. The token is an in-process cache key,
 * never a replacement for the emitter's canonical SHA-256 proof. */
static int consume(Py_ssize_t *budget, Py_ssize_t size) {
    if (size > *budget) return 0;
    *budget -= size;
    return 1;
}

static int snapshot_shape(PyObject *value, unsigned depth, Py_ssize_t *budget) {
    if (depth > 32 || !consume(budget, 8)) return 0;
    if (value == Py_None || PyBool_Check(value)) return 1;
    if (PyLong_CheckExact(value)) {
        int overflow;
        PyLong_AsLongLongAndOverflow(value, &overflow);
        if (PyErr_Occurred()) return -1;
        return !overflow && consume(budget, 12);
    }
    if (PyFloat_CheckExact(value)) return isfinite(PyFloat_AS_DOUBLE(value)) && consume(budget, 8);
    if (PyUnicode_CheckExact(value)) {
        Py_ssize_t length = PyUnicode_GET_LENGTH(value);
        return length <= *budget / 4 && consume(budget, length * 4);
    }
    if (PyBytes_CheckExact(value)) return consume(budget, PyBytes_GET_SIZE(value));
    if (PyByteArray_CheckExact(value)) return consume(budget, PyByteArray_GET_SIZE(value));

    if (PyList_CheckExact(value) || PyTuple_CheckExact(value)) {
        int list = PyList_CheckExact(value);
        Py_ssize_t size = list ? PyList_GET_SIZE(value) : PyTuple_GET_SIZE(value);
        for (Py_ssize_t index = 0; index < size; ++index) {
            PyObject *item = list ? PyList_GET_ITEM(value, index) : PyTuple_GET_ITEM(value, index);
            int supported = snapshot_shape(item, depth + 1, budget);
            if (supported != 1) return supported;
        }
        return 1;
    }

    if (PyDict_CheckExact(value)) {
        PyObject *key, *item;
        Py_ssize_t cursor = 0;
        while (PyDict_Next(value, &cursor, &key, &item)) {
            int supported = snapshot_shape(key, depth + 1, budget);
            if (supported != 1) return supported;
            supported = snapshot_shape(item, depth + 1, budget);
            if (supported != 1) return supported;
        }
        return 1;
    }

    if (PySet_CheckExact(value) || PyFrozenSet_CheckExact(value)) {
        PyObject *iterator = PyObject_GetIter(value);
        if (!iterator) return -1;
        PyObject *item;
        while ((item = PyIter_Next(iterator)) != NULL) {
            int supported = snapshot_shape(item, depth + 1, budget);
            Py_DECREF(item);
            if (supported != 1) {
                Py_DECREF(iterator);
                return supported;
            }
        }
        Py_DECREF(iterator);
        return PyErr_Occurred() ? -1 : 1;
    }
    return 0;
}

static PyObject *snapshot(PyObject *self, PyObject *value) {
    (void) self;
    Py_ssize_t budget = 1024 * 1024;
    int supported = snapshot_shape(value, 0, &budget);
    if (supported < 0) return NULL;
    if (!supported) Py_RETURN_NONE;
    /* Format 2 has no object-sharing references or interned-string shortcuts. */
    return PyMarshal_WriteObjectToString(value, 2);
}

static PyMethodDef methods[] = {
    {"snapshot", snapshot, METH_O, "Capture an exact builtin value for the proof cache."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_sots_digest_snapshot", NULL, -1, methods,
};

PyMODINIT_FUNC PyInit__sots_digest_snapshot(void) {
    return PyModule_Create(&module);
}
