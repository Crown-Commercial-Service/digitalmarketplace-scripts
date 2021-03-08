from invoke import task

from dmdevtools.invoke_tasks import library_tasks as ns
from dmdevtools.invoke_tasks import docker_build, docker_push


@task(ns["virtualenv"], ns["requirements-dev"])
def functional_tests(c):
    c.run("./functional-tests/setup.sh")
    c.run("cram -v functional-tests/")


ns.add_task(docker_build)
ns.add_task(docker_push)
ns.add_task(functional_tests)
