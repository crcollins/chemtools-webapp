import logging


logger = logging.getLogger(__name__)


def get_templates_from_request(request):
    templates = []
    usertemps = request.user.templates.all()
    for key in request.POST:
        if ':' in key and request.POST[key] == "on":
            try:
                creator, name, id_ =  key.split(':')
                template = usertemps.get(
                    id=id_,
                    creator__username=creator,
                    name=name)
                templates.append(template)
            except Exception as e:
                logger.info("Could not find the template: %s:%s:%s" % (creator, name, id_))
                pass
    return templates