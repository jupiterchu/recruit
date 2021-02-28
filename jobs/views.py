from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.views.generic import CreateView, DetailView

from jobs.models import Job, Cities, JobsType, Resume


def joblist(request):
    job_list = Job.objects.order_by('job_type')
    template = loader.get_template('joblist.html')
    context = {'job_list': job_list}

    for job in job_list:
        job.city_name = Cities[job.job_city][1]
        job.job_type = JobsType[job.job_type][1]

    return HttpResponse(template.render(context))


def job(request, id):
    try:
        job = Job.objects.get(pk=id)
        job.city_name = Cities[job.job_city][1]
    except Job.DoesNotExist:
        raise Http404()

    return render(request, 'job.html', locals())


class ResumeCreateView(LoginRequiredMixin, CreateView):
    """简历创建页面视图
    CreateView Django 中通用可编辑的视图
    """
    template_name = 'resume_form.html'  # 定义
    success_url = '/joblist/'  # 创建成功后跳转的页面
    model = Resume
    fields = ["username", "city", "phone",
              'email', 'apply_position', "gender",
              "bachelor_school", "master_school", "major", "degree",
              "candidate_introduction", "work_experience", "project_experience"]

    def get_initial(self):
        """
        可以从 URL 请求中参数，给到 form 表单默认值
        :return: dict
        """
        initial = {}
        for i in self.request.GET:
            initial[i] = self.request.GET[i]
        return initial

    def form_valid(self, form):
        """
        验证表单，简历跟当前用户相关
        :param form:
        :return:
        """
        self.object = form.save(commit=False)
        self.object.applicant = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

class ResumeDetailView(DetailView):
    """简历详情页"""
    model = Resume
    template_name = 'resume_detail.html'
