from rest_framework import serializers
from .models import (
    QCProject,
    QCSite,
    ChecklistTemplate,
    ChecklistInstance,
    ChecklistItemResult,
    QCIssue
)


class QCProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCProject
        fields = '__all__'


class QCSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCSite
        fields = '__all__'


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplate
        fields = '__all__'


class ChecklistInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistInstance
        fields = '__all__'


class QCIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCIssue
        fields = '__all__'