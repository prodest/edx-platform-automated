#
# metalogix report generation script
#
# TODO: clean up unused fields
#
#
#
# instructions:
#   ---on open edx server
#       cd /edx/app/edxapp/edx-platform
#       source ../edxapp_env
#       python manage.py lms --settings=aws_appsembler shell  
#   
#       inside the django shell, execute this script
#       
#  ---after script has executed
#  scp files from site to personal computer
#  there will be two files: 
#	/tmp/gradeReport<DATE>.csv
#	/tmp/userReport<DATE>.csv
#

from xmodule.modulestore.django import modulestore
from django.contrib.auth.models import User
from instructor.utils import DummyRequest
from instructor.views.legacy import get_student_grade_summary_data
from student.models import CourseEnrollment
from certificates.models import GeneratedCertificate

import csv 
from datetime import datetime

from django.contrib.auth.models import User


################# course report ######################
random_user = User.objects.all()[0]

course_file_name = '/tmp/gradeReport%s.csv' % (datetime.now().strftime('%Y%m%d')) 
fp = open(course_file_name,'w')
writer = csv.writer(fp, quotechar='"', quoting=csv.QUOTE_ALL)
request = DummyRequest()
request.user = random_user

mongo_courses = modulestore().get_courses()
writer.writerow(['#course_id', 'course_name','user_id','username','email','final_score','date_registered','date_passed','certificate_eligible'])
for course in mongo_courses:
#location, city, country; registered, is_active, last_login
#course_id = 'course-v1:Metalogix+EO301+2015'
#course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
#course = get_course_by_id(course_key)
    course_name = course.display_name
    get_raw_scores = False
    datatable = get_student_grade_summary_data(request, course, get_raw_scores=get_raw_scores)
    for d in datatable['data']:
        user_id = d[0]
        u = User.objects.get(id=user_id)
        cag = u.courseaccessgroup_set.all()
        if not cag:
            cag = ''
        else:
            cag = cag[0]
        try: 
            loc = u.profile.location
        except Exception:
            loc = ''
        try: 
            p = u.profile   
            city = str(p.city)
            country = str(p.country)
            full_name = str(p.name)
        except Exception: #profile doesn't exist or city isn't ascii
            city = ''
            country = ''
            full_name = ''
        certificate = GeneratedCertificate.objects.filter(user=u).filter(course_id=course.id)
        if certificate:
            cert = certificate[0]
            completion_date = cert.created_date
        else:
            completion_date = ''
        ce = CourseEnrollment.objects.filter(user_id=u.id).filter(course_id=course.id)[0]
        # try:
        #     course_access_group = user.courseaccessgroup_set.all()[0].name #assume there's at least one group and get it
        #     p = user.profile
        # except:
        #     course_access_group = 'None'
        output_data = [course.id,
                       course_name,
                        str(u.id), 
                        u.username, 
                        u.email,
                        d[len(d)-1],
                        str(ce.created),
                        str(completion_date),
                        '?'
                    ]
        encoded_row = [unicode(s).encode('utf-8') for s in output_data]
        #writer.writerow(output_data)
        writer.writerow(encoded_row)

fp.close()
################# end course report ######################


################# user report ######################
user_file_name = '/tmp/userReport%s.csv' % datetime.now().strftime('%Y%m%d')
fp = open(user_file_name,'w')
writer = csv.writer(fp, quotechar='"', quoting=csv.QUOTE_ALL)

writer.writerow(['#user_id','username','full_name','email_address','email_domain','is_active','last_login','date_joined','city','country','course_access_group'])

users = User.objects.all()
for u in users:
    cag = u.courseaccessgroup_set.all()
    try:
        email_domain = u.email.split('@')[1]
    except Exception:
        email_domain = ''
    if not cag:
        cag = ''
    else:
        cag = cag[0]
    try:
        loc = u.profile.location
    except Exception:
        loc = ''
    if not u.last_login:
        last_login = u.date_joined
    else: 
        last_login = u.last_login
    try:
        p = u.profile
        city = str(p.city)
        country = str(p.country)
        full_name = str(p.name)
    except Exception: #profile doesn't exist or city isn't ascii
        city = ''
        country = ''
        full_name = ''
    output_data = [u.id,
                   u.username,
				   full_name,
                   u.email,
                   email_domain,
                   u.is_active,
                   last_login,
                   u.date_joined,
                   city,
                   country,
                   cag,
                ]
    encoded_row = [unicode(s).encode('utf-8') for s in output_data]
    #print encoded_row
    #writer.writerow(output_data)
    writer.writerow(encoded_row)

fp.close()

################# end user report ######################
