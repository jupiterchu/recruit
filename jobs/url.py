from django.urls import path

from jobs import views

urlpatterns = [
    path(r"joblist/", views.joblist, name='joblist'),
    path(r"job/<int:id>/", views.job, name="job_detail"),
    path("resume/add/", views.ResumeCreateView.as_view(), name="resume_add"),

    path('resume/<int:pk>', views.ResumeDetailView.as_view(), name="resume_detail"),
    path(r'', views.joblist, name='name'),    # 首页自动跳转到职位列表
]
