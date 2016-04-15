from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

from os import mkdir, remove, path
from shutil import rmtree

from custom_user.models import User

from .export import is_patient_active
from .input_export import InputExport, build_complete_export_structure
from .views import Survey, Questionnaires, QuestionnaireResponse, create_directory

from patient.models import Gender, Patient

# Constantes para testes de User
USER_EDIT = 'user_edit'
USER_USERNAME = 'myadmin'
USER_PWD = 'mypassword'
USER_NEW = 'user_new'

QUESTIONNAIRE_ID = 957421
TEST_QUESTIONNAIRE = 271192


class UtilTests:

    def create_patient_mock(self, name='Pacient Test', user=None):
        """ Cria um participante para ser utilizado durante os testes """
        gender = Gender.objects.create(name='Masculino')
        gender.save()

        p_mock = Patient()
        p_mock.name = name
        p_mock.date_birth = '2001-01-15'
        p_mock.cpf = '374.276.738-08'
        p_mock.gender = gender
        p_mock.changed_by = user
        p_mock.save()
        return p_mock

    #
    #     def create_cid10_to_search(self):
    #         cid10 = ClassificationOfDiseases.objects.create(code='A01', description='Febres paratifoide',
    #                                                         abbreviated_description='A01 Febres paratifoide')
    #         cid10.save()
    #         cid10 = ClassificationOfDiseases.objects.create(code='B01', description='Febres tifoide ',
    #                                                         abbreviated_description='B01 Febres tifoide ')
    #         cid10.save()
    #
    #     def create_cid10_mock(self):
    #         cid10 = ClassificationOfDiseases.objects.create(code='A01', description='Febres paratifoide',
    #                                                         abbreviated_description='A01 Febres paratifoide')
    #         cid10.save()
    #
    #         return cid10
    #
    #     def create_medical_record_mock(self, user, new_patient):
    #         medical_record = MedicalRecordData()
    #         medical_record.patient = new_patient
    #         medical_record.record_responsible = user
    #         medical_record.save()
    #         return medical_record
    #
    #     def create_diagnosis_mock(self, medical_record):
    #         cid10_mock = self.create_cid10_mock()
    #         diagnosis = Diagnosis(medical_record_data=medical_record, classification_of_diseases=cid10_mock)
    #         diagnosis.save()
    #
    #         return diagnosis
    #
    def create_survey_mock(self, survey_id, is_initial_evaluation):
        survey = Survey(lime_survey_id=survey_id, is_initial_evaluation=is_initial_evaluation)
        survey.save()

        return survey

    def create_token_id_mock(self, patient, survey):
        questionnaire_lime_survey = Questionnaires()
        result = questionnaire_lime_survey.add_participant(survey.lime_survey_id)
        questionnaire_lime_survey.release_session_key()

        return result['token_id']

    def create_response_survey_mock(self, user, patient, survey, token_id=None):
        if token_id is None:
            token_id = self.create_token_id_mock(patient, survey)

        questionnaire_response = QuestionnaireResponse(patient=patient, survey=survey, token_id=token_id,
                                                       questionnaire_responsible=user)
        questionnaire_response.save()

        return questionnaire_response


class DirectoryTest(TestCase):
    """ Cria um participante para ser utilizado durante os testes """
    user = ''
    data = {}

    def setUp(self):
        # """
        # Configure authentication and variables to start each test
        #
        # """
        # print('Set up for', self._testMethodName)

        self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.factory = RequestFactory()

        logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
        self.assertEqual(logged, True)

        self.basedir = path.join(path.join(path.dirname(path.realpath("__file__")), "test_directory"))

        mkdir(self.basedir)

    def tearDown(self):
        """ finalize test """

        #  delete directory and files created for testing
        rmtree(self.basedir)

    def test_directory_create(self):
        """ Test if directory is created correctly """
        path_to_create = "opt/"
        create_directory(self.basedir, path_to_create)

        self.assertTrue(path.exists(path.join(self.basedir, path_to_create)))

    def test_directory_already_exists(self):
        """ Test directory creation when it already exists """

        # in this case, nothing will change
        path_to_create = "opt/"

        mkdir(path.join(self.basedir, path_to_create))

        self.assertTrue(path.exists(path.join(self.basedir, path_to_create)))

        # call function to create an already created directory
        msg, path_created = create_directory(self.basedir, path_to_create)
        self.assertEquals(msg, "")
        self.assertEquals(path_created, path.join(self.basedir, path_to_create))

    def test_base_directory_does_not_exist(self):
        """ Test when base directory does not exist or contains incorrect name """

        path_to_create = "opt/"
        path_with_error = self.basedir + "/error_path"

        msg, path_created = create_directory(path_with_error, path_to_create)

        self.assertEquals(msg, _("Base path does not exist"))


class PatientActiveTest(TestCase):
    """ Cria um participante para ser utilizado durante os testes """
    user = ''
    data = {}
    util = UtilTests()

    def setUp(self):
        # """
        # Configure authentication and variables to start each test
        #
        # """
        # print('Set up for', self._testMethodName)

        self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.factory = RequestFactory()

        logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
        self.assertEqual(logged, True)

        # create user

    def test_active_patient(self):
        """ test correct path - everything is ok """

        patient_mock = self.util.create_patient_mock(user=self.user)
        survey_mock = self.util.create_survey_mock(QUESTIONNAIRE_ID, True)
        response_survey_mock = self.util.create_response_survey_mock(self.user, patient_mock, survey_mock)

        subject_id = str(float(patient_mock.pk))

        response = is_patient_active(subject_id)
        self.assertTrue(response)

        subject_id = str(patient_mock.pk)
        response = is_patient_active(subject_id)
        self.assertTrue(response)

    def test_subject_is_not_number(self):
        """ test when subject value is incorrect """

        subject_id = "subject_error"

        response = is_patient_active(subject_id)
        self.assertTrue(not response)

    def test_patient_not_in_questionnaire_response(self):
        """ test when subject is not in questionnaire response """

        patient_mock = self.util.create_patient_mock(user=self.user)
        survey_mock = self.util.create_survey_mock(QUESTIONNAIRE_ID, True)

        subject_id = str(float(patient_mock.pk))
        response = is_patient_active(subject_id)
        self.assertTrue(not response)

    def test_patient_removed_from_database(self):
        """ test when patient is removed """

        patient_mock = self.util.create_patient_mock(user=self.user)
        patient_mock.removed = True
        patient_mock.save()

        survey_mock = self.util.create_survey_mock(QUESTIONNAIRE_ID, True)
        response_survey_mock = self.util.create_response_survey_mock(self.user, patient_mock, survey_mock)

        subject_id = str(float(patient_mock.pk))
        response = is_patient_active(subject_id)
        self.assertTrue(not response)


# class ExportPatientTest(TestCase):
#
#     """ Cria um participante para ser utilizado durante os testes """
#     user = ''
#     data = {}
#     util = UtilTests()
#
#     def setUp(self):
#         # """
#         # Configure authentication and variables to start each test
#         #
#         # """
#         # print('Set up for', self._testMethodName)
#
#         self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
#         self.user.is_staff = True
#         self.user.is_superuser = True
#         self.user.save()
#
#         self.factory = RequestFactory()
#
#         logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
#         self.assertEqual(logged, True)
#
#     def test_patientexport_create(self):
#         """ Test if directory is created correctly """
#     def test_patientexport_a(self):
#         """ Test if directory is created correctly """
#     def test_patientexport_b(self):
#         """ Test if directory is created correctly """
#
#
class ExportQuestionnaireTest(TestCase):

    """ Cria um participante para ser utilizado durante os testes """
    user = ''
    data = {}
    util = UtilTests()

    def setUp(self):
        # """
        # Configure authentication and variables to start each test
        #
        # """
        # print('Set up for', self._testMethodName)

        self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.factory = RequestFactory()

        logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
        self.assertEqual(logged, True)

    def test_export(self):
        # create mock patient, questionnaire
        patient_mock = self.util.create_patient_mock(name=self._testMethodName, user=self.user)
        survey_mock = self.util.create_survey_mock(TEST_QUESTIONNAIRE, True)
        response_survey_mock = self.util.create_response_survey_mock(self.user, patient_mock, survey_mock, token_id=36)

        response = self.client.get(reverse('export_view'))
        self.assertEqual(response.status_code, 200)

        questionnaire_selected = ["271192*title*id*id",
                                  "271192*title*famliacanhoto2*famliacanhoto2",
                                  "271192*title*idteste[1][1]*idteste[1][1]"]

        patient_selected = ["id*id"]

        diagnosis_selected = ["medicalrecorddata__record_responsible_id*responsible_id"]

        self.data = {
            'questionnaire_selected': questionnaire_selected,
            'patient_selected':  patient_selected,
            'diagnosis_selected': diagnosis_selected,
            'per_questionnaire': 1,
            'per_participant': 1,
        }

        response = self.client.post(reverse('export_view'), self.data)
        self.assertEqual(response.status_code, 200)

        filename = path.join("export", path.join(str(self.user.id), "1/export.zip"))
        output_filename = path.join(settings.MEDIA_ROOT, filename)  # "export/<user.id>/1/export.zip"
        print(output_filename)
        self.assertTrue(path.isfile(output_filename))


class JsonTest(TestCase):
    """ Cria um participante para ser utilizado durante os testes """
    user = ''
    data = {}

    def setUp(self):
        # """
        # Configure authentication and variables to start each test
        #
        # """
        # print('Set up for', self._testMethodName)

        self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.factory = RequestFactory()

        logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
        self.assertEqual(logged, True)

    # def test_json_preparation(self):
    #     # questionnaire_code_list_example = [
    #     #     113491,
    #     #     256242,
    #     #     # 271192,
    #     #     # 345282,
    #     #     # 367311,
    #     #     # 456776,
    #     #     # 471898,
    #     #     # 578559,
    #     #     # 599846,
    #     #     # 885183,
    #     #     # 944684,
    #     #     # 969322,
    #     # ]
    #
    #     # prepare_json(questionnaire_code_list_example)
    #
    #     prepare_json()

    def test_explanation_fields(self):
        questionnaire_lime_survey = Questionnaires()
        questionnaire_id = 113491
        language = "pt-BR"

        fields = "remember to include only fields that exists"
        # create_questionnaire_explanation_fields_file(questionnaire_id, language, questionnaire_lime_survey, fields)

        questionnaire_lime_survey.release_session_key()


class InputExportTest(TestCase):
    """ Cria um participante para ser utilizado durante os testes """
    user = ''
    data = {}
    util = UtilTests()

    def setUp(self):
        # """
        # Configure authentication and variables to start each test
        #
        # """
        # print('Set up for', self._testMethodName)

        self.user = User.objects.create_user(username=USER_USERNAME, email='test@dummy.com', password=USER_PWD)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

        self.factory = RequestFactory()

        logged = self.client.login(username=USER_USERNAME, password=USER_PWD)
        self.assertEqual(logged, True)

    def test_write_dynamic_json(self):
        input_data = InputExport()

        self.assertEqual(len(input_data.data), 0)

        input_data.build_header()

        self.assertEqual(len(input_data.data), 4)
        # self.assertEqual(input_data.data, )
        input_data.build_dynamic_header("export_per_participant", 1)

        self.assertEqual(len(input_data.data), 5)

        # field_header_list[0] -> field
        # field_header_list[1] -> header
        participant_field_header_list = [
            ("id", "id"),
            ("name", "name")
            ]

        self.assertNotIn("participants", input_data.data)

        input_data.build_diagnosis_participant("participants", "Participants",
                                               participant_field_header_list)

        self.assertIn("participants", input_data.data)

        questionnaire_list = [
            (271192, "title", [("header1", "field1")]),
            (271193, "title", [("header2", "field2")])
        ]

        self.assertNotIn("questionnaires", input_data.data)

        input_data.build_questionnaire(questionnaire_list)

        self.assertIn("questionnaires", input_data.data)

    def test_crate_dynamic_json(self):

        participant_field_header_list = [
            ("id", "id"),
            ("name", "name")
            ]

        questionnaires_list = [
            (271192, "title", [("header1", "field1")]),
            (271193, "title", [("header2", "field2")])
        ]

        diagnosis_field_header_list = ""

        output_filename = path.join(settings.MEDIA_ROOT, "export/test123.json")

        if path.isfile(output_filename):
            remove(output_filename)

        self.assertTrue(not path.isfile(output_filename))

        build_complete_export_structure(0, 1, participant_field_header_list,
                                        diagnosis_field_header_list, questionnaires_list,
                                        output_filename)

        self.assertTrue(path.isfile(output_filename))

        remove(output_filename)