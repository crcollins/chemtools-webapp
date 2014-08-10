from django.contrib.auth.models import User

from models import Job
from interface import get_all_jobs


def run_all():
    for user in User.objects.all():
        creds = user.credentials.all()
        for i, cluster in enumerate(get_all_jobs(user)):
            cred = creds[i]
            jobs = {}
            jobids = []
            for job in cluster["jobs"]:
                status = job[-1]
                job_id = job[0]
                jobids.append(job_id)
                if status in jobs:
                    jobs[status].append(job_id)
                else:
                    jobs[status] = [job_id]
            running = Job.get_running_jobs(credential=cred)
            unknown = running.exclude(jobid__in=set(jobids)).values_list('jobid', flat=True)
            if unknown:
                jobs[Job.UNKNOWN] = list(unknown)
            Job.update_states(cred, jobs)


if __name__ == "__main__":
    run_all()
