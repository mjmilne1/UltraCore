"""Scheduled Jobs Tests"""
def test_job_scheduler():
    from ultracore.scheduled_jobs.scheduler.job_scheduler import JobScheduler
    scheduler = JobScheduler()
    cron = scheduler.parse_cron("0 2 * * *")
    assert cron["hour"] == "2"

def test_portfolio_valuation_job():
    from ultracore.scheduled_jobs.jobs.financial_jobs import PortfolioValuationJob
    job = PortfolioValuationJob()
    result = job.execute({})
    assert "portfolios_updated" in result

def test_ml_retraining_job():
    from ultracore.scheduled_jobs.jobs.ml_jobs import MLModelRetrainingJob
    job = MLModelRetrainingJob()
    result = job.execute({"model_type": "price_prediction"})
    assert "models_retrained" in result
