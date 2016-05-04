from django.shortcuts import render
from django.views.generic import ListView, TemplateView
from .models import *
# Create your views here.

class IndexView(ListView):
    template_name = "website/index/index.html"
    model = PaperModel


class TestingView(TemplateView):
    template_name = "website/testing/index.html"
    def get_context_data(self, pk, **kwargs):
        context = {}
        context['choice_s'] = ChoiceModel.objects.filter(paper=pk, type="s")
        context['choice_m'] = ChoiceModel.objects.filter(paper=pk, type="m")
        context['fillblank'] = FillBlankModel.objects.filter(paper=pk)
        return context

    def post(self, request, pk, **kwargs):
        POST = request.POST
        context={
            'choice_s':[],
            'choice_m': [],
            'fillblank': [],
            'error': 0,
            'total': 0,
            'correct': 0,
        }
        for x in ChoiceModel.objects.filter(paper=pk, type="s"):
            _check = x.check_answer(POST.getlist('test-choice-%s'%x.pk))
            context['total'] += 1
            if _check:
                context['correct'] +=1
            else:
                context['error'] += 1
            context['choice_s'].append({
                'item': x,
                'correct': _check,
                'yours_answer': ','.join(POST.getlist('test-choice-%s'%x.pk))
            })

        for x in ChoiceModel.objects.filter(paper=pk, type="m"):
            _check = x.check_answer(POST.getlist('test-choice-%s' % x.pk))
            context['total'] += 1
            if _check:
                context['correct'] += 1
            else:
                context['error'] += 1

        context['choice_m'].append({
                'item': x,
                'correct': _check,
                'yours_answer': ','.join(POST.getlist('test-choice-%s' % x.pk))
            })
        for x in FillBlankModel.objects.filter(paper=pk):
            _check = x.check_answer(POST.get('test-fill-%s'%x.pk,  None))
            context['total'] += 1
            if _check:
                context['correct'] += 1
            else:
                context['error'] += 1

            context['fillblank'].append({
                'item': x,
                'correct': _check,
                'yours_answer': POST.get('test-fill-%s' % x.pk, ""),
            })
        return render(request, "website/testing/result.html", context)