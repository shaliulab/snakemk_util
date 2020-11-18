import os.path
import json
import logging

import snakemk_util
import snakemake.workflow
import snakemake.exceptions

class UniversalSnakemake:

    def __init__(self, snakefile):
        self.snakefile = snakefile
        self.workflow = snakemake.workflow.Workflow(snakefile)

    def load_rule(self, rule, defaults=None, root="."):
        """
        Load the IO and params of a rule `rule` in a snakefile
        """

        try:
            snakemake_rule = snakemk_util.load_rule_args(
                snakefile=self.snakefile,
                rule_name=rule,
                default_wildcards=defaults,
                root=root
            )
        except snakemake.exceptions.WildcardError as error:
            logging.warning(f"Rule {rule} requires wilcards. Please see exception")
            raise error

        return snakemake_rule

    def export_rules(self, json_file):
        """
        Cant find a way to view available rules.
        Rules is initialized to an empty list
        which does not get populated upon init
        """
        raise NotImplemented

    def export_rule(self, rule, json_file, *args, **kwargs):
        """
        Exports a rule to json for easy loading into R
        """

        if isinstance(rule, str):
            rule = self.load_rule(rule, *args, **kwargs)

        rule_attrs = dir(rule)
        rule_attrs_dict = {}
        for a in rule_attrs:
            if a[:2] != "__":
                v = getattr(rule, a)

                rule_attrs_dict[a] = v

        json_file = os.path.join(os.getcwd(), json_file)
        logging.info(f"Saving json to {json_file}")
        with open(json_file, "w") as fh:
            json.dump(rule_attrs_dict, fh, indent="")


if __name__ == "__main__":

    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--snakefile")
    ap.add_argument("--rule")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", default=None)
    ap.add_argument("output", help="Output json file")

    args = ap.parse_args()

    us = UniversalSnakemake(args.snakefile)

    if args.json is None:
        defaults = None
    else:
        with open(args.json, "r") as fh:
            defaults = json.load(fh)

    us.export_rule(args.rule, args.output, defaults=defaults, root=args.root)

