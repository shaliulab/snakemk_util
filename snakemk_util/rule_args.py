import os
from snakemake.workflow import Workflow
from dataclasses import dataclass

@dataclass
class SnakemakeRuleArgs:
    input: dict
    params: dict
    output: dict
    wildcards: dict


class AttrDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def map_custom_wd(workflow, path_iterable, root="."):
    """
    Make paths relative to the Snakemake working dir absolute

    * If a path is absolute, it is left unchanged
    * If it is relative, assume it is made absolute by
    prepending the root dir and the Snakemake workdir

    ex: `y_KCs_1/edgeR` becomes `/Projects/SCS/` + `results/20201118` + `y_KCs_1/edgeR`

    This makes certain operations straightforward while avoiding hardcoding absolute paths
    in Snakefiles (just on the call to this function)
    """

    def include_custom_wd(workflow, path):

        # if path is absolute, leave it
        if os.path.isabs(path):
            return path

        # Otherwise the path is relative
        # Make the path absolute
        # https://github.com/Hoeze/snakemk_util/issues/1
        # Just put together root and path if workdir is None
        if workflow._workdir is None:
            return os.path.join(root, path)
        # Otherwise put it in between
        else:
            return os.path.join(root, workflow._workdir, path)

    if isinstance(path_iterable, list):
        return list(map(lambda x: include_custom_wd(workflow, x), path_list))
    elif isinstance(path_iterable, dict):
        return {k: include_custom_wd(workflow, v) for k, v in path_iterable.items()}

def load_rule_args(snakefile, rule_name, default_wildcards=None, change_dir=False, create_dir=True, root="."):
    """
    Returns a rule object for some default arguments.
    Example usage:
        ```
        try:
            snakemake
        except NameError:
            snakefile_path = os.getcwd() + "/Snakefile"

            snakemake = load_rule_args(
                snakefile = snakefile_path,
                rule_name = 'create_prediction_target',
                default_wildcards={
                    'ds_dir': 'full_data_samplefilter'
                }
            )
        ```
    """
    # save current working dir for later
    cwd = os.getcwd()
    try:
        if default_wildcards == None:
            default_wildcards = dict()

        # change to snakefile directory
        os.chdir(os.path.dirname(snakefile))

        # load workflow
        workflow = Workflow(snakefile=snakefile)
        workflow.include(snakefile)
        # get rule
        rule = workflow.get_rule(rule_name)


        smk_input = dict(rule.expand_input(default_wildcards)[0])
        smk_output = dict(rule.expand_output(default_wildcards)[0])
        smk_params = dict(rule.expand_params(
            default_wildcards, rule.input, rule.output, AttrDict(rule.resources)
        ))


        # Make paths in snakemake inputs and outputs absolute
        smk_input = map_custom_wd(workflow, smk_input, root)
        smk_output = map_custom_wd(workflow, smk_output, root)


        if create_dir:
            if isinstance(smk_output, list):
                path_list = smk_output
            elif isinstance(smk_output, dict):
                path_list = list(smk_output.values())

            for path in path_list:
                dest_folder = os.path.join(cwd, os.path.dirname(path))
                if os.path.isdir(dest_folder):
                    pass
                else:
                    print(f"Creating output directory {dest_folder}")
                    os.makedirs(dest_folder)

        # setup rule arguments
        retval = SnakemakeRuleArgs(
            input=smk_input,
            params=smk_params,
            output=smk_output,
            wildcards=default_wildcards
        )
        return retval
    finally:
        if not change_dir:
            # change back to previous working directory
            os.chdir(cwd)
