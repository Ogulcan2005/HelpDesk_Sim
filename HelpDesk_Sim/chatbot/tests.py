from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import Student, Teacher, ClassGroup
from chatbot.models import ChatLog

class ChatLogSecurityTest(TestCase):
    def setUp(self):
        # 1. Setup: Maak klas, docent en studenten aan
        self.klas = ClassGroup.objects.create(name="Klas A")
        
        # Docent in Klas A
        self.docent_user = User.objects.create_user(username="docent", password="pw")
        self.teacher = Teacher.objects.create(user=self.docent_user, class_group=self.klas)
        
        # Student in Klas A
        self.student_user = User.objects.create_user(username="student1", password="pw")
        self.student = Student.objects.create(user=self.student_user, class_group=self.klas)
        
        # Buitenstaander (Klas B)
        self.buiten_klas = ClassGroup.objects.create(name="Klas B")
        self.buiten_user = User.objects.create_user(username="buitenstaander", password="pw")
        self.buiten_student = Student.objects.create(user=self.buiten_user, class_group=self.buiten_klas)

        self.client = Client()
        self.client.login(username="docent", password="pw")

    def test_docent_kan_eigen_student_zien(self):
        """Test of de docent de chatlog van zijn eigen student kan inzien."""
        response = self.client.get(f'/chatbot/logs/{self.student_user.id}/')
        self.assertEqual(response.status_code, 200)

    def test_docent_kan_geen_andere_student_zien(self):
        """Test of de docent geblokkeerd wordt bij een student uit een andere klas."""
        response = self.client.get(f'/chatbot/logs/{self.buiten_user.id}/')
        
        # Controleer de statuscode 403
        self.assertEqual(response.status_code, 403)
        
        # Controleer of de foutmelding in de tekst staat (zonder dat er een template nodig is)
        self.assertContains(response, "Je hebt geen toestemming", status_code=403)