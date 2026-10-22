"""Explicit OpenAPI contracts for action endpoints and file responses."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from . import serializers as s

def annotate_views(v):
    binary=OpenApiTypes.BINARY
    obj=OpenApiTypes.OBJECT
    class ImportInput(serializers.Serializer):
        files=serializers.ListField(child=serializers.FileField())
        source=serializers.CharField(required=False)
        fruit_code=serializers.CharField(required=False)
    class SplitInput(serializers.Serializer):
        ratios=serializers.ListField(child=serializers.FloatField(),min_length=3,max_length=3)
        seed=serializers.IntegerField(default=42)
    class FreezeInput(serializers.Serializer):
        seed=serializers.IntegerField(default=42)
        variants=serializers.DictField(child=serializers.UUIDField(),required=False)
        reviewed_variants=serializers.BooleanField(default=False)
    class InspectionInput(serializers.Serializer):
        files=serializers.ListField(child=serializers.FileField())
        model=serializers.UUIDField()
        confidence=serializers.FloatField(default=.25)
    class ReviewInput(serializers.Serializer):
        decision=serializers.ChoiceField(choices=['confirmed','corrected'])
        note=serializers.CharField()
        annotations=serializers.JSONField(default=list)
    class ObservationInput(serializers.Serializer):
        sample=serializers.UUIDField()
        participant=serializers.CharField()
        positive=serializers.BooleanField()
        elapsed_ms=serializers.FloatField()
    mappings=[
        (v.DatasetViewSet,'import_files',ImportInput,{201:obj}),
        (v.DatasetViewSet,'split',SplitInput,obj),
        (v.DatasetViewSet,'freeze',FreezeInput,{201:s.VersionSerializer}),
        (v.DatasetViewSet,'duplicates',None,obj),
        (v.ImageViewSet,'annotate',s.AnnotationInput,s.ImageSerializer),
        (v.ImageViewSet,'history',None,OpenApiTypes.ANY),
        (v.ImageViewSet,'file',None,binary),
        (v.VersionViewSet,'download',None,binary),
        (v.VariantViewSet,'file',None,binary),
        (v.JobViewSet,'preprocessing',s.PreprocessingInput,{202:s.JobSerializer}),
        (v.JobViewSet,'retry',None,{202:s.JobSerializer}),
        (v.ModelViewSet,'activate',None,s.ModelSerializer),
        (v.ModelViewSet,'download',None,binary),
        (v.InspectionViewSet,'create',InspectionInput,{202:s.InspectionSerializer(many=True)}),
        (v.InspectionViewSet,'review',ReviewInput,s.InspectionSerializer),
        (v.InspectionViewSet,'reviews',None,OpenApiTypes.ANY),
        (v.InspectionViewSet,'file',None,binary),
        (v.EvaluationViewSet,'samples',None,OpenApiTypes.ANY),
        (v.EvaluationViewSet,'sample_file',None,binary),
        (v.EvaluationViewSet,'observe',ObservationInput,{201:obj}),
        (v.EvaluationViewSet,'run',None,{202:s.JobSerializer}),
        (v.EvaluationViewSet,'summary',None,obj),
        (v.EvaluationViewSet,'export',None,binary),
        (v.DashboardViewSet,'list',None,obj),
        (v.ReportViewSet,'list',None,obj),
        (v.ReportViewSet,'export',None,binary),
    ]
    for cls,name,request,response in mappings:
        method=getattr(cls,name)
        extend_schema(request=request,responses=response)(method)
    extend_schema(parameters=[OpenApiParameter('sample',OpenApiTypes.UUID,required=True)],responses=binary)(v.EvaluationViewSet.sample_file)
    extend_schema(parameters=[OpenApiParameter('name',OpenApiTypes.STR)],responses=OpenApiTypes.ANY)(v.TrainingViewSet.artifacts)
    extend_schema(parameters=[OpenApiParameter('format',OpenApiTypes.STR,enum=['xlsx','pdf']),OpenApiParameter('from',OpenApiTypes.DATE),OpenApiParameter('to',OpenApiTypes.DATE)],responses=binary)(v.ReportViewSet.export)
