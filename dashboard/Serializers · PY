from rest_framework import serializers
from .models import (
    QCProject, QCSite,
    ChecklistTemplate, ChecklistTemplateItem,
    ChecklistInstance, ChecklistItemResult, QCIssue,
)


class QCProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCProject
        fields = ["id", "unique_id", "name", "location", "is_active"]


class QCSiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCSite
        fields = ["id", "unique_id", "project", "name"]


class ChecklistTemplateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplateItem
        fields = ["id", "sequence", "stage", "question", "requires_photo", "requires_note"]


class ChecklistTemplateSerializer(serializers.ModelSerializer):
    items = ChecklistTemplateItemSerializer(many=True, read_only=True)

    class Meta:
        model = ChecklistTemplate
        fields = ["id", "unique_id", "name", "activity_type", "version", "is_active", "items"]


class ChecklistItemResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemResult
        fields = [
            "id", "template_item", "status", "note", "photo1", "photo2",
            "verified_by", "verified_at",
        ]
        read_only_fields = ["verified_by", "verified_at"]


class ChecklistInstanceSerializer(serializers.ModelSerializer):
    """
    Used both for a normal online submit AND for offline-sync replay — the
    JS layer hits this same endpoint either way (see qc_sync.js discussed
    earlier). client_uuid makes a retried sync safe: DB unique constraint
    stops a duplicate ChecklistInstance being created if the same offline
    entry gets POSTed twice.
    """
    item_results = ChecklistItemResultSerializer(many=True, required=False)

    class Meta:
        model = ChecklistInstance
        fields = [
            "id", "unique_id", "client_uuid",
            "template", "template_version", "project", "site",
            "filled_by", "verified_by", "audited_by", "status",
            "filled_at_device_time", "created_at", "verified_at",
            "item_results",
        ]
        read_only_fields = ["filled_by", "verified_by", "audited_by", "created_at"]

    def create(self, validated_data):
        item_results_data = validated_data.pop("item_results", [])
        request = self.context["request"]
        validated_data["filled_by"] = request.user

        # idempotent: if this client_uuid already synced, return the
        # existing instance instead of erroring or duplicating
        client_uuid = validated_data.get("client_uuid")
        if client_uuid:
            existing = ChecklistInstance.objects.filter(client_uuid=client_uuid).first()
            if existing:
                return existing

        instance = ChecklistInstance.objects.create(**validated_data)
        for item_data in item_results_data:
            ChecklistItemResult.objects.create(instance=instance, **item_data)
        return instance


class QCIssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCIssue
        fields = [
            "id", "unique_id", "checklist_item_result", "raised_by", "assigned_to",
            "source", "description", "status", "due_date", "created_at", "closed_at",
        ]
        read_only_fields = ["raised_by", "created_at", "closed_at"]

    def create(self, validated_data):
        validated_data["raised_by"] = self.context["request"].user
        return QCIssue.objects.create(**validated_data)