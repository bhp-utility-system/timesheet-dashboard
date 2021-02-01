import re
from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.decorators import method_decorator
from edc_base.view_mixins import EdcBaseViewMixin
from edc_dashboard.view_mixins import ListboardFilterViewMixin, SearchFormViewMixin
from edc_dashboard.views import ListboardView
from edc_navbar import NavbarViewMixin

from bhp_personnel_dashboard.model_wrappers import EmployeeModelWrapper
from .filters import EmployeeListboardViewFilters


class EmployeeListBoardView(
        NavbarViewMixin, EdcBaseViewMixin, ListboardFilterViewMixin,
        SearchFormViewMixin, ListboardView):

    listboard_template = 'timesheet_employee_listboard_template'
    listboard_url = 'timesheet_employee_listboard_url'
    listboard_panel_style = 'info'
    listboard_fa_icon = "fa-user-plus"

    model = 'bhp_personnel.employee'
    model_wrapper_cls = EmployeeModelWrapper
    listboard_view_filters = EmployeeListboardViewFilters()
    navbar_name = 'timesheet'
    navbar_selected_item = 'timesheet_listboard'
    ordering = '-modified'
    paginate_by = 10
    search_form_url = 'timesheet_employee_listboard_url'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        p_role = self.request.GET.get('p_role')
        context.update(
            p_role=p_role,
            departments=self.departments,
            groups=[g.name for g in self.request.user.groups.all()],
            employee_add_url=self.model_cls().get_absolute_url())
        return context

    def get_queryset_filter_options(self, request, *args, **kwargs):
        options = super().get_queryset_filter_options(request, *args, **kwargs)
        usr_groups = [g.name for g in self.request.user.groups.all()]

        if kwargs.get('subject_id'):
            options.update(
                {'identifier': kwargs.get('subject_id')})

        elif('Supervisor' in usr_groups and request.GET.get('p_role') == 'Supervisor'):
            supervisor_cls = django_apps.get_model('bhp_personnel.supervisor')
            try:
                supervisor_obj = supervisor_cls.objects.get(email=self.request.user.email)
            except supervisor_cls.DoesNotExist:
                options.update({'user_created': None})
            else:
                options.update({'supervisor': supervisor_obj})
        return options

    def get_queryset(self):
        qs = super().get_queryset()

        if self.request.GET.get('dept'):
            usr_groups = [g.name for g in self.request.user.groups.all()]

            if 'HR' in usr_groups and self.request.GET.get('p_role') == 'HR':
                qs = qs.filter(department__dept_name=self.request.GET.get('dept'))
        return qs

    def extra_search_options(self, search_term):
        q = Q()
        if re.match('^[A-Z]+$', search_term):
            q = Q(first_name__exact=search_term)
        return q

    @property
    def departments(self):
        department_cls = django_apps.get_model('bhp_personnel.department')

        return [dept.dept_name for dept in department_cls.objects.all()]
