from models import Job
from interface import get_all_jobs


def running_jobs(request):
    if request.user.is_authenticated():
        # hack to get numbers to update
        get_all_jobs(request.user)
        temp = len(Job.get_running_jobs(user=request.user))
        return {"running_jobs": temp}
    else:
        return {"running_jobs": None}
