from django.contrib import admin, messages

from interview.models import Candidate
from .models import Job, Resume


class JobAdmin(admin.ModelAdmin):
    exclude = ["create_date", "modified_date", "creator"]
    list_display = ("job_name", "job_type", "job_city", "creator", "create_date", "modified_date")

    def save_model(self, request, obj, form, change):
        obj.creator = request.user
        super().save_model(request, obj, form, change)


def enter_interview_process(model_admin, request, queryset):
    candidate_names = ""
    for resume in queryset:
        candidate = Candidate()
        # 将 resume 中所有属性拷贝到 candidate 对象中去，由于复制了 ID 所以会覆盖已有ID到的角色
        candidate.__dict__.update(resume.__dict__)
        candidate_names = candidate.username + "," + candidate_names
        candidate.creator = request.user.username
        candidate.save()
    messages.add_message(request, messages.INFO, '候选人：%s 已经进入面试流程' % candidate_names)


enter_interview_process.short_description = u"进入面试流程"


class ResumeAdmin(admin.ModelAdmin):
    actions = (enter_interview_process,)

    # def image_tag(self, obj):
    #     if obj.picture:
    #         return format_html('<img src="{}" style="width:100px;height:80px;"/>'.format(obj.picture.url))
    #     return ""

    # image_tag.allow_tags = True
    # image_tag.short_description = 'Image'

    list_display = (
        'username', 'applicant', 'city', 'apply_position', 'bachelor_school', 'master_school', 'major',
        'created_date')

    readonly_fields = ('applicant', 'created_date', 'modified_date',)

    fieldsets = (
        (None, {'fields': (
            "applicant", ("username", "city", "phone"),
            ("email", "apply_position", "born_address", "gender",), ("picture", "attachment",),
            ("bachelor_school", "master_school"), ("major", "degree"), ('created_date', 'modified_date'),
            "candidate_introduction", "work_experience", "project_experience",)}),
    )

    def save_model(self, request, obj, form, change):
        obj.applicant = request.user  # 申请人保存成当前用户
        super(ResumeAdmin, self).save_model(request, obj, form, change)


admin.site.register(Job, JobAdmin)
admin.site.register(Resume, ResumeAdmin)
