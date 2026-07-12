"""
Airflow DAG — Pipeline Híbrido de Alfabetização no Brasil
Orquestra: Bronze → Quality (Silver input) → Silver → Gold → Quality (Gold)
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

default_args = {
    "owner": "data-team",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="pipeline_alfabetizacao",
    description="Pipeline híbrido de dados de alfabetização — Bronze > Silver > Gold",
    schedule_interval="0 6 * * *",  # diário às 6h UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["alfabetizacao", "educacao", "batch"],
) as dag:

    def task_ingest_bronze(**ctx):
        import sys, os
        sys.path.insert(0, os.path.join(os.environ.get("AIRFLOW_HOME", "/opt/airflow"), ".."))
        from pipelines.batch.bronze.ingest_bronze import run
        results = run()
        ctx["ti"].xcom_push(key="bronze_counts", value=results)

    def task_transform_silver(**ctx):
        from pipelines.batch.silver.transform_silver import run
        run()

    def task_build_gold(**ctx):
        from pipelines.batch.gold.build_gold import run
        run()

    def task_quality_silver(**ctx):
        from quality.quality_checks import check_silver_alfabetizacao
        report = check_silver_alfabetizacao()
        if not report.passed:
            raise ValueError(f"Quality check Silver falhou: {report.summary()}")

    def task_quality_gold(**ctx):
        from quality.quality_checks import check_gold_alfabetizacao_municipio, check_gold_evolucao_temporal
        for fn in [check_gold_alfabetizacao_municipio, check_gold_evolucao_temporal]:
            report = fn()
            if not report.passed:
                raise ValueError(f"Quality check Gold falhou: {report.summary()}")

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    bronze = PythonOperator(task_id="ingest_bronze", python_callable=task_ingest_bronze)
    quality_silver = PythonOperator(task_id="quality_check_silver", python_callable=task_quality_silver)
    silver = PythonOperator(task_id="transform_silver", python_callable=task_transform_silver)
    gold = PythonOperator(task_id="build_gold", python_callable=task_build_gold)
    quality_gold = PythonOperator(task_id="quality_check_gold", python_callable=task_quality_gold)

    start >> bronze >> silver >> quality_silver >> gold >> quality_gold >> end
