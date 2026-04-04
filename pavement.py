# -*- coding: utf-8 -*-
"""Paver tasks for vendoring plugin dependencies into extlibs."""

from __future__ import annotations

import os
import shutil
import sys

from paver.easy import Bunch, BuildFailure, needs, options, path, sh, task

options(
    extlib=Bunch(
        requirements_file="requirements.txt",
        target_dir="extlibs",
    )
)


def _quote(value: object) -> str:
    return '"{}"'.format(str(value).replace('"', '\\"'))


@task
def clean_extlibs() -> None:
    """Remove vendored dependencies."""
    target = path(options.extlib.target_dir)
    if target.exists():
        shutil.rmtree(str(target))


@task
@needs("clean_extlibs")
def build_extlibs() -> None:
    """Install requirements into extlibs using pip --target."""
    requirements_file = path(options.extlib.requirements_file)
    if not requirements_file.exists():
        raise BuildFailure(
            "Missing requirements file: {}".format(requirements_file.abspath())
        )

    target = path(options.extlib.target_dir)
    if not target.exists():
        os.makedirs(str(target))

    cmd = (
        "{python} -m pip install "
        "-r {requirements} "
        "--target {target} "
        "--upgrade --no-compile"
    ).format(
        python=_quote(sys.executable),
        requirements=_quote(requirements_file.abspath()),
        target=_quote(target.abspath()),
    )
    sh(cmd)


@task
@needs("build_extlibs")
def default() -> None:
    """Build extlibs by default when running plain `paver`."""
    return None
