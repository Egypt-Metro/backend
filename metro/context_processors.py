# metro/context_processors.py

# Context processors are functions that run before rendering a template.
def project_name(request):
    return {
        'project_name': 'Egypt Metro',  # Project name
    }
