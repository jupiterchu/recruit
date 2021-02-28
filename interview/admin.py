import csv
import logging
from datetime import datetime

from django.contrib import admin, messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils.safestring import mark_safe

from interview.candidate_field import default_fieldsets_first, default_fieldsets_second, default_fieldsets
from interview.dingtalk import send as DingTalkSend
from interview.models import Candidate
from jobs.models import Resume

logger = logging.getLogger(__name__)  # 获取模块名称

exportable_fields = (
    'username', 'city', 'phone', 'bachelor_school', 'master_school', 'degree', 'first_result', 'first_interviewer_user',
    'second_result', 'second_interviewer_user', 'hr_result', 'hr_score', 'hr_remark', 'hr_interviewer_user')


def export_model_as_csv(model_admin, request, queryset):
    response = HttpResponse(content_type='text/csv', charset='utf-8-sig')  # 针对 win 处理

    field_list = exportable_fields
    response['Content-Disposition'] = 'attachment; filename=recruitment-candidates-list-%s.csv' % (
        datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
    )

    # response.write(codecs.BOM_UTF8) # 针对 win 处理
    writer = csv.writer(response)
    writer.writerow(
        [queryset.model._meta.get_field(f).verbose_name.title() for f in field_list]
    )

    for obj in queryset:
        csv_line_values = []
        for field in field_list:
            field_object = queryset.model._meta.get_field(field)
            field_value = field_object.value_from_object(obj)
            csv_line_values.append(field_value)
        writer.writerow(csv_line_values)

    logger.error(" %s has exported %s candidate records" % (request.user.username, len(queryset)))
    return response


export_model_as_csv.short_description = u'导出为 CSV 文本'
# 允许的权限，如果用户有 export 权限，这个方法则允许调用, 多个定义多个方法
export_model_as_csv.allowed_permissions = ('export',)


def notify_interviewer(model_admin, request, queryset):
    """通知一面面试官面试候选人"""
    candidates = ""
    interviewers = ""
    for obj in queryset:
        candidates = obj.username + ";" + candidates
        interviewers = obj.first_interviewer_user.username + ';' + interviewers
    DingTalkSend("候选人 %s 进入面试环节，亲爱的面试官，请准备好面试：%s" % (candidates, interviewers))
    messages.add_message(request, messages.INFO, '已成功发送面试通知')

notify_interviewer.short_description = u"通知一面面试官"
notify_interviewer.allowed_permissions = ('notify',)


class CandidateAdmin(admin.ModelAdmin):
    # 详情页不展示字段
    exclude = ('creator', 'create_date', 'modified_date')

    # 列表页展示字段
    list_display = (
        'username', 'city', 'bachelor_school', 'get_resume', 'first_score', 'first_result', 'first_interviewer_user', 'second_score',
        'second_result', 'second_interviewer_user', 'hr_score', 'hr_result', 'hr_interviewer_user', 'last_editor'
    )

    # 列表页排序字段，从高到低
    ordering = ('hr_result', 'second_result', 'first_result',)

    # 筛选条件
    list_filter = (
        'city', 'first_result', 'second_result', 'hr_result', 'first_interviewer_user', 'second_interviewer_user',
        'hr_interviewer_user')

    # 查询字段
    search_fields = ('username', 'phone', 'email', 'bachelor_school')

    # 新增动作函数
    actions = [export_model_as_csv, notify_interviewer]

    def has_export_permission(self, request):
        """检测当前用户是否有导出权限"""
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, 'export'))  # interview.export

    def has_notify_permission(self, request):
        """检测当前用户是否有通知权限"""
        opts = self.opts
        return request.user.has_perm('%s.%s' % (opts.app_label, 'notify'))

    def save_model(self, request, obj, form, change):
        """自动设置并保存字段属性"""
        obj.last_editor = request.user.username
        if not obj.creator:
            obj.creator = request.user.username
        obj.modified_date = datetime.now()
        super().save_model(request, obj, form, change)

    def get_group_names(self, user):
        """获取用户的所有组别"""
        group_names = []
        for g in user.groups.all():
            group_names.append(g.name)
        return group_names

    def get_readonly_fields(self, request, obj=None):
        """对指定用户，设置只读字段，让面试官不可以在详情页修改谁是面试官
        所有用户 readonly_fields = ('first_interviewer_user', 'second_interviewer_user',)
        """
        group_names = self.get_group_names(request.user)

        if 'interviewer' in group_names:
            logger.info("interviews is in user's group for %s" % request.user.username)
            return ('first_interviewer_user', 'second_interviewer_user',)
        return ()

    def get_list_editable(self, request):
        """让 HR 可以直接在列表里面操作谁是面试官, 针对不同的角色展示不同的 list_editable """
        default_list_editable = ('first_interviewer_user', 'second_interviewer_user',)
        group_names = self.get_group_names(request.user)

        if request.user.is_superuser or 'HR' in group_names:
            return default_list_editable
        return ()

    def get_changelist_instance(self, request):
        """调用父类方法，让自定义 get_list_editable 函数有效"""
        self.list_editable = self.get_list_editable(request)
        return super(CandidateAdmin, self).get_changelist_instance(request)

    def get_fieldsets(self, request, obj=None):
        """一二面面试官仅填写自己的反馈, 针对不同的角色展示不同的 fieldsets"""
        group_names = self.get_group_names(request.user)
        if 'interviewer' in group_names and obj.first_interviewer_user == request.user:
            return default_fieldsets_first
        if 'interviewer' in group_names and obj.second_interviewer_user == request.user:
            return default_fieldsets_second
        return default_fieldsets

    def get_queryset(self, request):
        """在列表页展示时使用该方法, 对于面试官, 只展示要模式的候选人集合
        Q 用于 and 和 or 操作
        """
        queryset = super(CandidateAdmin, self).get_queryset(request)

        group_names = self.get_group_names(request.user)
        if request.user.is_superuser or 'HR' in group_names:
            return queryset
        return Candidate.objects.filter(
            Q(first_interviewer_user=request.user) | Q(second_interviewer_user=request.user)
        )

    def get_resume(self, obj):
        if not obj.phone:
            return ""
        resumes = Resume.objects.filter(phone=obj.phone)
        if resumes and len(resumes) > 0:
            return mark_safe(u'<a href="/resume/%s" target="_blank">%s</a>'%(resumes[0].id, "查看简历")) # 返回一个安全的 HTML
        return ""
    get_resume.short_description = '查看简历'
    get_resume.allow_tags = True

admin.site.register(Candidate, CandidateAdmin)
