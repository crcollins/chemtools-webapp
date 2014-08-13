from models import Job


def running_jobs(request):
    if request.user.is_authenticated():
        temp = len(Job.get_running_jobs(user=request.user))
        return {"running_jobs": temp}
    else:
        return {"running_jobs": None}
