# ubume

Ubume is a small python module to cirucmvent slow startup times due to
long import times. On the first call, ubume will launch a server that
loads the specified module and then forks a client to actually execute
the module. Due to the forking most of the modules (apart from the
main module itself) are already imported.

Example usage:

```
python -m ubume /tmp/ubume_test_main.socket your_program_main -- arg1 arg2 arg3
```
further executions of `your_program_main` will use the launched fork server --- until the server times out and shuts down.
