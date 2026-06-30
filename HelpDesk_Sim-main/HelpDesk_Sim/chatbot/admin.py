from django.contrib import admin
from .models import QuestionAnswer

# Registreert QuestionAnswer in de Django admin, zodat FAQ-vragen en
# -antwoorden via het admin-paneel beheerd (toegevoegd/bewerkt/verwijderd)
# kunnen worden, in plaats van rechtstreeks in de database.
admin.site.register(QuestionAnswer)
