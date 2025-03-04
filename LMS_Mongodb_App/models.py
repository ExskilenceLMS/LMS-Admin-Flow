from djongo import models
# from LMS_MSSQLdb_App.models import Students, Subjects, Courses,Questions
# Create your models here.

# 1
class students_assessments(models.Model):
    student_id          = models.CharField(max_length=20)
    assessment_type = models.CharField(max_length=20)
    subject_id          = models.CharField(max_length=20)
    test_id             = models.CharField(max_length=20)
    course_id           = models.CharField(max_length=20)
    assessment_score_secured = models.FloatField()
    assessment_max_score = models.FloatField()
    assessment_week_number = models.IntegerField()
    assessment_completion_time = models.DateTimeField()
    assessment_rank     = models.IntegerField()
    assessment_overall_rank = models.IntegerField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'students_assessments'
# 2
class practice_questions(models.Model):
    student_id          = models.CharField(max_length=20)
    subject_id          = models.CharField(max_length=20)
    question_type       = models.CharField(max_length=20)
    practice_score_secured = models.FloatField()
    practice_max_score  = models.FloatField()
    practice_week_number = models.IntegerField()
    practice_completion_time = models.DateTimeField()
    question_id         = models. CharField(max_length=20)
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'practice_questions'
# 3
class live_sessions(models.Model):

    # student_id = models.ForeignKey(Students,  on_delete=models.SET_NULL, null=True)
    session_id          = models.CharField(max_length=20)
    session_title       = models.TextField()
    session_starttime   = models.DateTimeField()
    session_author      = models.TextField()
    session_subject     = models.TextField()
    session_meetlink    = models.TextField()
    session_endtime     = models.DateTimeField()
    session_video_link  = models.TextField()
    session_status      = models.TextField()
    student_ids         = models.JSONField(default=list)
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'live_sessions'
# 4
class student_practiceMCQ_answers(models.Model):
    student_id          = models.CharField(max_length=20)
    question_id         = models.CharField(max_length=20)
    correct_ans         = models.CharField(max_length=20)
    entered_ans         = models.CharField(max_length=20)
    subject_id          = models.CharField(max_length=20)
    answered_time       = models.DateTimeField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_practiceMCQ_answers'
# 5
class student_practice_coding_ans(models.Model):
    student_id          = models.CharField(max_length=20)
    question_id         = models.CharField(max_length=20)
    entered_ans         = models.TextField()
    subject_id          = models.CharField(max_length=20)
    answered_time       = models.DateTimeField()
    testcase_results    = models.JSONField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_practice_coding_ans'
# 6
class student_online_session(models.Model):
    session_id          = models.CharField(max_length=20)
    student_id          = models.CharField(max_length=20)
    attended_duration   = models.FloatField()
    display_name        = models.CharField(max_length=20)
    delete = models.BooleanField(default=False)

    def __str__(self):
        return self.session_id
    class Meta:
        db_table = 'student_online_session'
# 7
class student_attendance_session_details(models.Model):
    session_id          = models.CharField(max_length=20)    
    student_id          = models.CharField(max_length=20)
    session_in          = models.DateTimeField()
    session_out         = models.DateTimeField()
    attended_time       = models.FloatField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'student_attendance_session_details'
# 8
class group_announcement(models.Model):
    group_id = models.CharField(max_length=20, primary_key=True)
    group_name = models.TextField()
    student_ids = models.JSONField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'group_announcement'
# 9
class notification(models.Model):
    notification_id = models.CharField(max_length=20)
    notification_title = models.TextField()
    notification_message = models.TextField()
    notification_timestamp = models.DateTimeField()
    status = models.CharField(max_length=1)
    student_id = models.CharField(max_length=20)
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'notification'
# 10
class announcements(models.Model):
    announcement_id = models.CharField(max_length=20)
    announcement_title = models.TextField()
    announcement_message = models.TextField()
    announcement_timestamp = models.DateTimeField()
    origin = models.CharField(max_length=20)
    attachments = models.JSONField()
    group_id = models.CharField(max_length=20)
    announcement_type = models.CharField(max_length=20)
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'announcements'
# 11
class students(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    student_group_ids = models.JSONField()
    student_notification = models.JSONField()
    student_announcements = models.JSONField()
    student_education_details =models.JSONField()
    delete = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'students'
# 12
class participant(models.Model):
    session_id = models.CharField(max_length=20)
    student_id = models.CharField(max_length=20)
    display_name = models.CharField(max_length=20)
    attended_time = models.FloatField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'participant'
# 13
class logs(models.Model):
    session_id = models.CharField(max_length=20)
    student_id = models.CharField(max_length=20)
    session_start_time = models.DateTimeField()
    session_end_time = models.DateTimeField()
    delete = models.BooleanField(default=False)

    class Meta:
        db_table = 'logs'