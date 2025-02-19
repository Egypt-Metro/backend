# apps/trains/management/commands/generate_api_docs.py

from django.core.management.base import BaseCommand
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenAPIRenderer


class Command(BaseCommand):
    help = "Generate API documentation"

    def handle(self, *args, **options):
        generator = SchemaGenerator()
        schema = generator.get_schema()
        renderer = OpenAPIRenderer()
        output = renderer.render(schema, None, None)

        with open("docs/api/swagger.yaml", "w") as f:
            f.write(output.decode())
