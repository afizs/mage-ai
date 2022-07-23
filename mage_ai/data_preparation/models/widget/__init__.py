from .charts import (
    MAX_BUCKETS,
    build_histogram_data,
)
from .constants import (
    ChartType,
    VARIABLE_NAMES_BY_CHART_TYPE,
    VARIABLE_NAME_BUCKETS,
    VARIABLE_NAME_GROUP_BY,
    VARIABLE_NAME_LIMIT,
    VARIABLE_NAME_METRICS,
    VARIABLE_NAME_X,
    VARIABLE_NAME_Y,
)
from .utils import calculate_metrics_for_group, convert_to_list, encode_values_in_list
from mage_ai.data_preparation.models.block import Block
from mage_ai.data_preparation.models.constants import (
    BlockStatus,
    BlockType,
    DATAFRAME_SAMPLE_COUNT_PREVIEW,
)
from mage_ai.shared.hash import ignore_keys, merge_dict
import numpy as np


class Widget(Block):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **ignore_keys(kwargs, ['configuration']))
        self.configuration = kwargs.get('configuration', {})

    @classmethod
    def create(
        self,
        name,
        block_type,
        repo_path,
        **kwargs,
    ):
        return super().create(
            name,
            block_type,
            repo_path,
            widget=True,
            **kwargs,
        )

    @classmethod
    def block_class_from_type(self, block_type: str) -> str:
        return BLOCK_TYPE_TO_CLASS.get(block_type)

    @classmethod
    def get_block(
        self,
        name,
        uuid,
        block_type,
        status=BlockStatus.NOT_EXECUTED,
        pipeline=None,
        configuration=None,
    ):
        block_class = BLOCK_TYPE_TO_CLASS.get(block_type, Block)
        return block_class(
            name,
            uuid,
            block_type,
            status=status,
            pipeline=pipeline,
            configuration=configuration,
        )

    @property
    def chart_type(self):
        return self.configuration.get('chart_type')

    @property
    def output_variable_names(self):
        var_names = VARIABLE_NAMES_BY_CHART_TYPE.get(self.chart_type, [])
        return [(var_name_orig, self.configuration.get(var_name_orig)) for var_name_orig in var_names]

    def delete(self):
        super().delete(widget=True)

    def get_variables_from_code_execution(self, results):
        data = {}
        for var_name_orig, var_name in self.output_variable_names:
            data[var_name_orig] = results.get(var_name)

        return data

    def to_dict(self, **kwargs):
        return merge_dict(super().to_dict(**kwargs), dict(
            configuration=self.configuration,
        ))

    def post_process_variables(
        self,
        variables,
        code=None,
        results={},
        upstream_block_uuids=[],
    ):
        data = variables.copy()
        group_by = self.configuration.get(VARIABLE_NAME_GROUP_BY)
        metrics = self.configuration.get(VARIABLE_NAME_METRICS)
        dfs = []
        for key in upstream_block_uuids:
            if key in results.keys():
                dfs.append(results[key])

        has_code = code and len(code.strip()) >= 1

        if ChartType.BAR_CHART == self.chart_type:
            if has_code:
                for var_name_orig, var_name in self.output_variable_names:
                    data.update({
                        var_name_orig: encode_values_in_list(convert_to_list(variables[var_name_orig])),
                    })
            elif len(dfs):
                df = dfs[0]
                groups = df.groupby(group_by)
                data[VARIABLE_NAME_X] = list(groups.groups.keys())
                data[VARIABLE_NAME_Y] = groups.apply(
                    lambda group: calculate_metrics_for_group(metrics, group),
                ).values
        elif ChartType.HISTOGRAM == self.chart_type:
            for var_name_orig, var_name in self.output_variable_names:
                values = [v for v in variables[var_name_orig] if v is not None and not np.isnan(v)]
                data = build_histogram_data(
                    values,
                    int(self.configuration.get(VARIABLE_NAME_BUCKETS, MAX_BUCKETS)),
                )
        elif ChartType.LINE_CHART == self.chart_type:
            for var_name_orig, var_name in self.output_variable_names:
                data.update({
                    var_name_orig: encode_values_in_list(convert_to_list(variables[var_name_orig])),
                })
        elif ChartType.PIE_CHART == self.chart_type:
            for var_name_orig, var_name in self.output_variable_names:
                values = [v for v in variables[var_name_orig] if v is not None]
                value_counts = {}
                for key in values:
                    if not value_counts.get(key):
                        value_counts[key] = 0
                    value_counts[key] += 1

                buckets = int(self.configuration.get(VARIABLE_NAME_BUCKETS, MAX_BUCKETS))
                arr = sorted(
                    list(zip(value_counts.values(), value_counts.keys())),
                    reverse=True,
                )[:buckets]
                value_counts_top = {k: v for v, k in arr}
                data.update({
                    var_name_orig: value_counts_top,
                })
        elif ChartType.TABLE == self.chart_type:
            for var_name_orig, var_name in self.output_variable_names:
                arr = variables[var_name_orig]
                limit = len(arr)
                if VARIABLE_NAME_Y == var_name_orig:
                    limit = int(self.configuration.get(
                        VARIABLE_NAME_LIMIT,
                        DATAFRAME_SAMPLE_COUNT_PREVIEW,
                    ))

                data.update({
                    var_name_orig: encode_values_in_list(convert_to_list(arr, limit=limit)),
                })

        return data


class ChartBlock(Widget):
    @property
    def output_variables(self):
        return dict()


BLOCK_TYPE_TO_CLASS = {
    BlockType.CHART: ChartBlock,
}
