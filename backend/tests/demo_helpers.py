"""Native response assertions through the same job lifecycle as the browser."""


async def resolve_demo_job(response, maker):
    """Browser-equivalent job polling for native response-contract regression tests."""
    from httpx import Response

    from feature_demo.models import DemoJob
    from feature_demo.worker import run_job

    if response.status_code != 202 or "job_id" not in response.json():
        return response
    job_id = response.json()["job_id"]
    await run_job(job_id, maker)
    async with maker() as db:
        job = await db.get(DemoJob, job_id)
        if job.status == "completed":
            return Response(
                job.result["http_status"],
                json=job.result["body"],
                headers={"Cache-Control": "no-store"},
            )
        return Response((job.result or {}).get("status_code", 503), json={"detail": job.error_code})
