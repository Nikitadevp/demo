from rest_framework import serializers
from .models import (
    QCProject,
    QCSite,
    ChecklistTemplate,
    ChecklistTemplateItem,
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


class ChecklistTemplateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplateItem
        fields = '__all__'


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    items = ChecklistTemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistTemplate
        fields = '__all__'


class ChecklistItemResultSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='template_item.question', read_only=True)

    class Meta:
        model = ChecklistItemResult
        fields = '__all__'


class ChecklistInstanceSerializer(serializers.ModelSerializer):
    item_results = ChecklistItemResultSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistInstance
        fields = '__all__'


class QCIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCIssue
        fields = '__all__'
        
