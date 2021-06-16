from pprint import pprint

import pandas as pd


def build_airflow_dataframe(dags):
    data_frame = pd.DataFrame(dags)
    runs = [dag['runs'] for dag in dags]
    runs = [run for run_list in runs for run in run_list]
    run_dataframe = pd.DataFrame(runs).drop(
        columns=['conf', 'external_trigger'])

    data_frame = data_frame.drop(columns=['tags', 'runs'])
    merged_data_frame = pd.merge(data_frame, run_dataframe, on='dag_id',
                                 how='left')
    merged_data_frame['profile_and_version'] = merged_data_frame[
                                                   'version'] + " " + \
                                               merged_data_frame['profile']

    merged_data_frame['start_date'] = merged_data_frame[
        'start_date'].dt.strftime('%b %d, %Y @ %H:%M')
    merged_data_frame = merged_data_frame.drop(columns=['execution_date'])

    if pd.api.types.is_datetime64_any_dtype(merged_data_frame.end_date.dtype):
        merged_data_frame['end_date'] = merged_data_frame[
            'end_date'].dt.strftime('%b %d, %Y @ %H:%M')

    ordered_data_frame = merged_data_frame.reindex(
        columns=["dag_id", "dag_run_id", "platform", "profile_and_version",
                 "version", "release_stream", "profile", "start_date",
                 "end_date", "state"])
    df = {'response': group_by_platform(ordered_data_frame.rename(
        columns={"dag_id": "pipeline_id", "dag_run_id": "job_id"}))}
    return df


def group_by_platform(data_frame: pd.DataFrame):
    return [
        get_table(group[0], group[1].drop(columns=['platform']))
        for group in data_frame.groupby(by=['platform'])
    ]


def get_table(title: str, data_frame: pd.DataFrame):
    return {
        'title': title,
        'data' : get_framelist(data_frame)
    }


def get_framelist(data_frame: pd.DataFrame):
    return [
        get_frame(group[0], (group[1].drop(
            columns=['profile_and_version', 'profile', 'version'])))
        for group in data_frame.groupby(by=['profile_and_version'])
    ]


def get_frame(title: str, data_frame: pd.DataFrame):
    return {
        'version'   : title.title(),
        'cloud_data': data_frame.values.tolist(),
        'columns'   : [name.replace('_', ' ').title()
                       for name in data_frame.columns.tolist()]
    }
