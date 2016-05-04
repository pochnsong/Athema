# coding=utf-8
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class PaperModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="题库名称")
    created_time = models.DateField(auto_now_add=True)
    class Meta:
        verbose_name = "题库"
        verbose_name_plural = "题库"
    def __unicode__(self):
        return self.name

class ChoiceModel(models.Model):
    paper=models.ForeignKey(PaperModel, blank=True, null=True, on_delete=models.SET_NULL)
    title = models.TextField("题目")

    type = models.CharField("选择题类型", max_length=2, choices=(("s", "单选"), ("m", "多选")),
                            blank=True, default="s")
    answer_1 = models.CharField("选项A", max_length=100, blank=True, default="")
    answer_2 = models.CharField("选项B", max_length=100, blank=True, default="")
    answer_3 = models.CharField("选项C", max_length=100, blank=True, default="")
    answer_4 = models.CharField("选项D", max_length=100, blank=True, default="")
    result = models.CharField("答案", max_length=10, blank=True, null=True)
    class Meta:
        verbose_name = "选则题"
        verbose_name_plural = "选则题"


    def check_answer(self, answer):
        """对比答案是否正确"""

        if self.type=="s":
            if isinstance(answer, list) and len(answer)==1 and answer[0]== self.result:
                return True
            if isinstance(answer, unicode) or isinstance(answer, str):
                if answer == self.result:
                    return True
        if self.type == "m":
            _res = self.result.split(',')
            for a in answer:
                _res.remove(a)
            if len(_res) == 0:
                return True
        return False

    def __unicode__(self):
        return self.title

class FillBlankModel(models.Model):
    paper = models.ForeignKey(PaperModel, blank=True, null=True, on_delete=models.SET_NULL)
    title = models.TextField("题目", default="")
    correct = models.CharField("答案", max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "填空题"
        verbose_name_plural = "填空题"

    def __unicode__(self):
        return self.title

    def check_answer(self, answer):
        print answer, self.correct, "ssss"
        if answer == self.correct:
            return True
        return False